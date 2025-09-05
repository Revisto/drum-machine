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
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from ..interfaces.sound import ISoundService
from ..config.constants import DRUM_PARTS


class SoundService(ISoundService):
    def __init__(self, drumkit_dir):
        self.drumkit_dir = drumkit_dir
        # Map of drum part -> list[Gtk.MediaFile]
        self.sounds = {}
        # Round-robin index for each drum part to allow overlapping playback
        self._next_instance_index = {}
        # Number of concurrent players per sound to allow overlaps
        self._instances_per_sound = 4
        # Volume stored as 0.0 - 1.0
        self.volume = 1.0

    def load_sounds(self):
        """Preload media players for each drum part using GtkMediaStream."""
        loaded_sounds = {}
        indices = {}

        for drum_part in DRUM_PARTS:
            file_path = os.path.join(self.drumkit_dir, f"{drum_part}.wav")
            # Create a small pool so the same sound can overlap itself
            pool = []
            for _ in range(self._instances_per_sound):
                media = Gtk.MediaFile.new_for_filename(file_path)
                # Ensure current volume is applied
                try:
                    media.set_volume(self.volume)
                except Exception:
                    pass
                pool.append(media)
            loaded_sounds[drum_part] = pool
            indices[drum_part] = 0

        self.sounds = loaded_sounds
        self._next_instance_index = indices

    def _play_sound_on_main(self, sound_name):
        pool = self.sounds.get(sound_name)
        if not pool:
            return False

        idx = self._next_instance_index.get(sound_name, 0)
        media = pool[idx]
        # Advance round-robin index
        self._next_instance_index[sound_name] = (idx + 1) % len(pool)

        try:
            # Restart from beginning if supported
            if hasattr(media, "seek"):
                media.seek(0)
        except Exception:
            pass

        try:
            media.play()
        except Exception:
            pass

        # Returning False removes this idle source
        return False

    def play_sound(self, sound_name):
        # Schedule playback on the GTK main loop for thread-safety
        GLib.idle_add(self._play_sound_on_main, sound_name)

    def _set_volume_on_main(self):
        for pool in self.sounds.values():
            for media in pool:
                try:
                    media.set_volume(self.volume)
                except Exception:
                    pass
        return False

    def set_volume(self, volume):
        # Convert 0-100 UI value to 0.0-1.0
        self.volume = max(0.0, min(1.0, float(volume) / 100.0))
        # Apply on main loop to avoid threading issues
        GLib.idle_add(self._set_volume_on_main)

    def preview_sound(self, sound_name):
        if sound_name in self.sounds:
            self.play_sound(sound_name)
