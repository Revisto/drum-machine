# services/drum_machine_service.py
#
# Copyright 2024 revisto
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
from ..interfaces.player import IPlayer

class DrumMachineService(IPlayer):
    def __init__(self, sound_service, ui_helper):
        self.sound_service = sound_service
        self.ui_helper = ui_helper
        self.playing = False
        self.bpm = 120
        self.volume = 0.8
        self.play_thread = None
        self.stop_event = threading.Event()
        self.drum_parts = {"kick": [False] * 16, "snare": [False] * 16, "hihat": [False] * 16}

    def play(self):
        self.playing = True
        self.stop_event.clear()
        self.play_thread = threading.Thread(target=self._play_drum_sequence)
        self.play_thread.start()

    def stop(self):
        self.playing = False
        self.stop_event.set()
        self.ui_helper.clear_highlight()
        if self.play_thread:
            self.play_thread.join()
            self.play_thread = None

    def set_bpm(self, bpm):
        self.bpm = bpm

    def set_volume(self, volume):
        self.volume = volume
        self.sound_service.set_volume(volume)

    def _play_drum_sequence(self):
        while self.playing and not self.stop_event.is_set():
            delay_per_step = 60 / self.bpm / 4
            for i in range(16):
                if self.stop_event.is_set():
                    return
                self.ui_helper.highlight_playing_bar(i)
                if self.drum_parts["kick"][i]:
                    self.sound_service.play_sound("kick")
                    print("Playing kick")
                if self.drum_parts["snare"][i]:
                    self.sound_service.play_sound("snare")
                if self.drum_parts["hihat"][i]:
                    self.sound_service.play_sound("hihat")
                time.sleep(delay_per_step)
        self.ui_helper.clear_highlight()