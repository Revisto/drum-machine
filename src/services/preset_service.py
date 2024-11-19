# services/preset_service.py
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

import mido
from ..config import DRUM_PARTS, NUM_TOGGLES


class PresetService:
    def _get_midi_note_for_part(self, part):
        mapping = {
            "kick": 36,
            "kick-2": 35,
            "kick-3": 34,
            "snare": 38,
            "snare-2": 37,
            "hihat": 42,
            "hihat-2": 44,
            "clap": 39,
            "tom": 41,
            "crash": 49,
        }
        return mapping.get(part, 0)

    def _get_part_for_midi_note(self, note):
        mapping = {
            36: "kick",
            35: "kick-2",
            34: "kick-3",
            38: "snare",
            37: "snare-2",
            42: "hihat",
            44: "hihat-2",
            39: "clap",
            41: "tom",
            49: "crash",
        }
        return mapping.get(note, None)

    def save_preset(self, file_path, drum_parts, bpm):
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

        for i in range(NUM_TOGGLES):
            for part, notes in drum_parts.items():
                if notes[i]:
                    note = self._get_midi_note_for_part(part)
                    track.append(
                        mido.Message("note_on", note=note, velocity=64, time=i)
                    )
                    track.append(
                        mido.Message("note_off", note=note, velocity=64, time=0)
                    )

        mid.save(file_path)

    def load_preset(self, file_path):
        mid = mido.MidiFile(file_path)
        drum_parts = {part: [False] * NUM_TOGGLES for part in DRUM_PARTS}
        bpm = 120

        for track in mid.tracks:
            for msg in track:
                if msg.type == "set_tempo":
                    bpm = mido.tempo2bpm(msg.tempo)
                elif msg.type == "note_on":
                    part = self._get_part_for_midi_note(msg.note)
                    if part is not None:
                        drum_parts[part][msg.time] = True

        return drum_parts, bpm
