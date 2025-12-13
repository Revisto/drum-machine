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
from typing import Optional, List, Tuple
import logging
from gi.repository import Gtk, Gdk, Gio, GObject
from gettext import gettext as _
from ..config.constants import SUPPORTED_INPUT_AUDIO_FORMATS
from ..utils.name_utils import extract_name_from_path


class DragDropHandler:
    def __init__(self, window) -> None:
        self.window = window
        self.new_drum_placeholder: Optional[Gtk.Widget] = None
        self._dragged_drum_id: Optional[str] = None

    def setup_drag_drop(
        self, target_widget: Optional[Gtk.Widget] = None
    ) -> Gtk.DropTarget:
        if target_widget is None:
            target_widget = self.window

        # Create drop target for file drops on window (for general drag detection)
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_window_drop)
        drop_target.connect("enter", self._on_drag_enter)
        drop_target.connect("leave", self._on_drag_leave)

        target_widget.add_controller(drop_target)
        return drop_target

    def setup_button_drop_target(
        self, button: Gtk.Button, drum_id: Optional[str] = None
    ) -> None:
        """Setup drop target on individual drum button for replacement"""
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_button_drop, drum_id)
        drop_target.connect("enter", self._on_button_drag_enter, button)
        drop_target.connect("leave", self._on_button_drag_leave, button)
        button.add_controller(drop_target)

    def setup_button_reorder_drag_source(
        self, button: Gtk.Button, drum_id: str
    ) -> None:
        """Setup drag source on drum button for reordering.

        Args:
            button: The drum part button that can be dragged
            drum_id: The ID of the drum part associated with this button
        """
        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self._on_reorder_drag_prepare, drum_id)
        drag_source.connect("drag-begin", self._on_reorder_drag_begin, drum_id, button)
        drag_source.connect("drag-end", self._on_reorder_drag_end, button)
        button.add_controller(drag_source)

    def setup_column_reorder_drop_target(self, column_widget: Gtk.Box) -> None:
        """Setup drop target on the entire drum parts column for reordering"""
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self._on_column_reorder_drop)
        drop_target.connect("motion", self._on_column_reorder_motion)
        drop_target.connect("leave", self._on_column_reorder_leave)
        column_widget.add_controller(drop_target)

    def _on_reorder_drag_prepare(
        self,
        drag_source: Gtk.DragSource,
        x: float,
        y: float,
        drum_id: str,
    ) -> Gdk.ContentProvider:
        """Prepare data for drag"""
        self._dragged_drum_id = drum_id
        content = Gdk.ContentProvider.new_for_value(drum_id)
        return content

    def _on_reorder_drag_begin(
        self,
        drag_source: Gtk.DragSource,
        drag: Gdk.Drag,
        drum_id: str,
        button: Gtk.Button,
    ) -> None:
        """Handle drag begin for reordering"""
        button.add_css_class("drag-source-active")
        icon = Gtk.DragIcon.get_for_drag(drag)
        label = Gtk.Label(label=button.get_label())
        icon.set_child(label)

    def _on_reorder_drag_end(
        self,
        drag_source: Gtk.DragSource,
        drag: Gdk.Drag,
        delete_data: bool,
        button: Gtk.Button,
    ) -> None:
        """Handle drag end"""
        button.remove_css_class("drag-source-active")
        self._dragged_drum_id = None
        self._clear_all_insertion_indicators()

    def _get_widget_index(self, column: Gtk.Box, widget: Gtk.Widget) -> int:
        """Get the index of a widget within its parent column"""
        child = column.get_first_child()
        index = 0
        while child:
            if child == widget:
                return index
            index += 1
            child = child.get_next_sibling()
        return -1

    def _get_insertion_index_and_widget(
        self, column: Gtk.Box, y: float
    ) -> Tuple[int, Optional[Gtk.Widget]]:
        """Calculate insertion index based on y position in column.
        Returns (index, widget_to_show_line_on) or (index, None) for end."""
        if not column:
            return 0, None

        child = column.get_first_child()
        index = 0

        while child:
            child_y = child.get_allocation().y
            child_height = child.get_height()
            child_center = child_y + child_height / 2

            if y < child_center:
                return index, child

            index += 1
            child = child.get_next_sibling()

        last_child = column.get_last_child()
        return index, last_child

    def _on_column_reorder_motion(
        self, drop_target: Gtk.DropTarget, x: float, y: float
    ) -> Gdk.DragAction:
        """Handle drag motion over column - show insertion line"""
        if not self._dragged_drum_id:
            return Gdk.DragAction.MOVE

        self._clear_all_insertion_indicators()

        drum_parts_column = self.window.drum_grid_builder.drum_parts_column
        insert_index, widget = self._get_insertion_index_and_widget(
            drum_parts_column, y
        )

        if widget:
            widget_index = self._get_widget_index(drum_parts_column, widget)
            if insert_index > widget_index:
                widget.add_css_class("insert-below")
            else:
                widget.add_css_class("insert-above")

        return Gdk.DragAction.MOVE

    def _on_column_reorder_leave(self, drop_target: Gtk.DropTarget) -> None:
        """Handle drag leave from column"""
        self._clear_all_insertion_indicators()

    def _clear_all_insertion_indicators(self) -> None:
        """Clear all insertion indicators from drum parts column"""
        drum_parts_column = self.window.drum_grid_builder.drum_parts_column
        if not drum_parts_column:
            return

        child = drum_parts_column.get_first_child()
        while child:
            child.remove_css_class("insert-above")
            child.remove_css_class("insert-below")
            child = child.get_next_sibling()

    def _on_column_reorder_drop(
        self, drop_target: Gtk.DropTarget, value: str, x: float, y: float
    ) -> bool:
        """Handle drop for reordering drum parts"""
        source_drum_id = value
        self._clear_all_insertion_indicators()

        if not source_drum_id:
            return False

        drum_part_manager = self.window.sound_service.drum_part_manager
        source_index = drum_part_manager.get_part_index(source_drum_id)

        if source_index == -1:
            return False

        drum_parts_column = self.window.drum_grid_builder.drum_parts_column
        target_index, _ = self._get_insertion_index_and_widget(drum_parts_column, y)

        if source_index < target_index:
            target_index -= 1

        if source_index == target_index:
            return False

        if drum_part_manager.reorder_part(source_drum_id, target_index):
            self.window.drum_grid_builder.rebuild_drum_parts_column()
            self.window.drum_grid_builder.rebuild_carousel()
            return True

        return False

    def _on_drag_enter(
        self, drop_target: Gtk.DropTarget, x: float, y: float
    ) -> Gdk.DragAction:
        self.window.add_css_class("drag-hover")
        self.new_drum_placeholder = (
            self.window.drum_grid_builder.create_new_drum_placeholder()
        )
        return Gdk.DragAction.COPY

    def _on_button_drag_enter(
        self, drop_target: Gtk.DropTarget, x: float, y: float, button: Gtk.Button
    ) -> Gdk.DragAction:
        """Handle drag enter on drum button - highlight for replacement"""
        button.add_css_class("drag-over-replace")
        return Gdk.DragAction.COPY

    def _on_button_drag_leave(
        self, drop_target: Gtk.DropTarget, button: Gtk.Button
    ) -> None:
        """Handle drag leave on drum button - remove highlight"""
        button.remove_css_class("drag-over-replace")

    def _on_drag_leave(self, drop_target: Gtk.DropTarget) -> None:
        self._clear_drag_feedback()

    def _on_window_drop(
        self, drop_target: Gtk.DropTarget, value: Gdk.FileList, x: float, y: float
    ) -> bool:
        """Handle drop on window - add new drum(s)"""
        self._clear_drag_feedback()

        files_list = value.get_files()
        files = list(files_list)
        return self.handle_multiple_files_drop(files, None)

    def _on_button_drop(
        self,
        drop_target: Gtk.DropTarget,
        value: Gdk.FileList,
        x: float,
        y: float,
        drum_id: Optional[str],
    ) -> bool:
        """Handle drop on drum button - replace drum or add multiple"""
        files_list = value.get_files()
        files = list(files_list)
        return self.handle_multiple_files_drop(files, drum_id)

    def handle_replacement_file_selected(self, file_path: str, drum_id: str) -> bool:
        """Handle replacement file selected from file chooser

        Args:
            file_path: Path to the selected file
            drum_id: ID of the drum part to replace
        """
        if not file_path:
            return False

        path = Path(file_path)

        # Validate file
        if not self._validate_file_format(path):
            return False
        if not self._validate_file_access(path):
            return False

        # Extract name and replace
        name = extract_name_from_path(path)
        result = self.window.replace_drum_part(drum_id, str(path), name)

        if result:
            self.window.show_toast(_("Sound replaced"))
            self.window.save_changes_service.mark_unsaved_changes(True)
        else:
            self.window.show_toast(_("Failed to replace sound"))

        return result

    def _validate_file_format(self, path: Path) -> bool:
        """Validate file format is supported"""
        if path.suffix.lower() not in SUPPORTED_INPUT_AUDIO_FORMATS:
            logging.warning(
                f"Unsupported file format attempted: {path.suffix} for {path.name}"
            )
            self.window.show_toast(_("Not a supported audio file"))
            return False
        return True

    def _validate_file_access(self, path: Path) -> bool:
        """Validate file exists, is accessible, and reasonable size"""
        if not path.exists():
            logging.error(f"Dropped file not found: {path}")
            self.window.show_toast(_("File not found"))
            return False

        if not path.is_file():
            logging.warning(f"Dropped item is not a file: {path}")
            self.window.show_toast(_("Selected item is not a file"))
            return False

        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            logging.warning(f"File too large: {file_size_mb:.1f}MB - {path.name}")
            self.window.show_toast(
                _("File too large: {:.1f}MB (max 50MB)").format(file_size_mb)
            )
            return False

        return True

    def handle_multiple_files_drop(
        self, files: List[Gio.File], drum_id_to_replace: Optional[str]
    ) -> bool:
        """Handle files dropped at once"""
        if not files:
            return False

        valid_files: List[Path] = []
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

    def _handle_files(
        self,
        valid_files: List[Path],
        skipped_count: int,
        drum_id_to_replace: Optional[str],
    ) -> bool:
        """Handle files - replacement and additions"""
        success_count = 0
        replacement_done = False
        successful_additions: List[str] = []

        # Process all files
        for i, path in enumerate(valid_files):
            try:
                name = extract_name_from_path(path)

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

        if len(valid_files) > 1:
            self._show_files_notifications(
                success_count, skipped_count, replacement_done, successful_additions
            )

        return success_count > 0

    def _show_files_notifications(
        self,
        success_count: int,
        skipped_count: int,
        replacement_done: bool,
        successful_additions: List[str],
    ) -> None:
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

    def _clear_drag_feedback(self) -> None:
        """Clear all drag feedback visuals"""
        self.window.remove_css_class("drag-hover")

        # Remove placeholder
        if self.new_drum_placeholder:
            self.window.drum_grid_builder.remove_new_drum_placeholder(
                self.new_drum_placeholder
            )
            self.new_drum_placeholder = None
