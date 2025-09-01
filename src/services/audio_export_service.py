# services/audio_export_service.py
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
# MERCHANTABILITY or FITNESS FOR ANY PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import numpy as np
import soundfile as sf
from gi.repository import GLib
from ..config import DRUM_PARTS, GROUP_TOGGLE_COUNT


class AudioExportService:
    """Handles audio export functionality with progress tracking"""

    def __init__(self, parent_window, drumkit_dir):
        self.parent_window = parent_window
        self.drumkit_dir = drumkit_dir
        self.sample_rate = 44100
        self.samples = {}
        self._load_samples()

    def _load_samples(self):
        """Load all drum samples into memory"""
        for part in DRUM_PARTS:
            sample_path = os.path.join(self.drumkit_dir, f"{part}.wav")
            if os.path.exists(sample_path):
                try:
                    audio_data, _ = sf.read(sample_path, dtype="float32")
                    # Convert to mono if needed
                    if audio_data.ndim > 1:
                        audio_data = audio_data[:, 0]
                    self.samples[part] = audio_data
                except Exception as e:
                    print(f"Warning: Could not load {part}.wav: {e}")
                    self.samples[part] = np.zeros(1000, dtype="float32")

    def export_audio(
        self, drum_parts_state, bpm, file_path, repeat_count=1, progress_callback=None
    ):
        """
        Export drum pattern to audio file

        Args:
            drum_parts_state: Current drum pattern state
            bpm: Beats per minute
            file_path: Output file path
            repeat_count: Number of times to repeat the pattern
            progress_callback: Callback function(progress: float) for progress updates
        """
        try:
            # Check if pattern has any active beats
            has_beats = any(
                any(part_state.values()) for part_state in drum_parts_state.values()
            )
            if not has_beats:
                raise ValueError("No active beats in pattern")

            # Calculate export duration including repeats
            subdivisions_per_second = (bpm / 60) * GROUP_TOGGLE_COUNT
            total_beats = self.parent_window.drum_machine_service.total_beats

            # Calculate minimum pattern duration
            pattern_duration_seconds = total_beats / subdivisions_per_second

            # Find the latest time any sample will finish playing
            latest_sample_end_time = 0
            for part in DRUM_PARTS:
                part_state = drum_parts_state[part]
                if part_state:
                    # Find last subdivision where this instrument is played
                    last_subdivision = max(
                        sub for sub, active in part_state.items() if active
                    )
                    # Calculate when this sample would finish
                    trigger_time = last_subdivision / subdivisions_per_second
                    sample_length_seconds = (
                        len(self.samples.get(part, [])) / self.sample_rate
                    )
                    end_time = trigger_time + sample_length_seconds
                    latest_sample_end_time = max(latest_sample_end_time, end_time)

            # Use the longer of pattern duration or latest sample end time,
            # then multiply by repeats
            extra_time_to_add = (
                max(latest_sample_end_time, pattern_duration_seconds)
                - pattern_duration_seconds
            )
            duration_seconds = (
                pattern_duration_seconds * repeat_count
            ) + extra_time_to_add

            # Create output buffer
            total_samples = int(duration_seconds * self.sample_rate)
            output_buffer = np.zeros(total_samples, dtype="float32")

            # Calculate samples per subdivision (16th note)
            samples_per_subdivision = int(self.sample_rate / subdivisions_per_second)

            if progress_callback:
                GLib.idle_add(progress_callback, 0.1)

            # Render pattern for each repeat
            total_subdivisions = total_beats * repeat_count
            for repeat in range(repeat_count):
                repeat_offset = repeat * int(
                    pattern_duration_seconds * self.sample_rate
                )

                for subdivision in range(total_beats):
                    # Update progress every 10% of total subdivisions
                    current_subdivision = repeat * total_beats + subdivision
                    if progress_callback and current_subdivision:
                        progress = (
                            0.1 + (current_subdivision / total_subdivisions) * 0.8
                        )
                        GLib.idle_add(progress_callback, progress)

                    start_sample = repeat_offset + (
                        subdivision * samples_per_subdivision
                    )

                    # Add samples for each active drum part
                    for part in DRUM_PARTS:
                        if drum_parts_state[part].get(subdivision, False):
                            sample_data = self.samples.get(part, np.zeros(1000))
                            end_sample = min(
                                start_sample + len(sample_data), len(output_buffer)
                            )
                            output_buffer[start_sample:end_sample] += sample_data[
                                : end_sample - start_sample
                            ]

            if progress_callback:
                GLib.idle_add(progress_callback, 0.9)

            # Normalize audio
            max_amplitude = np.max(np.abs(output_buffer))
            if max_amplitude > 0:
                output_buffer = output_buffer / max_amplitude * 0.95  # Leave headroom

            # Determine file format and export
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext == ".wav":
                sf.write(file_path, output_buffer, self.sample_rate)
            elif file_ext == ".flac":
                self._export_flac(file_path, output_buffer)
            elif file_ext == ".ogg":
                self._export_ogg(file_path, output_buffer)
            elif file_ext == ".mp3":
                self._export_mp3(file_path, output_buffer)
            else:
                # Default to WAV
                if not file_path.endswith(".wav"):
                    file_path += ".wav"
                sf.write(file_path, output_buffer, self.sample_rate)

            # Final progress update
            if progress_callback:
                GLib.idle_add(progress_callback, 1.0)

            return True

        except Exception as e:
            print(f"Export error: {e}")
            return False

    def _export_flac(self, file_path, audio_data):
        """Export to FLAC format"""
        try:
            # FLAC is supported by soundfile
            sf.write(file_path, audio_data, self.sample_rate, format="FLAC")
        except Exception as e:
            print(f"FLAC export error: {e}")
            # Fallback to WAV
            sf.write(file_path.replace(".flac", ".wav"), audio_data, self.sample_rate)

    def _export_ogg(self, file_path, audio_data):
        """Export to OGG format"""
        try:
            # OGG is supported by soundfile
            sf.write(file_path, audio_data, self.sample_rate, format="OGG")
        except Exception as e:
            print(f"OGG export error: {e}")
            # Fallback to WAV
            sf.write(file_path.replace(".ogg", ".wav"), audio_data, self.sample_rate)

    def _export_mp3(self, file_path, audio_data):
        """Export to MP3 format"""
        try:
            # Try to use soundfile with MP3 support
            sf.write(file_path, audio_data, self.sample_rate, format="MP3")
        except Exception as e:
            print(f"MP3 export error: {e}")
            # Fallback to WAV
            sf.write(file_path.replace(".mp3", ".wav"), audio_data, self.sample_rate)
