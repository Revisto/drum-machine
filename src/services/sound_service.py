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

import os
import pygame
from ..interfaces.sound import ISoundService
from .drum_part_manager import DrumPartManager


class SoundService(ISoundService):
    def __init__(self, drumkit_dir):
        pygame.init()
        pygame.mixer.set_num_channels(32)
        self.drumkit_dir = drumkit_dir
        self.drum_part_manager = DrumPartManager(drumkit_dir)
        self.sounds = {}

    def load_sounds(self):
        self.sounds = {}
        for part in self.drum_part_manager.get_all_parts():
            try:
                self.sounds[part.id] = pygame.mixer.Sound(part.file_path)
            except Exception as e:
                print(f"Error loading sound {part.name}: {e}")

    def reload_sounds(self):
        self.drum_part_manager._load_drum_parts()
        self.load_sounds()

    def play_sound(self, part_id):
        if part_id in self.sounds:
            self.sounds[part_id].play()

    def set_volume(self, volume):
        for sound in self.sounds.values():
            sound.set_volume(volume / 100)

    def preview_sound(self, part_id):
        if part_id in self.sounds:
            self.play_sound(part_id)
    
    def get_drum_part_manager(self):
        return self.drum_part_manager
