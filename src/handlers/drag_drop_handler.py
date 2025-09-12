# handlers/drag_drop_handler.py
#
# Copyright 2025 revisto
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path
from gi.repository import Gtk, Gdk, Gio
from gettext import gettext as _


class DragDropHandler:
    def __init__(self, window):
        self.window = window
        self.supported_formats = {".wav", ".mp3", ".ogg", ".flac"}
        self.new_drum_placeholder = None

    def setup_drag_drop(self, target_widget=None):
        if target_widget is None:
            target_widget = self.window

        # Create drop target for file drops on window (for general drag detection)
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_window_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)

        target_widget.add_controller(drop_target)
        return drop_target

    def setup_button_drop_target(self, button, drum_id=None):
        """Setup drop target on individual drum button for replacement"""
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_button_drop, drum_id)
        drop_target.connect("enter", self._on_button_drag_enter, button)
        drop_target.connect("leave", self._on_button_drag_leave, button)
        button.add_controller(drop_target)

    def _on_drag_enter(self, _drop_target, _x, _y):
        self.window.add_css_class("drag-hover")
        self.new_drum_placeholder = (
            self.window.drum_grid_builder.create_new_drum_placeholder()
        )
        return Gdk.DragAction.COPY

    def _on_button_drag_enter(self, _drop_target, _x, _y, button):
        """Handle drag enter on drum button - highlight for replacement"""
        button.add_css_class("drag-over-replace")
        return Gdk.DragAction.COPY

    def _on_button_drag_leave(self, _drop_target, button):
        """Handle drag leave on drum button - remove highlight"""
        button.remove_css_class("drag-over-replace")

    def _on_drag_leave(self, _drop_target):
        self._clear_drag_feedback()

    def _on_window_drop(self, _drop_target, value, _x, _y):
        """Handle drop on window - add new drum"""
        self._clear_drag_feedback()
        if not isinstance(value, Gio.File):
            return False
        file_path = value.get_path()
        if not file_path:
            return False
        return self._handle_file_drop(file_path, None)  # None = add new

    def _on_button_drop(self, _drop_target, value, _x, _y, drum_id):
        """Handle drop on drum button - replace drum"""
        if not isinstance(value, Gio.File):
            return False
        file_path = value.get_path()
        if not file_path:
            return False
        return self._handle_file_drop(file_path, drum_id)  # drum_id = replace

    def _validate_file_format(self, path):
        """Validate file format is supported"""
        if path.suffix.lower() not in self.supported_formats:
            self.window.show_toast(_("Not a supported audio file"))
            return False
        return True

    def _validate_file_access(self, path):
        """Validate file exists, is accessible, and reasonable size"""
        if not path.exists():
            self.window.show_toast(_("File not found"))
            return False

        if not path.is_file():
            self.window.show_toast(_("Selected item is not a file"))
            return False

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            self.window.show_toast(
                _("File too large: {:.1f}MB (max 50MB)").format(file_size_mb)
            )
            return False

        return True

    def _extract_name_from_path(self, path):
        """Extract display name from file path"""
        name = path.stem.replace("_", " ").replace("-", " ").title()
        return name if name.strip() else _("Custom Sound")

    def _handle_file_drop(self, file_path, drum_id):
        """Handle file drop - validate file and delegate to window methods"""
        try:
            path = Path(file_path)

            if not self._validate_file_format(path):
                return False

            if not self._validate_file_access(path):
                return False

            name = self._extract_name_from_path(path)

            if drum_id:
                return self.window.replace_drum_part(drum_id, str(path), name)
            else:
                return self.window.add_new_drum_part(str(path), name)

        except PermissionError:
            self.window.show_toast(_("Permission denied accessing file"))
            return False
        except OSError as e:
            self.window.show_toast(_("File system error: {}").format(str(e)))
            return False
        except Exception as e:
            self.window.show_toast(_("Error processing file: {}").format(str(e)))
            return False

    def _clear_drag_feedback(self):
        """Clear all drag feedback visuals"""
        self.window.remove_css_class("drag-hover")

        # Remove placeholder
        if self.new_drum_placeholder:
            self.window.drum_grid_builder.remove_new_drum_placeholder(
                self.new_drum_placeholder
            )
            self.new_drum_placeholder = None
