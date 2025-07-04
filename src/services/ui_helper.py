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


class UIHelper:
    def __init__(self, window, toggle_parts, num_toggles):
        self.window = window
        self.toggle_parts = toggle_parts
        self.num_toggles = num_toggles

    def _set_playhead_highlight_for_beat(self, beat_index, highlight_on):
        """
        Internal helper to add or remove the 'playhead-active' CSS class
        for a vertical column of toggles at a specific beat index.
        """
        for part in self.toggle_parts:
            toggle = getattr(self.window, f"{part}_toggle_{beat_index}")
            if highlight_on:
                toggle.get_style_context().add_class("toggle-active")
            else:
                toggle.get_style_context().remove_class("toggle-active")

    def highlight_playhead_at_beat(self, beat_index):
        self._set_playhead_highlight_for_beat(beat_index, highlight_on=True)

    def remove_playhead_highlight_at_beat(self, beat_index):
        self._set_playhead_highlight_for_beat(beat_index, highlight_on=False)

    def clear_all_playhead_highlights(self):
        """Removes all playhead highlights from the currently visible toggles."""
        # This is inefficient and will be slow with many pages.
        # It should ideally track the last highlighted beat and only clear that one.
        for i in range(self.num_toggles):
            self._set_playhead_highlight_for_beat(i, highlight_on=False)

    def deactivate_all_toggles_in_ui(self):
        """Sets the state of all currently rendered toggles to inactive (OFF)."""
        for part in self.toggle_parts:
            for i in range(self.num_toggles * self.window.carousel.get_n_pages()):
                try:
                    toggle = getattr(self.window, f"{part}_toggle_{i}")
                    toggle.set_active(False)
                except AttributeError:
                    continue

    def load_pattern_into_ui(self, pattern_data):
        """
        Updates the UI to reflect a new pattern.
        This is fundamentally broken with the dynamic grid and needs a redesign.
        The UI should pull data when it's created, not have data pushed to it.
        """
        for part, active_beats in pattern_data.items():
            for beat_index in active_beats.keys():
                toggle = getattr(self.window, f"{part}_toggle_{beat_index}")
                toggle.set_active(True)

    def set_bpm_in_ui(self, bpm_value):
        """Updates the BPM spin button with a new value."""
        self.window.bpm_spin_button.set_value(bpm_value)
