# ui/drum_grid_builder.py
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

import gi
import logging

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib
from gettext import gettext as _
from ..config.constants import GROUP_TOGGLE_COUNT
from ..dialogs.midi_mapping_dialog import MidiMappingDialog


class DrumGridBuilder:
    """Responsible for building the drum grid UI components"""

    def __init__(self, window):
        self.window = window
        self.main_container = None
        self.drum_parts_column = None

    @property
    def beats_per_page(self):
        """Get the current number of beats per page from the grid builder."""
        return self.window.drum_machine_service.beats_per_page

    def build_drum_machine_interface(self):
        """Build the static drum machine interface and placeholders."""
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_container.set_name("main_container")

        horizontal_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        horizontal_layout.set_homogeneous(False)

        drum_parts_column = self._create_drum_parts_column()
        self.drum_parts_column = drum_parts_column
        horizontal_layout.append(drum_parts_column)

        # Create a container to hold the rebuildable carousel
        self.carousel_container = Gtk.Box()
        self.carousel_container.set_hexpand(True)
        horizontal_layout.append(self.carousel_container)

        self.main_container.append(horizontal_layout)

        # Create a container for the dots indicator
        self.dots_container = Gtk.Box()
        self.dots_container.set_halign(Gtk.Align.CENTER)
        self.main_container.append(self.dots_container)

        # Build the carousel for the first time
        self.rebuild_carousel()

        return self.main_container

    def rebuild_carousel(self, focus_beat_index=0):
        """Builds or rebuilds only the carousel and its indicator dots."""
        carousel = self._create_carousel_drum_rows()
        dots = self._create_dots_indicator(carousel)

        if self.carousel_container.get_first_child():
            self.carousel_container.remove(self.carousel_container.get_first_child())
        if self.dots_container.get_first_child():
            self.dots_container.remove(self.dots_container.get_first_child())

        self.carousel_container.append(carousel)
        self.dots_container.append(dots)

        self.window.drum_machine_service.update_total_beats()
        new_target_page = focus_beat_index // self.beats_per_page
        self.reset_carousel_pages(new_target_page)
        self.window.ui_helper.load_pattern_into_ui(
            self.window.drum_machine_service.drum_parts_state
        )
        GLib.timeout_add(50, self._scroll_carousel_to_page_safely, new_target_page)

    def _scroll_carousel_to_page_safely(self, page_index):
        """Scrolls the carousel to a specific page, ensuring it exists."""
        if hasattr(self.window, "carousel"):
            n_pages = self.window.carousel.get_n_pages()
            target_page = max(0, min(page_index, n_pages - 1))
            if n_pages > 0:
                self.window.carousel.scroll_to(
                    self.window.carousel.get_nth_page(target_page), True
                )
        return GLib.SOURCE_REMOVE

    def _create_dots_indicator(self, carousel):
        """Create dots indicator for the carousel"""
        dots = Adw.CarouselIndicatorDots()
        dots.set_carousel(carousel)
        dots.set_margin_top(10)
        return dots

    def _create_drum_parts_column(self):
        """Create the drum parts buttons column"""
        drum_parts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Get drum parts from the sound service
        drum_part_manager = self.window.sound_service.drum_part_manager
        for drum_part in drum_part_manager.get_all_parts():
            instrument_button = self.create_instrument_button(drum_part)
            drum_parts.append(instrument_button)
        return drum_parts

    def _create_carousel_drum_rows(self):
        """Create carousel with drum rows"""
        carousel = Adw.Carousel()
        carousel.set_spacing(30)
        self.window.carousel = carousel
        carousel.connect("page-changed", self._on_page_changed)

        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_carousel_key_pressed)
        carousel.add_controller(key_controller)

        for i in range(2):
            page = self._create_beat_grid_page(i)
            carousel.append(page)

        return carousel

    def _on_page_changed(self, carousel, index):
        self.reset_carousel_pages()

    def reset_carousel_pages(self, current_page_index=-1):
        """Resets the carousel pages to match the number of active pages in the current
        pattern."""
        carousel = self.window.carousel

        active_pages_in_pattern = self.window.drum_machine_service.active_pages
        pages_for_pattern = active_pages_in_pattern + 1

        if current_page_index == -1:
            current_page_index = carousel.get_position()
        pages_for_view = current_page_index + 2

        desired_pages = max(2, pages_for_pattern, pages_for_view)

        n_pages = carousel.get_n_pages()

        while n_pages < desired_pages:
            new_page = self._create_beat_grid_page(n_pages)
            carousel.append(new_page)
            n_pages = carousel.get_n_pages()

        while n_pages > desired_pages:
            page_to_remove = carousel.get_nth_page(n_pages - 1)
            carousel.remove(page_to_remove)
            n_pages = carousel.get_n_pages()

    def _on_carousel_key_pressed(self, controller, keyval, keycode, state):
        """Handles key presses on the carousel to prevent page navigation with arrow
        keys."""
        if keyval == Gdk.KEY_Left or keyval == Gdk.KEY_Right:
            return True
        return False

    def _on_instrument_button_key_pressed(
        self, controller, keyval, keycode, state, drum_part
    ):
        """Handles right arrow key navigation from an instrument button to the grid."""
        if keyval == Gdk.KEY_Right:
            current_page_index = self.window.carousel.get_position()
            target_beat_index = int(current_page_index * self.beats_per_page)
            try:
                target_toggle = getattr(
                    self.window, f"{drum_part}_toggle_{target_beat_index}"
                )
                target_toggle.grab_focus()
                return True
            except AttributeError as e:
                logging.debug(
                    f"Toggle not found during navigation: "
                    f"{drum_part}_toggle_{target_beat_index}: {e}"
                )
                return True
        return False

    def _on_toggle_key_pressed(
        self, controller, keyval, keycode, state, drum_part, global_beat_index
    ):
        """Handles arrow key navigation between toggle buttons."""
        if keyval == Gdk.KEY_Right:
            return self._handle_right_arrow(drum_part, global_beat_index)
        elif keyval == Gdk.KEY_Left:
            return self._handle_left_arrow(drum_part, global_beat_index)
        return False

    def _handle_right_arrow(self, drum_part, global_beat_index):
        """Handle right arrow key navigation."""
        # Check if we're at the rightmost position of the current page
        if (global_beat_index + 1) % self.beats_per_page == 0:
            return self._scroll_to_next_page(drum_part, global_beat_index)
        target_beat_index = global_beat_index + 1
        return self._navigate_to_target(drum_part, global_beat_index, target_beat_index)

    def _scroll_to_next_page(self, drum_part, global_beat_index):
        """Scroll to next page and focus the leftmost toggle."""
        carousel = self.window.carousel
        current_page = global_beat_index // self.beats_per_page
        n_pages = carousel.get_n_pages()

        if current_page < n_pages - 1:
            carousel.scroll_to(carousel.get_nth_page(current_page + 1), True)
            # Focus the leftmost toggle on the next page
            target_beat_index = (current_page + 1) * self.beats_per_page
            return self._focus_target_toggle(drum_part, target_beat_index)

        # If we're on the last page, stay where we are
        return True

    def _handle_left_arrow(self, drum_part, global_beat_index):
        """Handle left arrow key navigation."""
        if global_beat_index % self.beats_per_page == 0:
            # At the leftmost position, scroll to previous page instead of jumping to
            # instrument
            return self._scroll_to_previous_page(drum_part, global_beat_index)
        target_beat_index = global_beat_index - 1
        return self._navigate_to_target(drum_part, global_beat_index, target_beat_index)

    def _scroll_to_previous_page(self, drum_part, global_beat_index):
        """Scroll to previous page and focus the rightmost toggle."""
        carousel = self.window.carousel
        current_page = global_beat_index // self.beats_per_page

        if current_page > 0:
            carousel.scroll_to(carousel.get_nth_page(current_page - 1), True)
            # Focus the rightmost toggle on the previous page
            target_beat_index = (current_page - 1) * self.beats_per_page + (
                self.beats_per_page - 1
            )
            return self._focus_target_toggle(drum_part, target_beat_index)

        # If we're on the first page, go to instrument button
        return self._navigate_to_instrument_button(drum_part)

    def _navigate_to_instrument_button(self, drum_part):
        """Navigate to the instrument button."""
        try:
            instrument_button = getattr(self.window, f"{drum_part}_instrument_button")
            instrument_button.grab_focus()
            return True
        except AttributeError as e:
            logging.debug(
                f"Instrument button not found: {drum_part}_instrument_button: {e}"
            )
            return True

    def _navigate_to_target(self, drum_part, global_beat_index, target_beat_index):
        """Navigate to target toggle button."""
        self._scroll_if_needed(global_beat_index, target_beat_index)
        return self._focus_target_toggle(drum_part, target_beat_index)

    def _scroll_if_needed(self, global_beat_index, target_beat_index):
        """Scroll carousel if crossing page boundary."""
        current_page_index = global_beat_index // self.beats_per_page
        target_page_index = target_beat_index // self.beats_per_page

        if current_page_index != target_page_index:
            carousel = self.window.carousel
            n_pages = carousel.get_n_pages()
            if 0 <= target_page_index < n_pages:
                carousel.scroll_to(carousel.get_nth_page(target_page_index), True)

    def _focus_target_toggle(self, drum_part, target_beat_index):
        """Focus the target toggle button."""
        try:
            target_toggle = getattr(
                self.window, f"{drum_part}_toggle_{target_beat_index}"
            )
            target_toggle.grab_focus()
            return True
        except AttributeError as e:
            logging.debug(
                f"Target toggle not found: {drum_part}_toggle_{target_beat_index}: {e}"
            )
            return True

    def _setup_instrument_button_right_click(self, button, drum_part):
        """Setup right-click gesture for instrument button to remove drum part"""
        right_click_gesture = Gtk.GestureClick.new()
        right_click_gesture.set_button(Gdk.BUTTON_SECONDARY)
        right_click_gesture.connect(
            "released", self._on_drum_part_button_right_clicked, drum_part.id
        )
        button.add_controller(right_click_gesture)

    def _on_drum_part_button_right_clicked(self, gesture_click, n_press, x, y, drum_id):
        """Handle right-click on instrument buttons to show context menu"""
        self._show_drum_part_context_menu(gesture_click.get_widget(), drum_id)

    def _show_drum_part_context_menu(self, button, drum_id):
        """Show context menu for drum part button"""
        popover = Gtk.Popover()
        popover.set_parent(button)

        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Build menu items
        can_remove = (
            len(self.window.sound_service.drum_part_manager.get_all_parts()) > 1
        )

        menu_items = [
            (_("Preview"), self._on_preview_clicked, True, None),
            (
                _("Replace…"),
                self._on_replace_clicked,
                True,
                _("Replace with new sound"),
            ),
            (
                _("Remove"),
                self._on_remove_clicked,
                can_remove,
                None if can_remove else _("At least one drum part must remain"),
            ),
            None,
            (
                _("MIDI Mapping"),
                self._on_midi_mapping_clicked,
                True,
                _("Configure MIDI note for export"),
            ),
        ]

        # Create buttons
        for item in menu_items:
            if item is None:
                menu_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
                continue

            label, callback, enabled, tooltip = item
            btn = self._create_menu_button(
                label, callback, drum_id, popover, enabled, tooltip
            )
            menu_box.append(btn)

        popover.set_child(menu_box)
        popover.popup()

    def _create_menu_button(
        self, label, callback, drum_id, popover, enabled=True, tooltip=None
    ):
        """Create a menu button with consistent styling"""
        btn = Gtk.Button(label=label)
        btn.add_css_class("flat")
        btn.set_sensitive(enabled)

        if enabled:
            btn.connect("clicked", callback, drum_id, popover)

        if tooltip:
            btn.set_tooltip_text(tooltip)

        return btn

    def _on_preview_clicked(self, button, drum_id, popover):
        """Handle preview button click"""
        self.window.drum_machine_service.preview_drum_part(drum_id)
        popover.popdown()

    def _on_midi_mapping_clicked(self, button, drum_id, popover):
        """Handle MIDI mapping button click"""
        popover.popdown()

        drum_part_manager = self.window.sound_service.drum_part_manager
        drum_part = drum_part_manager.get_part_by_id(drum_id)

        if not drum_part:
            return

        dialog = MidiMappingDialog(self.window, drum_part, self._on_midi_mapping_save)
        dialog.present(self.window)

    def _on_midi_mapping_save(self, drum_id, note):
        """Callback for saving MIDI mapping"""
        drum_part_manager = self.window.sound_service.drum_part_manager
        if drum_part_manager.update_part_midi_note(drum_id, note):
            self.window.show_toast(_("MIDI note updated"))
            self.update_drum_button(drum_id)

    def _on_replace_clicked(self, button, drum_id, popover):
        """Handle replace button click"""
        popover.popdown()
        # Open file chooser
        self.window.file_dialog_handler.open_audio_file_chooser(
            _("Select New Sound"),
            self.window.drag_drop_handler.handle_replacement_file_selected,
            drum_id,
        )

    def _on_remove_clicked(self, button, drum_id, popover):
        """Handle remove button click"""
        # Get drum part name before removing it
        drum_part_manager = self.window.sound_service.drum_part_manager
        drum_part = drum_part_manager.get_part_by_id(drum_id)
        drum_name = drum_part.name if drum_part else drum_id

        result = self.window.drum_machine_service.remove_drum_part(drum_id)
        if result:
            self.window.show_toast(_("Removed drum part: {}").format(drum_name))
            # Mark as unsaved when removing drum parts
            self.window.save_changes_service.mark_unsaved_changes(True)
            self.window.update_export_button_sensitivity()
        else:
            self.window.show_toast(_("Failed to remove drum part"))

        popover.popdown()

    def _create_beat_grid_page(self, page_index):
        """Creates a single page containing a full set of instrument tracks."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Get drum parts from the sound service
        drum_part_manager = self.window.sound_service.drum_part_manager
        for drum_part in drum_part_manager.get_all_parts():
            drum_row = self.create_drum_row(drum_part.id, page_index)
            page.append(drum_row)
        return page

    def create_drum_row(self, drum_part, page_index):
        """Create a complete row for a drum part"""
        instrument_container = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=10
        )
        num_beat_groups = (
            self.beats_per_page + GROUP_TOGGLE_COUNT - 1
        ) // GROUP_TOGGLE_COUNT

        for group_index in range(num_beat_groups):
            beat_group = self.create_beat_toggle_group(
                drum_part, group_index, page_index
            )
            instrument_container.append(beat_group)

            if group_index != num_beat_groups - 1:
                beat_group.set_margin_end(20)

        return instrument_container

    def _create_drum_button(self, label, tooltip_text, clickable=True, drum_part=None):
        """Create a drum button with consistent styling"""
        button = Gtk.Button(label=label)
        button.set_halign(Gtk.Align.START)
        button.add_css_class("drum-part-button")
        button.add_css_class("flat")
        button.set_tooltip_text(tooltip_text)
        button.set_has_tooltip(True)

        if not clickable:
            button.set_sensitive(False)

        if drum_part and clickable:
            button.connect(
                "clicked", self.window.on_drum_part_button_clicked, drum_part.id
            )

            key_controller = Gtk.EventControllerKey.new()
            key_controller.connect(
                "key-pressed", self._on_instrument_button_key_pressed, drum_part.id
            )
            button.add_controller(key_controller)

            # Add right-click gesture for removing drum parts
            self._setup_instrument_button_right_click(button, drum_part)

            setattr(self.window, f"{drum_part.id}_instrument_button", button)

            # Setup drag and drop for replacement

        if drum_part:
            self.window.drag_drop_handler.setup_button_drop_target(button, drum_part.id)
        else:
            self.window.drag_drop_handler.setup_button_drop_target(button)
        return button

    def _create_button_container(self, button):
        """Create button container with consistent layout"""
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_container.set_spacing(5)
        button_container.append(button)

        spacer = Gtk.Label()
        spacer.set_hexpand(True)
        button_container.append(spacer)

        return button_container

    def create_instrument_button(self, drum_part):
        """Create the instrument preview button"""
        # Calculate button content first
        label, tooltip = self._get_button_content(drum_part)

        button = self._create_drum_button(
            label, tooltip, clickable=True, drum_part=drum_part
        )

        # Apply styling based on file availability
        self._apply_button_styling(button, drum_part)

        return self._create_button_container(button)

    def _get_button_content(self, drum_part):
        """Get the label and tooltip for a drum part button"""
        # Truncate long names to keep UI clean
        max_length = 11
        display_name = (
            drum_part.name[: max_length - 3] + "…"
            if len(drum_part.name) > max_length
            else drum_part.name
        )

        # Handle temporary parts
        if not drum_part.file_path:
            tooltip_text = (
                f"Temporary part: {drum_part.name} (MIDI Note {drum_part.midi_note_id})"
            )
            return display_name, tooltip_text

        # Check if the file is available
        drum_part_manager = self.window.sound_service.drum_part_manager
        file_available = drum_part_manager.is_file_available(drum_part.id)

        # Create tooltip text based on file availability
        if file_available:
            tooltip_text = f"Click to Preview {drum_part.name}"
        else:
            tooltip_text = f"Missing file: {drum_part.file_path}"

        return display_name, tooltip_text

    def _apply_button_styling(self, button, drum_part):
        """Apply styling to a button based on file availability"""
        drum_part_manager = self.window.sound_service.drum_part_manager
        file_available = drum_part_manager.is_file_available(drum_part.id)

        if file_available:
            button.remove_css_class("disabled")
        else:
            button.add_css_class("disabled")

    def update_button_content(self, button, drum_part):
        """Update button content (label, tooltip, disabled state) for a drum part"""
        label, tooltip = self._get_button_content(drum_part)

        button.set_label(label)
        button.set_tooltip_text(tooltip)
        self._apply_button_styling(button, drum_part)

    def update_drum_button(self, drum_id):
        """Update an existing drum button's state"""
        try:
            # Get the drum part
            drum_part_manager = self.window.sound_service.drum_part_manager
            drum_part = drum_part_manager.get_part_by_id(drum_id)
            if not drum_part:
                logging.warning(f"Drum part not found: {drum_id}")
                return

            # Find and update the button
            button_attr = f"{drum_id}_instrument_button"
            if hasattr(self.window, button_attr):
                button = getattr(self.window, button_attr)
                # Use the shared logic
                self.update_button_content(button, drum_part)
            else:
                # Button doesn't exist, rebuild the drum parts column
                self.rebuild_drum_parts_column()
        except Exception as e:
            logging.error(
                f"Error updating drum button for {drum_id}: {e}", exc_info=True
            )
            # Fallback: rebuild the drum parts column
            self.rebuild_drum_parts_column()

    def create_beat_toggle_group(self, drum_part, group_index, page_index):
        """Create a group of beat toggles"""
        beat_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        for position in range(GROUP_TOGGLE_COUNT):
            beat_number_on_page = group_index * GROUP_TOGGLE_COUNT + position + 1
            if beat_number_on_page > self.beats_per_page:
                break
            beat_toggle = self.create_single_beat_toggle(
                drum_part, beat_number_on_page, page_index
            )
            beat_group.append(beat_toggle)

        return beat_group

    def rebuild_drum_parts_column(self):
        """Rebuild the drum parts column to reflect current drum parts"""
        try:
            # Get the current drum parts column
            if not self.drum_parts_column:
                return

            # Clear existing children
            while self.drum_parts_column.get_first_child():
                self.drum_parts_column.remove(self.drum_parts_column.get_first_child())

            # Rebuild with current drum parts
            drum_part_manager = self.window.sound_service.drum_part_manager
            for drum_part in drum_part_manager.get_all_parts():
                instrument_button = self.create_instrument_button(drum_part)
                self.drum_parts_column.append(instrument_button)

        except Exception as e:
            logging.error(f"Error rebuilding drum parts column: {e}", exc_info=True)

    def create_single_beat_toggle(self, drum_part, beat_number_on_page, page_index):
        """Create a single beat toggle button"""
        global_beat_index = page_index * self.beats_per_page + (beat_number_on_page - 1)

        beat_toggle = Gtk.ToggleButton()
        beat_toggle.set_size_request(20, 20)
        beat_toggle.set_name(f"{drum_part}_toggle_{global_beat_index}")
        beat_toggle.set_valign(Gtk.Align.CENTER)
        beat_toggle.add_css_class("drum-toggle")
        beat_toggle.connect(
            "toggled", self.window.on_toggle_changed, drum_part, global_beat_index
        )

        toggle_key_controller = Gtk.EventControllerKey.new()
        toggle_key_controller.connect(
            "key-pressed", self._on_toggle_key_pressed, drum_part, global_beat_index
        )
        beat_toggle.add_controller(toggle_key_controller)

        right_click_gesture = Gtk.GestureClick.new()
        right_click_gesture.set_button(Gdk.BUTTON_SECONDARY)
        right_click_gesture.connect(
            "released", self.window._on_right_click_released, beat_toggle
        )
        beat_toggle.add_controller(right_click_gesture)

        setattr(self.window, f"{drum_part}_toggle_{global_beat_index}", beat_toggle)
        return beat_toggle

    def update_drum_parts_spacing(self, is_compact):
        """Updates the spacing of the drum parts column."""
        if self.drum_parts_column:
            new_spacing = 12 if is_compact else 10
            self.drum_parts_column.set_spacing(new_spacing)

    def add_drum_part(self, drum_part):
        """Add a new drum part to the existing interface"""
        # Add new instrument button to drum parts column
        if self.drum_parts_column:
            instrument_button = self.create_instrument_button(drum_part)
            self.drum_parts_column.append(instrument_button)

        # Add new drum row to each carousel page
        if hasattr(self.window, "carousel"):
            n_pages = self.window.carousel.get_n_pages()
            for page_index in range(n_pages):
                page = self.window.carousel.get_nth_page(page_index)
                drum_row = self.create_drum_row(drum_part.id, page_index)
                page.append(drum_row)

    def _create_placeholder_button_container(self):
        """Create a placeholder button container"""
        placeholder_button = self._create_drum_button(
            "+ New", "Drop audio files here to add new drum", clickable=True
        )
        return self._create_button_container(placeholder_button)

    def create_new_drum_placeholder(self):
        """Create the 'New Drum' placeholder at the end of the drum parts column"""
        if not self.drum_parts_column:
            return None

        placeholder_container = self._create_placeholder_button_container()
        placeholder_container.add_css_class("new-drum-placeholder")

        self.drum_parts_column.append(placeholder_container)

        placeholder_container.queue_allocate()
        return placeholder_container

    def remove_new_drum_placeholder(self, placeholder):
        """Remove the new drum placeholder from the drum parts column"""
        if (
            placeholder
            and self.drum_parts_column
            and placeholder.get_parent() == self.drum_parts_column
        ):
            self.drum_parts_column.remove(placeholder)
