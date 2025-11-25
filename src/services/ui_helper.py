# services/ui_helper.py
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

import logging
from typing import Dict


class UIHelper:
    def __init__(self, window) -> None:
        self.window = window

    @property
    def beats_per_page(self) -> int:
        """Get the current number of beats per page from the grid builder."""
        return self.window.drum_machine_service.beats_per_page

    def _set_playhead_highlight_for_beat(
        self, beat_index: int, highlight_on: bool
    ) -> None:
        """
        Internal helper to add or remove the 'playhead-active' CSS class
        for a vertical column of toggles at a specific beat index.
        """
        for part in self.window.sound_service.drum_part_manager.get_all_parts():
            try:
                toggle = getattr(self.window, f"{part.id}_toggle_{beat_index}")
                if highlight_on:
                    toggle.get_style_context().add_class("toggle-active")
                else:
                    toggle.get_style_context().remove_class("toggle-active")
            except AttributeError:
                logging.debug(
                    f"Toggle not found for playhead highlight: "
                    f"{part.id}_toggle_{beat_index}"
                )
                continue

    def highlight_playhead_at_beat(self, beat_index: int) -> None:
        self._set_playhead_highlight_for_beat(beat_index, highlight_on=True)

    def remove_playhead_highlight_at_beat(self, beat_index: int) -> None:
        self._set_playhead_highlight_for_beat(beat_index, highlight_on=False)

    def clear_all_playhead_highlights(self) -> None:
        """Removes all playhead highlights from the currently visible toggles."""
        # This is inefficient and will be slow with many pages.
        # It should ideally track the last highlighted beat and only clear that one.
        for i in range(self.beats_per_page * self.window.carousel.get_n_pages()):
            self._set_playhead_highlight_for_beat(i, highlight_on=False)

    def deactivate_all_toggles_in_ui(self) -> None:
        """Sets the state of all currently rendered toggles to inactive (OFF)."""
        total_toggles = self.beats_per_page * self.window.carousel.get_n_pages()
        for part in self.window.sound_service.drum_part_manager.get_all_parts():
            for i in range(total_toggles):
                try:
                    toggle = getattr(self.window, f"{part.id}_toggle_{i}")
                    if toggle.get_active():
                        toggle.set_active(False)
                except AttributeError:
                    logging.debug(
                        f"Toggle not found for deactivation: {part.id}_toggle_{i}"
                    )
                    continue

    def load_pattern_into_ui(
        self, drum_parts_state: Dict[str, Dict[int, bool]]
    ) -> None:
        """
        Updates the UI to reflect a new pattern.
        This is fundamentally broken with the dynamic grid and needs a redesign.
        The UI should pull data when it's created, not have data pushed to it.
        """
        for part_id in drum_parts_state:
            for beat_index in drum_parts_state[part_id].keys():
                toggle = getattr(self.window, f"{part_id}_toggle_{beat_index}")
                toggle.set_active(True)

    def set_bpm_in_ui(self, bpm_value: float) -> None:
        """Updates the BPM spin button with a new value."""
        self.window.bpm_spin_button.set_value(bpm_value)

    def scroll_carousel_to_page(self, page_index: int) -> None:
        """Delegates the request to scroll the carousel to the main window."""
        self.window.scroll_carousel_to_page(page_index)
