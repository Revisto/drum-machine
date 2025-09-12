# services/audio_renderer.py
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

import numpy as np
from ..config.constants import (
    GROUP_TOGGLE_COUNT,
    DEFAULT_FALLBACK_SAMPLE_SIZE,
)


class AudioBuffer:
    """Manages audio buffer operations"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.buffer = None

    def create_buffer(self, duration_seconds: float):
        """Create output buffer with calculated duration"""
        total_samples = int(duration_seconds * self.sample_rate)
        self.buffer = np.zeros((total_samples, 2), dtype="float32")
        return self.buffer

    def add_sample(self, sample_data: np.ndarray, start_sample: int):
        """Add a sample to the buffer at the specified position"""
        if self.buffer is None:
            return

        end_sample = min(start_sample + len(sample_data), len(self.buffer))
        self.buffer[start_sample:end_sample] += sample_data[: end_sample - start_sample]

    def normalize(self):
        """Normalize the audio buffer"""
        if self.buffer is None:
            return

        max_amplitude = np.max(np.abs(self.buffer))
        if max_amplitude > 0:
            self.buffer[:] = self.buffer / max_amplitude * 0.95


class AudioRenderer:
    """Handles audio rendering operations"""

    def __init__(self, samples, sample_rate: int = 44100):
        self.samples = samples
        self.sample_rate = sample_rate

    def calculate_pattern_duration(
        self, drum_parts_state, bpm: int, repeat_count: int, total_beats: int
    ) -> float:
        """Calculate total export duration including repeats"""
        subdivisions_per_second = (bpm / 60) * GROUP_TOGGLE_COUNT
        pattern_duration_seconds = total_beats / subdivisions_per_second

        latest_sample_end_time = self._find_latest_sample_end_time(
            drum_parts_state, subdivisions_per_second
        )

        extra_time_to_add = (
            max(latest_sample_end_time, pattern_duration_seconds)
            - pattern_duration_seconds
        )
        return (pattern_duration_seconds * repeat_count) + extra_time_to_add

    def render_pattern(
        self, drum_parts_state, bpm: int, total_beats: int, repeat_count: int
    ) -> AudioBuffer:
        """Render drum pattern into an audio buffer"""
        duration = self.calculate_pattern_duration(
            drum_parts_state, bpm, repeat_count, total_beats
        )

        audio_buffer = AudioBuffer(self.sample_rate)
        audio_buffer.create_buffer(duration)

        subdivisions_per_second = (bpm / 60) * GROUP_TOGGLE_COUNT
        samples_per_subdivision = int(self.sample_rate / subdivisions_per_second)
        pattern_duration_seconds = total_beats / subdivisions_per_second

        for repeat in range(repeat_count):
            repeat_offset = repeat * int(pattern_duration_seconds * self.sample_rate)
            self._render_repeat(
                drum_parts_state,
                audio_buffer,
                repeat_offset,
                samples_per_subdivision,
                total_beats,
            )

        audio_buffer.normalize()
        return audio_buffer

    def _find_latest_sample_end_time(
        self, drum_parts_state, subdivisions_per_second: float
    ) -> float:
        """Find the latest time any sample will finish playing"""
        latest_sample_end_time = 0

        for part_id, part_state in drum_parts_state.items():
            if not part_state:
                continue

            active_subdivisions = [sub for sub, active in part_state.items() if active]
            if not active_subdivisions:
                continue

            last_subdivision = max(active_subdivisions)
            trigger_time = last_subdivision / subdivisions_per_second
            sample_length_seconds = (
                len(self.samples.get(part_id, [])) / self.sample_rate
            )
            end_time = trigger_time + sample_length_seconds
            latest_sample_end_time = max(latest_sample_end_time, end_time)

        return latest_sample_end_time

    def _render_repeat(
        self,
        drum_parts_state,
        audio_buffer: AudioBuffer,
        repeat_offset: int,
        samples_per_subdivision: int,
        total_beats: int,
    ):
        """Render a single repeat of the pattern"""
        for subdivision in range(total_beats):
            start_sample = repeat_offset + (subdivision * samples_per_subdivision)
            self._add_subdivision_samples(
                drum_parts_state, audio_buffer, subdivision, start_sample
            )

    def _add_subdivision_samples(
        self,
        drum_parts_state,
        audio_buffer: AudioBuffer,
        subdivision: int,
        start_sample: int,
    ):
        """Add samples for all active drum parts at this subdivision"""
        for part_id, part_state in drum_parts_state.items():
            if part_state.get(subdivision, False):
                sample_data = self.samples.get(
                    part_id, np.zeros(DEFAULT_FALLBACK_SAMPLE_SIZE)
                )
                audio_buffer.add_sample(sample_data, start_sample)
