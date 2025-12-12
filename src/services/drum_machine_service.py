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
import logging
from typing import Dict, Optional
from gi.repository import GLib
from ..interfaces.player import IPlayer
from ..config.constants import NUM_TOGGLES, GROUP_TOGGLE_COUNT
from .pattern_service import PatternService
from .ui_helper import UIHelper


class DrumMachineService(IPlayer):
    def __init__(self, window, sound_service, ui_helper: UIHelper) -> None:
        self.window = window
        self.sound_service = sound_service
        self.ui_helper = ui_helper
        self.playing: bool = False
        self.bpm: float = 120
        self.last_volume: float = 100
        self.play_thread: Optional[threading.Thread] = None
        self.stop_event: threading.Event = threading.Event()
        self.drum_parts_state: Dict[str, Dict[int, bool]] = (
            self.create_empty_drum_parts_state()
        )
        self.pattern_service = PatternService(window)
        self.total_beats: int = NUM_TOGGLES
        self.beats_per_page: int = NUM_TOGGLES
        self.active_pages: int = 1
        self.playing_beat: int = -1

    def create_empty_drum_parts_state(self) -> Dict[str, Dict[int, bool]]:
        # Get drum parts from sound service
        drum_parts = self.sound_service.drum_part_manager.get_all_parts()
        drum_parts_state = {part.id: dict() for part in drum_parts}
        return drum_parts_state

    def play(self) -> None:
        self.playing = True
        self.stop_event.clear()
        self.play_thread = threading.Thread(target=self._play_drum_sequence)
        self.play_thread.start()

    def stop(self) -> None:
        self.playing = False
        self.stop_event.set()
        self.sound_service.stop_all_sounds()
        self.ui_helper.clear_all_playhead_highlights()
        self.playing_beat = -1
        if self.play_thread:
            self.play_thread.join()
            self.play_thread = None

    def update_total_beats(self) -> None:
        """
        Calculates the total number of beats and active pages
        based on the highest active toggle.
        """
        max_beat = 0
        for part_state in self.drum_parts_state.values():
            if part_state:  # Check if the instrument has any active toggles
                max_beat = max(max_beat, *part_state.keys())

        # If the pattern is completely empty, default to one page.
        if max_beat == 0 and not any(self.drum_parts_state.values()):
            num_pages = 1
        else:
            # Calculate pages needed for the highest beat.
            num_pages = (max_beat // self.beats_per_page) + 1

        self.active_pages = num_pages
        self.total_beats = self.active_pages * self.beats_per_page

    def set_bpm(self, bpm: float) -> None:
        self.bpm = bpm

    def set_volume(self, volume: float) -> None:
        self.sound_service.set_volume(volume)
        if volume != 0:
            self.last_volume = volume

    def clear_all_toggles(self) -> None:
        self.drum_parts_state = self.create_empty_drum_parts_state()
        self.ui_helper.deactivate_all_toggles_in_ui()

    def save_pattern(self, file_path: str) -> None:
        self.pattern_service.save_pattern(file_path, self.drum_parts_state, self.bpm)

    def load_pattern(self, file_path: str) -> None:
        self.ui_helper.deactivate_all_toggles_in_ui()
        self.drum_parts_state, self.bpm = self.pattern_service.load_pattern(file_path)

        # Refresh UI to show new temporary parts
        self.window.drum_grid_builder.rebuild_drum_parts_column()
        self.window.drum_grid_builder.rebuild_carousel()

        self.ui_helper.set_bpm_in_ui(self.bpm)

    def _play_drum_sequence(self) -> None:
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
            drum_parts = self.sound_service.drum_part_manager.get_all_parts()
            for part in drum_parts:
                if self.drum_parts_state[part.id].get(current_beat, False):
                    self.sound_service.play_sound(part.id)

            # Wait for the next beat
            delay_per_step = 60 / self.bpm / GROUP_TOGGLE_COUNT
            time.sleep(delay_per_step)

            GLib.idle_add(
                self.ui_helper.remove_playhead_highlight_at_beat, current_beat
            )

            # Advance the playhead
            current_beat += 1

    def preview_drum_part(self, part_id: str) -> None:
        """Preview a drum part sound"""
        drum_part_manager = self.sound_service.drum_part_manager
        if drum_part_manager.get_part_by_id(part_id):
            self.sound_service.preview_sound(part_id)

    def add_drum_part_state(self, part_id: str) -> None:
        """Add a new drum part to the state"""
        self.drum_parts_state[part_id] = {}

    def add_new_drum_part(self, file_path: str, name: str) -> Optional[object]:
        """Add a new drum part from an audio file"""
        new_part = self.sound_service.drum_part_manager.add_custom_part(name, file_path)
        if new_part:
            # Reload sounds
            self.sound_service.reload_sounds()
            # Add to drum machine state
            self.add_drum_part_state(new_part.id)
            # Update UI
            self.window.drum_grid_builder.add_drum_part(new_part)
            return new_part
        return None

    def replace_drum_part(
        self, drum_id: str, file_path: str, name: str
    ) -> Optional[object]:
        """Replace an existing drum part with a new audio file"""
        result = self.sound_service.drum_part_manager.replace_part(
            drum_id, file_path, name
        )
        if result:
            # Reload the specific sound for this drum part
            self.sound_service.reload_specific_sound(drum_id)
            # Update UI button label
            self.window.drum_grid_builder.update_drum_button(drum_id)
            # Update total beats in case pattern changed
            self.update_total_beats()
            return result
        return None

    def remove_drum_part(self, drum_id: str) -> bool:
        """Remove a drum part from the service"""
        result = self.sound_service.drum_part_manager.remove_part(drum_id)
        if result:
            # Remove from drum machine state
            self.drum_parts_state.pop(drum_id, None)
            # Rebuild the UI to reflect the removal
            self.window.drum_grid_builder.rebuild_drum_parts_column()
            self.window.drum_grid_builder.rebuild_carousel()
            # Update total beats in case pattern changed
            self.update_total_beats()
            logging.info(f"Removed drum part: {drum_id}")
            return True
        else:
            logging.error(f"Failed to remove drum part: {drum_id}")
            return False
