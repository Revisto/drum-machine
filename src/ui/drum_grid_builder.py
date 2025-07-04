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
from gi.repository import Gtk, Gdk, Adw
from ..config import DRUM_PARTS, NUM_TOGGLES, GROUP_TOGGLE_COUNT


class DrumGridBuilder:
    """Responsible for building the drum grid UI components"""

    def __init__(self, window):
        self.window = window

    def build_drum_machine_interface(self):
        """Build the complete drum machine grid interface"""
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_container.set_name("main_container")
        
        # Create horizontal layout with drum parts on left, carousel on right
        horizontal_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        horizontal_layout.set_homogeneous(False)
        
        # Create fixed drum parts column
        drum_parts_column = self._create_drum_parts_column()
        
        # Create carousel with drum rows
        carousel = self._create_carousel_drum_rows()
        
        horizontal_layout.append(drum_parts_column)
        horizontal_layout.append(carousel)
        main_container.append(horizontal_layout)
        
        # Add dots indicator
        dots = self._create_dots_indicator(carousel)
        main_container.append(dots)
        
        return main_container

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
        self.window.carousel = carousel
        carousel.connect("page-changed", self._on_page_changed)
        
        for i in range(2):
            page = self._create_beat_grid_page(i)
            carousel.append(page)
        
        return carousel

    def _on_page_changed(self, carousel, index):
        """Dynamically add/remove pages when the carousel page changes."""
        n_pages = carousel.get_n_pages()
        
        # Add a new page when the user scrolls to the last one
        if index == n_pages - 1:
            new_page = self._create_beat_grid_page(n_pages)
            carousel.append(new_page)
        # Remove the last page if it's more than one page ahead of the current one
        elif n_pages > index + 2:
            page_to_remove = carousel.get_nth_page(n_pages - 1)
            carousel.remove(page_to_remove)

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
        num_beat_groups = (NUM_TOGGLES + GROUP_TOGGLE_COUNT - 1) // GROUP_TOGGLE_COUNT

        for group_index in range(num_beat_groups):
            beat_group = self.create_beat_toggle_group(drum_part, group_index, page_index)
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
            if beat_number_on_page > NUM_TOGGLES:
                break
            beat_toggle = self.create_single_beat_toggle(drum_part, beat_number_on_page, page_index)
            beat_group.append(beat_toggle)

        return beat_group

    def create_single_beat_toggle(self, drum_part, beat_number_on_page, page_index):
        """Create a single beat toggle button"""
        # This will be the unique beat index across all pages
        global_beat_index = page_index * NUM_TOGGLES + (beat_number_on_page - 1)

        beat_toggle = Gtk.ToggleButton()
        beat_toggle.set_size_request(20, 20)
        beat_toggle.set_name(f"{drum_part}_toggle_{global_beat_index}")
        beat_toggle.set_valign(Gtk.Align.CENTER)
        beat_toggle.add_css_class("drum-toggle")
        beat_toggle.connect(
            "toggled", self.window.on_toggle_changed, drum_part, global_beat_index
        )

        right_click_gesture = Gtk.GestureClick.new()
        right_click_gesture.set_button(Gdk.BUTTON_SECONDARY)
        right_click_gesture.connect(
            "released", self.window._on_right_click_released, beat_toggle
        )
        beat_toggle.add_controller(right_click_gesture)

        setattr(self.window, f"{drum_part}_toggle_{global_beat_index}", beat_toggle)
        return beat_toggle
