# services/preset_service.py
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

import mido
import itertools


class PresetService:
    def __init__(self, window):
        self.window = window

    def _get_midi_note_for_part(self, part):
        mapping = {
            "default_kick": 36,
            "default_kick-2": 35,
            "default_kick-3": 34,
            "default_snare": 38,
            "default_snare-2": 37,
            "default_hihat": 42,
            "default_hihat-2": 44,
            "default_clap": 39,
            "default_tom": 41,
            "default_crash": 49,
        }
        return mapping.get(part, 0)

    def _get_part_for_midi_note(self, note):
        mapping = {
            36: "default_kick",
            35: "default_kick-2",
            34: "default_kick-3",
            38: "default_snare",
            37: "default_snare-2",
            42: "default_hihat",
            44: "default_hihat-2",
            39: "default_clap",
            41: "default_tom",
            49: "default_crash",
        }
        return mapping.get(note, None)

    def save_preset(self, file_path, drum_parts, bpm):
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm)))

        # 1. Collect all active notes from all pages into a list
        events = []
        for part, notes in drum_parts.items():
            for beat_index, is_active in notes.items():
                if is_active:
                    note = self._get_midi_note_for_part(part)
                    if note != 0:
                        # Store the note and its absolute beat index
                        events.append({"note": note, "beat": beat_index})

        # 2. Sort events by beat to process them in chronological order
        events.sort(key=lambda e: e["beat"])

        ticks_per_beat = mid.ticks_per_beat
        last_time_in_ticks = 0
        note_duration_ticks = ticks_per_beat // 4  # 16th note duration

        # 3. Group events by beat to handle chords correctly
        for beat, group in itertools.groupby(events, key=lambda e: e["beat"]):
            notes_in_chord = [event["note"] for event in group]

            # Calculate time for this beat/chord
            absolute_time_in_ticks = int(beat * ticks_per_beat / 4)
            delta_time = absolute_time_in_ticks - last_time_in_ticks

            # Add all note_on messages for the chord
            # The first note carries the delta_time, subsequent notes have time=0
            is_first_note = True
            for note in notes_in_chord:
                d_time = delta_time if is_first_note else 0
                track.append(
                    mido.Message("note_on", note=note, velocity=100, time=d_time)
                )
                is_first_note = False

            # Add all note_off messages for the chord
            # The first note_off has the duration, subsequent ones have time=0
            is_first_note = True
            for note in notes_in_chord:
                d_time = note_duration_ticks if is_first_note else 0
                track.append(
                    mido.Message("note_off", note=note, velocity=0, time=d_time)
                )
                is_first_note = False

            # Update the time of the last event
            last_time_in_ticks = absolute_time_in_ticks + note_duration_ticks

        mid.save(file_path)

    def load_preset(self, file_path):
        mid = mido.MidiFile(file_path)
        drum_parts_state = (
            self.window.drum_machine_service.create_empty_drum_parts_state()
        )
        bpm = 120

        ticks_per_beat = mid.ticks_per_beat
        if ticks_per_beat is None:
            ticks_per_beat = 480  # A common default

        for track in mid.tracks:
            absolute_time_in_ticks = 0
            for msg in track:
                # Keep a running total of the absolute time by adding the delta times
                absolute_time_in_ticks += msg.time
                if msg.type == "set_tempo":
                    bpm = mido.tempo2bpm(msg.tempo)
                elif msg.type == "note_on" and msg.velocity > 0:
                    part = self._get_part_for_midi_note(msg.note)
                    if part is not None:
                        # Convert absolute time in ticks back to a beat index
                        # assuming 16th notes
                        ticks_per_16th_note = ticks_per_beat / 4.0
                        beat_index = int(
                            round(absolute_time_in_ticks / ticks_per_16th_note)
                        )
                        drum_parts_state[part][beat_index] = True

        return drum_parts_state, bpm
