# services/sound_service.py
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

import pygame
import logging
from typing import Dict
from ..interfaces.sound import ISoundService
from .drum_part_manager import DrumPartManager
from ..config.constants import MIXER_CHANNELS


class SoundService(ISoundService):
    def __init__(self, user_data_dir: str, bundled_sounds_dir: str = None) -> None:
        pygame.init()
        pygame.mixer.set_num_channels(MIXER_CHANNELS)
        self.user_data_dir = user_data_dir
        self.bundled_sounds_dir = bundled_sounds_dir or user_data_dir
        self.drum_part_manager = DrumPartManager(user_data_dir, self.bundled_sounds_dir)
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self._current_volume: float = 1.0

    def load_sounds(self) -> None:
        self.sounds = {}
        for part in self.drum_part_manager.get_all_parts():
            try:
                # Skip temporary parts without file paths
                if not part.file_path:
                    continue

                sound = pygame.mixer.Sound(part.file_path)
                sound.set_volume(self._current_volume)
                self.sounds[part.id] = sound
            except Exception as e:
                logging.error(f"Error loading sound {part.name}: {e}")

    def reload_sounds(self) -> None:
        self.drum_part_manager.reload()
        self.load_sounds()

    def reload_specific_sound(self, part_id: str) -> None:
        """Reload a specific sound after drum part replacement"""
        self.drum_part_manager.reload()
        part = self.drum_part_manager.get_part_by_id(part_id)
        if part:
            sound = pygame.mixer.Sound(part.file_path)
            sound.set_volume(self._current_volume)
            self.sounds[part_id] = sound

    def play_sound(self, part_id: str) -> None:
        if part_id in self.sounds:
            self.sounds[part_id].play()

    def set_volume(self, volume: float) -> None:
        self._current_volume = volume / 100
        for sound in self.sounds.values():
            sound.set_volume(self._current_volume)

    def preview_sound(self, part_id: str) -> None:
        if part_id in self.sounds:
            self.play_sound(part_id)
