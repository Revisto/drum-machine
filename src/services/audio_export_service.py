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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import numpy as np
import subprocess

from ..config.constants import DRUM_PARTS
from ..utils.export_progress import ExportPhase
from ..config.export_formats import ExportFormatRegistry
from ..services.audio_renderer import AudioRenderer
from ..services.file_encoder import AudioEncoder


class SampleLoader:
    """Handles loading and caching of drum samples"""

    def __init__(self, drumkit_dir, sample_rate=44100):
        self.drumkit_dir = drumkit_dir
        self.sample_rate = sample_rate
        self.samples = {}
        self._load_samples()

    def _load_samples(self):
        """Load all drum samples into memory"""
        for part in DRUM_PARTS:
            sample_path = os.path.join(self.drumkit_dir, f"{part}.wav")
            if os.path.exists(sample_path):
                try:
                    audio_data = self._load_sample(sample_path)
                    self.samples[part] = audio_data
                except Exception as e:
                    print(f"Warning: Could not load {part}.wav: {e}")
                    self.samples[part] = np.zeros((1000, 2), dtype="float32")

    def _load_sample(self, sample_path):
        """Load a single audio sample using ffmpeg"""
        cmd = [
            "ffmpeg",
            "-i",
            sample_path,
            "-f",
            "f32le",
            "-ac",
            "2",  # Convert to stereo
            "-ar",
            str(self.sample_rate),
            "-",
        ]
        result = subprocess.run(cmd, capture_output=True, check=True)
        audio_data = np.frombuffer(result.stdout, dtype=np.float32)
        return audio_data.reshape(-1, 2)

    def get_samples(self):
        """Get the loaded samples dictionary"""
        return self.samples


class AudioExportService:
    """Handles audio export functionality with progress tracking"""

    def __init__(self, parent_window, drumkit_dir):
        self.parent_window = parent_window
        self.sample_rate = 44100

        # Initialize components
        self.sample_loader = SampleLoader(drumkit_dir, self.sample_rate)
        self.audio_renderer = AudioRenderer(
            self.sample_loader.get_samples(), self.sample_rate
        )
        self.format_registry = ExportFormatRegistry()
        self.audio_encoder = AudioEncoder(self.format_registry)

    def export_audio(
        self,
        drum_parts_state,
        bpm,
        file_path,
        progress_callback,
        repeat_count=1,
        metadata=None,
    ):
        """
        Export drum pattern to audio file

        Args:
            drum_parts_state: Current drum pattern state
            bpm: Beats per minute
            file_path: Output file path
            progress_callback: Callback function for progress updates
            repeat_count: Number of times to repeat the pattern
            metadata: Dict with artist, title, and cover_art keys
        """
        try:
            progress_callback(ExportPhase.PREPARING)
            self._validate_pattern(drum_parts_state)

            progress_callback(ExportPhase.RENDERING)
            total_beats = self.parent_window.drum_machine_service.total_beats
            audio_buffer = self.audio_renderer.render_pattern(
                drum_parts_state, bpm, total_beats, repeat_count
            )

            progress_callback(ExportPhase.SAVING)
            self.audio_encoder.encode_to_file(
                audio_buffer.buffer, self.sample_rate, file_path, metadata
            )

            return True

        except Exception as e:
            print(f"Export error: {e}")
            return False

    def _validate_pattern(self, drum_parts_state):
        """Validate that the pattern has active beats"""
        has_beats = any(
            any(part_state.values()) for part_state in drum_parts_state.values()
        )
        if not has_beats:
            raise ValueError("No active beats in pattern")
