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

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk, Adw, GLib
from ..config import DRUM_PARTS, GROUP_TOGGLE_COUNT


class DrumGridBuilder:
    """Responsible for building the drum grid UI components"""

    def __init__(self, window):
        self.window = window
        self.main_container = None

    @property
    def beats_per_page(self):
        """Get the current number of beats per page from the grid builder."""
        return self.window.drum_machine_service.beats_per_page

    def build_drum_machine_interface(self):
        """Build the static drum machine interface and placeholders."""
        self.main_container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=10
        )
        self.main_container.set_name("main_container")

        horizontal_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        horizontal_layout.set_homogeneous(False)

        drum_parts_column = self._create_drum_parts_column()
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
        """
        Builds or rebuilds only the carousel and its indicator dots.
        """
        # Clear only the dynamic parts by removing them from their containers
        if self.carousel_container.get_first_child():
            self.carousel_container.remove(self.carousel_container.get_first_child())
        if self.dots_container.get_first_child():
            self.dots_container.remove(self.dots_container.get_first_child())

        # Create the new carousel and dots
        carousel = self._create_carousel_drum_rows()
        dots = self._create_dots_indicator(carousel)

        # Add the new widgets to their containers
        self.carousel_container.append(carousel)
        self.dots_container.append(dots)

        # Update state and scroll to the correct page
        self.window.drum_machine_service.update_total_beats()
        new_target_page = (
            focus_beat_index // self.beats_per_page
        )
        self.window.drum_machine_service.active_pages = new_target_page + 1
        self.reset_carousel_pages()
        self.window.ui_helper.load_pattern_into_ui(
            self.window.drum_machine_service.drum_parts_state
        )
        GLib.timeout_add(50, self._scroll_carousel_to_page_safely, new_target_page)

    def _scroll_carousel_to_page_safely(self, page_index):
        """
        Scrolls the carousel to a specific page, ensuring it exists.
        This is intended to be called via GLib.idle_add.
        """
        if hasattr(self.window, "carousel"):
            n_pages = self.window.carousel.get_n_pages()
            # Clamp the index to be within valid bounds
            target_page = max(0, min(page_index, n_pages - 1))
            if n_pages > 0:
                self.window.carousel.scroll_to(
                    self.window.carousel.get_nth_page(target_page), True
                )
        return GLib.SOURCE_REMOVE  # Ensures the function is called only once

    def _create_dots_indicator(self, carousel):
        """Create dots indicator for the carousel"""
        dots = Adw.CarouselIndicatorDots()
        dots.set_carousel(carousel)
        dots.set_margin_top(10)
        return dots

    def _create_drum_parts_column(self):
        """Create the drum parts buttons column"""
        drum_parts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for drum_part in DRUM_PARTS:
            instrument_button = self.create_instrument_button(drum_part)
            drum_parts.append(instrument_button)
        return drum_parts

    def _create_carousel_drum_rows(self):
        """Create carousel with drum rows"""
        carousel = Adw.Carousel()
        carousel.set_spacing(30)
        self.window.carousel = carousel
        carousel.connect("page-changed", self._on_page_changed)

        # Add a key controller to intercept and handle arrow keys
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self._on_carousel_key_pressed)
        carousel.add_controller(key_controller)

        for i in range(2):
            page = self._create_beat_grid_page(i)
            carousel.append(page)

        return carousel

    def _on_page_changed(self, carousel, index):
        self.reset_carousel_pages()

    def reset_carousel_pages(self):
        """
        Resets the carousel pages to match the number of active pages in the
        current pattern, plus one empty page at the end, while also ensuring
        the user's currently viewed page is not removed.
        """
        carousel = self.window.carousel

        # Get the number of pages required by the pattern.
        active_pages_in_pattern = self.window.drum_machine_service.active_pages
        pages_for_pattern = active_pages_in_pattern + 1

        # Get the number of pages required by the user's current view.
        current_page_index = carousel.get_position()
        pages_for_view = current_page_index + 2  # Current page, plus one extra

        # The desired number of pages is the greater of the two requirements.
        # Also ensure a minimum of 2 pages.
        desired_pages = max(2, pages_for_pattern, pages_for_view)

        n_pages = carousel.get_n_pages()

        # Add pages if we don't have enough
        while n_pages < desired_pages:
            new_page = self._create_beat_grid_page(n_pages)
            carousel.append(new_page)
            n_pages = carousel.get_n_pages()

        # Remove pages if we have too many
        while n_pages > desired_pages:
            page_to_remove = carousel.get_nth_page(n_pages - 1)
            carousel.remove(page_to_remove)
            n_pages = carousel.get_n_pages()

    def _on_carousel_key_pressed(self, controller, keyval, keycode, state):
        """
        Handles key presses on the carousel to prevent page navigation
        with arrow keys.
        """
        # Stop the Left and Right arrow keys from being processed by the carousel
        if keyval == Gdk.KEY_Left or keyval == Gdk.KEY_Right:
            return True  # Indicates the event is handled and stops propagation
        return False  # Let other keys be processed normally

    def _on_instrument_button_key_pressed(
        self, controller, keyval, keycode, state, drum_part
    ):
        """Handles right arrow key navigation from an instrument button to the grid."""
        if keyval == Gdk.KEY_Right:
            # Find the first toggle on the currently visible page for this instrument
            current_page_index = self.window.carousel.get_position()
            target_beat_index = int(
                current_page_index * self.beats_per_page
            )
            print(f"{drum_part}_toggle_{target_beat_index}")
            try:
                target_toggle = getattr(
                    self.window, f"{drum_part}_toggle_{target_beat_index}"
                )
                target_toggle.grab_focus()
                return True  # Event handled
            except AttributeError:
                return True  # Target doesn't exist, but we handled the key press
        return False

    def _on_toggle_key_pressed(
        self, controller, keyval, keycode, state, drum_part, global_beat_index
    ):
        """
        Handles arrow key navigation between individual toggle buttons,
        scrolling the carousel when moving across pages.
        """
        target_beat_index = -1
        if keyval == Gdk.KEY_Right:
            target_beat_index = global_beat_index + 1
        elif keyval == Gdk.KEY_Left:
            # If on the first beat of a page, navigate to the instrument button
            if global_beat_index % self.beats_per_page == 0:
                try:
                    instrument_button = getattr(
                        self.window, f"{drum_part}_instrument_button"
                    )
                    instrument_button.grab_focus()
                    return True  # Event handled
                except AttributeError:
                    return True  # Should not happen, but good to be safe
            else:
                target_beat_index = global_beat_index - 1

        if target_beat_index != -1:
            # Check if we are crossing a page boundary
            current_page_index = (
                global_beat_index // self.beats_per_page
            )
            target_page_index = (
                target_beat_index // self.beats_per_page
            )

            if current_page_index != target_page_index:
                # We need to scroll the carousel
                carousel = self.window.carousel
                n_pages = carousel.get_n_pages()
                # Make sure the target page exists or can be created
                if 0 <= target_page_index < n_pages:
                    carousel.scroll_to(carousel.get_nth_page(target_page_index), True)

            try:
                # Find the target toggle button using the name we assigned it
                target_toggle = getattr(
                    self.window, f"{drum_part}_toggle_{target_beat_index}"
                )
                target_toggle.grab_focus()
                return True  # Event handled
            except AttributeError:
                # Target toggle doesn't exist (start/end of the line), do nothing
                return True  # Still handle it to prevent other actions

        return False  # Not an arrow key we handle

    def _create_beat_grid_page(self, page_index):
        """Creates a single page containing a full set of instrument tracks."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for drum_part in DRUM_PARTS:
            drum_row = self.create_drum_row(drum_part, page_index)
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

    def create_instrument_button(self, drum_part):
        """Create the instrument preview button"""
        button_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_container.set_spacing(5)

        instrument_button = Gtk.Button(
            label=f"{drum_part.capitalize().replace('-', ' ')}"
        )
        instrument_button.set_halign(Gtk.Align.START)
        instrument_button.connect(
            "clicked", self.window.on_drum_part_button_clicked, drum_part
        )
        instrument_button.add_css_class("drum-part-button")
        instrument_button.add_css_class("flat")
        instrument_button.set_tooltip_text(
            f"Click to Preview {drum_part.capitalize().replace('-', ' ')}"
        )
        instrument_button.set_has_tooltip(True)

        # Add key controller to navigate back to the grid
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect(
            "key-pressed", self._on_instrument_button_key_pressed, drum_part
        )
        instrument_button.add_controller(key_controller)

        # Store the button on the window so we can focus it from the grid
        setattr(self.window, f"{drum_part}_instrument_button", instrument_button)

        button_container.append(instrument_button)
        spacer = Gtk.Label()
        spacer.set_hexpand(True)
        button_container.append(spacer)

        return button_container

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

    def create_single_beat_toggle(self, drum_part, beat_number_on_page, page_index):
        """Create a single beat toggle button"""
        # This will be the unique beat index across all pages
        global_beat_index = (
            page_index * self.beats_per_page
            + (beat_number_on_page - 1)
        )

        beat_toggle = Gtk.ToggleButton()
        beat_toggle.set_size_request(20, 20)
        beat_toggle.set_name(f"{drum_part}_toggle_{global_beat_index}")
        beat_toggle.set_valign(Gtk.Align.CENTER)
        beat_toggle.add_css_class("drum-toggle")
        beat_toggle.connect(
            "toggled", self.window.on_toggle_changed, drum_part, global_beat_index
        )

        # Add a key controller for arrow navigation between toggles
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
