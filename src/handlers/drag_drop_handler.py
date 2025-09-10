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


class DragDropHandler:
    def __init__(self, window):
        self.window = window
        self.supported_formats = {".wav", ".mp3", ".ogg", ".flac", ".aiff", ".aif"}

    def setup_drag_drop(self, target_widget=None):
        if target_widget is None:
            target_widget = self.window

        # Create drop target for file drops
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)

        target_widget.add_controller(drop_target)

        return drop_target

    def _on_drag_enter(self, drop_target, x, y):
        self.window.add_css_class("drag-hover")
        return Gdk.DragAction.COPY

    def _on_drag_leave(self, drop_target):
        self.window.remove_css_class("drag-hover")

    def _on_drop(self, drop_target, value, x, y):
        self.window.remove_css_class("drag-hover")

        if not isinstance(value, Gio.File):
            return False

        file_path = value.get_path()
        if not file_path:
            return False

        return self._handle_file_drop(file_path)

    def _handle_file_drop(self, file_path):
        try:
            path = Path(file_path)

            # Check if it's a supported audio format
            if path.suffix.lower() not in self.supported_formats:
                self.window.show_toast(f"Unsupported file format: {path.suffix}")
                return False

            # Check if file exists and is readable
            if not path.exists() or not path.is_file():
                self.window.show_toast("File not found or not accessible")
                return False

            # Extract name from filename
            name = path.stem.replace("_", " ").replace("-", " ").title()

            # Add the sound
            drum_part_manager = self.window.sound_service.get_drum_part_manager()
            new_part = drum_part_manager.add_custom_part(name, str(path))

            if new_part:
                self.window.on_custom_sound_added(new_part, name)
            elif not new_part:
                self.window.show_toast("Failed to add custom sound")

            return True

        except Exception as e:
            self.window.show_toast(f"Error processing file: {str(e)}")
            return False
