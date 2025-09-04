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
import base64
import numpy as np
import soundfile as sf
from gi.repository import GLib
from mutagen.mp3 import MP3
from mutagen.id3 import TIT2, TPE1, APIC
from mutagen.flac import FLAC, Picture
from mutagen.oggvorbis import OggVorbis
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
        self,
        drum_parts_state,
        bpm,
        file_path,
        repeat_count=1,
        progress_callback=None,
        metadata=None,
    ):
        """
        Export drum pattern to audio file

        Args:
            drum_parts_state: Current drum pattern state
            bpm: Beats per minute
            file_path: Output file path
            repeat_count: Number of times to repeat the pattern
            progress_callback: Callback function(progress: float) for progress updates
            metadata: Dict with artist, title, and cover_art keys
        """
        try:
            self._validate_pattern(drum_parts_state)
            duration_seconds = self._calculate_duration(
                drum_parts_state, bpm, repeat_count
            )
            output_buffer = self._create_output_buffer(duration_seconds)

            subdivisions_per_second = (bpm / 60) * GROUP_TOGGLE_COUNT
            total_beats = self.parent_window.drum_machine_service.total_beats

            self._render_pattern(
                drum_parts_state,
                output_buffer,
                subdivisions_per_second,
                total_beats,
                repeat_count,
                progress_callback,
            )

            self._normalize_audio(output_buffer)
            self._export_to_file(
                file_path, output_buffer, progress_callback, metadata or {}
            )

            return True

        except Exception as e:
            print(f"Export error: {e}")
            return False

    def _validate_pattern(self, drum_parts_state):
        """Check if pattern has any active beats"""
        has_beats = any(
            any(part_state.values()) for part_state in drum_parts_state.values()
        )
        if not has_beats:
            raise ValueError("No active beats in pattern")

    def _calculate_duration(self, drum_parts_state, bpm, repeat_count):
        """Calculate total export duration including repeats"""
        subdivisions_per_second = (bpm / 60) * GROUP_TOGGLE_COUNT
        total_beats = self.parent_window.drum_machine_service.total_beats
        pattern_duration_seconds = total_beats / subdivisions_per_second

        latest_sample_end_time = self._find_latest_sample_end_time(
            drum_parts_state, subdivisions_per_second
        )

        extra_time_to_add = (
            max(latest_sample_end_time, pattern_duration_seconds)
            - pattern_duration_seconds
        )
        return (pattern_duration_seconds * repeat_count) + extra_time_to_add

    def _find_latest_sample_end_time(self, drum_parts_state, subdivisions_per_second):
        """Find the latest time any sample will finish playing"""
        latest_sample_end_time = 0
        for part in DRUM_PARTS:
            part_state = drum_parts_state[part]
            if part_state:
                last_subdivision = max(
                    sub for sub, active in part_state.items() if active
                )
                trigger_time = last_subdivision / subdivisions_per_second
                sample_length_seconds = (
                    len(self.samples.get(part, [])) / self.sample_rate
                )
                end_time = trigger_time + sample_length_seconds
                latest_sample_end_time = max(latest_sample_end_time, end_time)
        return latest_sample_end_time

    def _create_output_buffer(self, duration_seconds):
        """Create output buffer with calculated duration"""
        total_samples = int(duration_seconds * self.sample_rate)
        return np.zeros(total_samples, dtype="float32")

    def _render_pattern(
        self,
        drum_parts_state,
        output_buffer,
        subdivisions_per_second,
        total_beats,
        repeat_count,
        progress_callback,
    ):
        """Render drum pattern into output buffer"""
        samples_per_subdivision = int(self.sample_rate / subdivisions_per_second)
        pattern_duration_seconds = total_beats / subdivisions_per_second
        total_subdivisions = total_beats * repeat_count

        if progress_callback:
            GLib.idle_add(progress_callback, 0.1)

        for repeat in range(repeat_count):
            repeat_offset = repeat * int(pattern_duration_seconds * self.sample_rate)
            self._render_repeat(
                drum_parts_state,
                output_buffer,
                repeat,
                repeat_offset,
                samples_per_subdivision,
                total_beats,
                total_subdivisions,
                progress_callback,
            )

    def _render_repeat(
        self,
        drum_parts_state,
        output_buffer,
        repeat,
        repeat_offset,
        samples_per_subdivision,
        total_beats,
        total_subdivisions,
        progress_callback,
    ):
        """Render a single repeat of the pattern"""
        for subdivision in range(total_beats):
            self._update_progress(
                repeat, subdivision, total_beats, total_subdivisions, progress_callback
            )

            start_sample = repeat_offset + (subdivision * samples_per_subdivision)
            self._add_subdivision_samples(
                drum_parts_state, output_buffer, subdivision, start_sample
            )

    def _update_progress(
        self, repeat, subdivision, total_beats, total_subdivisions, progress_callback
    ):
        """Update progress callback during rendering"""
        current_subdivision = repeat * total_beats + subdivision
        if progress_callback and current_subdivision:
            progress = 0.1 + (current_subdivision / total_subdivisions) * 0.8
            GLib.idle_add(progress_callback, progress)

    def _add_subdivision_samples(
        self, drum_parts_state, output_buffer, subdivision, start_sample
    ):
        """Add samples for all active drum parts at this subdivision"""
        for part in DRUM_PARTS:
            if drum_parts_state[part].get(subdivision, False):
                sample_data = self.samples.get(part, np.zeros(1000))
                end_sample = min(start_sample + len(sample_data), len(output_buffer))
                output_buffer[start_sample:end_sample] += sample_data[
                    : end_sample - start_sample
                ]

    def _normalize_audio(self, output_buffer):
        """Normalize audio buffer"""
        max_amplitude = np.max(np.abs(output_buffer))
        if max_amplitude > 0:
            output_buffer[:] = output_buffer / max_amplitude * 0.95

    def _export_to_file(self, file_path, output_buffer, progress_callback, metadata):
        """Export buffer to appropriate file format"""
        if progress_callback:
            GLib.idle_add(progress_callback, 0.9)

        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == ".wav":
            self._export_wav(file_path, output_buffer, metadata)
        elif file_ext == ".flac":
            self._export_flac(file_path, output_buffer, metadata)
        elif file_ext == ".ogg":
            self._export_ogg(file_path, output_buffer, metadata)
        elif file_ext == ".mp3":
            self._export_mp3(file_path, output_buffer, metadata)
        else:
            if not file_path.endswith(".wav"):
                file_path += ".wav"
            self._export_wav(file_path, output_buffer, metadata)

        if progress_callback:
            GLib.idle_add(progress_callback, 1.0)

    def _get_image_mime_type(self, image_path):
        """Get MIME type for image based on file extension"""
        image_path_lower = image_path.lower()
        if image_path_lower.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        elif image_path_lower.endswith(".png"):
            return "image/png"
        else:
            return "image/jpeg"

    def _export_wav(self, file_path, audio_data, metadata):
        """Export to WAV format with metadata"""
        try:
            # WAV format doesn't support metadata through soundfile
            # Export WAV
            sf.write(file_path, audio_data, self.sample_rate)

        except Exception as e:
            print(f"WAV export error: {e}")
            # Fallback to basic WAV export
            sf.write(file_path, audio_data, self.sample_rate)

    def _export_flac(self, file_path, audio_data, metadata):
        """Export to FLAC format with metadata"""
        try:
            # Export basic FLAC first
            sf.write(file_path, audio_data, self.sample_rate, format="FLAC")

            # Try to add metadata using mutagen
            if (
                metadata.get("artist")
                or metadata.get("title")
                or metadata.get("cover_art")
            ):
                self._add_flac_metadata(file_path, metadata)

        except Exception as e:
            print(f"FLAC export error: {e}")
            # Fallback to basic FLAC
            try:
                sf.write(file_path, audio_data, self.sample_rate, format="FLAC")
            except Exception:
                # Final fallback to WAV
                sf.write(
                    file_path.replace(".flac", ".wav"), audio_data, self.sample_rate
                )

    def _export_ogg(self, file_path, audio_data, metadata):
        """Export to OGG format with metadata"""
        try:
            # Export basic OGG first
            sf.write(file_path, audio_data, self.sample_rate, format="OGG")

            # Try to add metadata using mutagen
            if (
                metadata.get("artist")
                or metadata.get("title")
                or metadata.get("cover_art")
            ):
                self._add_ogg_metadata(file_path, metadata)

        except Exception as e:
            print(f"OGG export error: {e}")
            # Fallback to basic OGG
            try:
                sf.write(file_path, audio_data, self.sample_rate, format="OGG")
            except Exception:
                # Final fallback to WAV
                sf.write(
                    file_path.replace(".ogg", ".wav"), audio_data, self.sample_rate
                )

    def _export_mp3(self, file_path, audio_data, metadata):
        """Export to MP3 format with metadata"""
        try:
            # Try to use mutagen for MP3 metadata support
            # First export as basic MP3
            sf.write(file_path, audio_data, self.sample_rate, format="MP3")

            # Then add metadata using mutagen
            if (
                metadata.get("artist")
                or metadata.get("title")
                or metadata.get("cover_art")
            ):
                self._add_mp3_metadata(file_path, metadata)

        except Exception as e:
            print(f"MP3 export error: {e}")
            # Fallback to WAV
            sf.write(file_path.replace(".mp3", ".wav"), audio_data, self.sample_rate)

    def _add_mp3_metadata(self, file_path, metadata):
        """Add metadata to MP3 file using mutagen"""
        try:
            audio = MP3(file_path)
            if audio.tags is None:
                audio.add_tags()

            if metadata.get("title"):
                audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
            if metadata.get("artist"):
                audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))

            # Add cover art if provided
            if metadata.get("cover_art") and os.path.exists(metadata["cover_art"]):
                with open(metadata["cover_art"], "rb") as albumart:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime=self._get_image_mime_type(metadata["cover_art"]),
                            type=3,
                            desc="Cover",
                            data=albumart.read(),
                        )
                    )

            audio.save()
        except Exception as e:
            print(f"MP3 metadata error: {e}")

    def _add_flac_metadata(self, file_path, metadata):
        """Add metadata to FLAC file using mutagen"""
        try:
            audio = FLAC(file_path)

            if metadata.get("title"):
                audio["TITLE"] = metadata["title"]
            if metadata.get("artist"):
                audio["ARTIST"] = metadata["artist"]

            # Add cover art if provided
            if metadata.get("cover_art") and os.path.exists(metadata["cover_art"]):
                with open(metadata["cover_art"], "rb") as albumart:
                    picture = Picture()
                    picture.data = albumart.read()
                    picture.type = 3  # Cover (front)
                    picture.mime = self._get_image_mime_type(metadata["cover_art"])
                    picture.desc = "Cover"
                    audio.add_picture(picture)

            audio.save()
        except Exception as e:
            print(f"FLAC metadata error: {e}")

    def _add_ogg_metadata(self, file_path, metadata):
        """Add metadata to OGG file using mutagen"""
        try:
            audio = OggVorbis(file_path)

            if metadata.get("title"):
                audio["TITLE"] = metadata["title"]
            if metadata.get("artist"):
                audio["ARTIST"] = metadata["artist"]

            # Add cover art if provided
            if metadata.get("cover_art") and os.path.exists(metadata["cover_art"]):
                with open(metadata["cover_art"], "rb") as albumart:
                    picture = Picture()
                    picture.data = albumart.read()
                    picture.type = 3  # Cover (front)

                    picture.mime = self._get_image_mime_type(metadata["cover_art"])

                    picture.desc = "Cover"
                    # OGG Vorbis uses base64 encoded METADATA_BLOCK_PICTURE for embedded images
                    audio["METADATA_BLOCK_PICTURE"] = base64.b64encode(picture.write()).decode('ascii')

            audio.save()
        except Exception as e:
            print(f"OGG metadata error: {e}")
