# services/drum_machine_service.py
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

import threading
import time
from gi.repository import GLib
from ..interfaces.player import IPlayer
from ..config import DRUM_PARTS, NUM_TOGGLES, GROUP_TOGGLE_COUNT
from .preset_service import PresetService
from .ui_helper import UIHelper


class DrumMachineService(IPlayer):
    def __init__(self, sound_service, ui_helper: UIHelper):
        self.sound_service = sound_service
        self.ui_helper = ui_helper
        self.playing = False
        self.bpm = 120
        self.volume = 0.8
        self.last_volume = 100
        self.play_thread = None
        self.stop_event = threading.Event()
        self.drum_parts_state = self.create_empty_drum_parts_state()
        self.preset_service = PresetService()
        self.total_beats = NUM_TOGGLES
        self.beats_per_page = NUM_TOGGLES
        self.active_pages = 1
        self.playing_beat = -1

    def create_empty_drum_parts_state(self):
        drum_parts_state = {part: dict() for part in DRUM_PARTS}
        return drum_parts_state

    def play(self):
        self.playing = True
        self.stop_event.clear()
        self.play_thread = threading.Thread(target=self._play_drum_sequence)
        self.play_thread.start()

    def stop(self):
        self.playing = False
        self.stop_event.set()
        self.ui_helper.clear_all_playhead_highlights()
        self.playing_beat = -1
        if self.play_thread:
            self.play_thread.join()
            self.play_thread = None

    def update_total_beats(self):
        """
        Calculates the total number of beats and active pages
        based on the highest active toggle.
        """
        max_beat = 0
        for part_state in self.drum_parts_state.values():
            if part_state:  # Check if the instrument has any active toggles
                max_beat = max(max_beat, max(part_state.keys()))

        # If the pattern is completely empty, default to one page.
        if max_beat == 0 and not any(self.drum_parts_state.values()):
            num_pages = 1
        else:
            # Calculate pages needed for the highest beat.
            num_pages = (max_beat // self.beats_per_page) + 1

        self.active_pages = num_pages
        self.total_beats = self.active_pages * self.beats_per_page

    def set_bpm(self, bpm):
        self.bpm = bpm

    def set_volume(self, volume):
        self.volume = volume
        self.sound_service.set_volume(volume)
        if volume != 0:
            self.last_volume = volume
        else:
            pass

    def clear_all_toggles(self):
        self.drum_parts_state = self.create_empty_drum_parts_state()
        self.ui_helper.deactivate_all_toggles_in_ui()

    def save_preset(self, file_path):
        self.preset_service.save_preset(file_path, self.drum_parts_state, self.bpm)

    def load_preset(self, file_path):
        self.ui_helper.deactivate_all_toggles_in_ui()
        self.drum_parts_state, self.bpm = self.preset_service.load_preset(file_path)
        self.ui_helper.set_bpm_in_ui(self.bpm)

    def _play_drum_sequence(self):
        current_beat = 0
        while self.playing and not self.stop_event.is_set():
            # Check if the loop should end or wrap around
            if current_beat >= self.total_beats:
                current_beat = 0  # Loop back to the beginning

            if self.stop_event.is_set():
                break

            # Highlight the current beat (this will also de-highlight the previous one)
            self.ui_helper.highlight_playhead_at_beat(current_beat)
            self.playing_beat = current_beat

            if current_beat % self.beats_per_page == 0 or current_beat == 0:
                target_page = current_beat // self.beats_per_page
                GLib.idle_add(self.ui_helper.scroll_carousel_to_page, target_page)

            # Play sounds for the current beat
            for part in DRUM_PARTS:
                if self.drum_parts_state[part].get(current_beat, False):
                    self.sound_service.play_sound(part)

            # Wait for the next beat
            delay_per_step = 60 / self.bpm / GROUP_TOGGLE_COUNT
            time.sleep(delay_per_step)

            self.ui_helper.remove_playhead_highlight_at_beat(current_beat)

            # Advance the playhead
            current_beat += 1

    def preview_drum_part(self, part):
        """Preview a drum part sound"""
        if part in DRUM_PARTS:
            self.sound_service.preview_sound(part)
