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
from gi.repository import Gtk, Gdk
from gettext import gettext as _
from ..config.constants import SUPPORTED_INPUT_AUDIO_FORMATS


class DragDropHandler:
    def __init__(self, window):
        self.window = window
        self.new_drum_placeholder = None

    def setup_drag_drop(self, target_widget=None):
        if target_widget is None:
            target_widget = self.window

        # Create drop target for file drops on window (for general drag detection)
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_window_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)

        target_widget.add_controller(drop_target)
        return drop_target

    def setup_button_drop_target(self, button, drum_id=None):
        """Setup drop target on individual drum button for replacement"""
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
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
        """Handle drop on window - add new drum(s)"""
        self._clear_drag_feedback()

        files_list = value.get_files()
        files = list(files_list)
        return self.handle_multiple_files_drop(files, None)

    def _on_button_drop(self, _drop_target, value, _x, _y, drum_id):
        """Handle drop on drum button - replace drum or add multiple"""
        files_list = value.get_files()
        files = list(files_list)
        return self.handle_multiple_files_drop(files, drum_id)

    def _validate_file_format(self, path):
        """Validate file format is supported"""
        if path.suffix.lower() not in SUPPORTED_INPUT_AUDIO_FORMATS:
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

    def handle_multiple_files_drop(self, files, drum_id_to_replace):
        """Handle files dropped at once"""
        if not files:
            return False

        valid_files = []
        skipped_count = 0

        # Filter and validate all files first
        for file_obj in files:
            file_path = file_obj.get_path()
            if not file_path:
                skipped_count += 1
                continue

            path = Path(file_path)
            if self._validate_file_format(path) and self._validate_file_access(path):
                valid_files.append(path)
            else:
                skipped_count += 1

        if not valid_files:
            self.window.show_toast(_("No valid audio files found"))
            return False

        return self._handle_files(valid_files, skipped_count, drum_id_to_replace)

    def _handle_files(self, valid_files, skipped_count, drum_id_to_replace):
        """Handle files - replacement and additions"""
        success_count = 0
        replacement_done = False
        successful_additions = []

        # Process all files
        for i, path in enumerate(valid_files):
            try:
                name = self._extract_name_from_path(path)

                if i == 0 and drum_id_to_replace:
                    # Replace first file and show replacement toast
                    if self.window.replace_drum_part(
                        drum_id_to_replace, str(path), name
                    ):
                        replacement_done = True
                        success_count += 1
                else:
                    # Add files
                    # show individual toast for single file, suppress for multiple
                    show_toast = len(valid_files) == 1 and not drum_id_to_replace
                    if self.window.add_new_drum_part(
                        str(path), name, show_success_toast=show_toast
                    ):
                        success_count += 1
                        if not show_toast:  # Track additions for summary
                            successful_additions.append(name)
            except Exception as e:
                skipped_count += 1
                self.window.show_toast(_("Error processing file: {}").format(str(e)))

        # Show summary notifications for multiple files
        if len(valid_files) > 1:
            self._show_files_notifications(
                success_count, skipped_count, replacement_done, successful_additions
            )

        return success_count > 0

    def _show_files_notifications(
        self, success_count, skipped_count, replacement_done, successful_additions
    ):
        """Show notifications for file operations"""
        if replacement_done:
            # If replacement occurred, don't count it in additions
            additions = success_count - 1
        else:
            additions = success_count

        # Show summary for additions only (replacement already showed toast)
        if additions > 0:
            if additions == 1 and successful_additions:
                # Show individual toast for single addition like normal
                self.window.show_added_toast(successful_additions[0])
            elif skipped_count > 0:
                if additions == 1:
                    self.window.show_toast(
                        _("Added {} drum part, {} files skipped").format(
                            additions, skipped_count
                        )
                    )
                else:
                    self.window.show_toast(
                        _("Added {} drum parts, {} files skipped").format(
                            additions, skipped_count
                        )
                    )
            else:
                self.window.show_toast(_("Added {} drum parts").format(additions))
        elif skipped_count > 0 and not replacement_done:
            # Only show skipped message if no replacement happened
            self.window.show_toast(_("{} files skipped").format(skipped_count))

    def _clear_drag_feedback(self):
        """Clear all drag feedback visuals"""
        self.window.remove_css_class("drag-hover")

        # Remove placeholder
        if self.new_drum_placeholder:
            self.window.drum_grid_builder.remove_new_drum_placeholder(
                self.new_drum_placeholder
            )
            self.new_drum_placeholder = None
