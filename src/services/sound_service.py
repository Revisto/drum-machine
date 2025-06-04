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
from ..config import DRUM_PARTS


class SoundService(ISoundService):
    def __init__(self, drumkit_dir):
        pygame.init()
        self.drumkit_dir = drumkit_dir
        self.sounds = {}

    def load_sounds(self):

        self.sounds = {
            drum_part: pygame.mixer.Sound(
                os.path.join(self.drumkit_dir, f"{drum_part}.wav")
            )
            for drum_part in DRUM_PARTS
        }

    def play_sound(self, sound_name):
        self.sounds[sound_name].play()

    def set_volume(self, volume):
        for sound in self.sounds.values():
            sound.set_volume(volume / 100)

    def preview_sound(self, sound_name):
        if sound_name in self.sounds:
            self.play_sound(sound_name)
