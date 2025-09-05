# services/file_encoder.py
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
import subprocess
from ..config.export_formats import ExportFormatRegistry


class AudioEncoder:
    """Handles encoding audio data to various file formats"""

    def __init__(self, format_registry: ExportFormatRegistry):
        self.format_registry = format_registry

    def encode_to_file(self, audio_data, sample_rate, file_path, metadata=None, export_task=None):
        """Encode audio data to the specified file format"""
        file_ext = os.path.splitext(file_path)[1].lower()
        format_info = self.format_registry.get_format_by_extension(file_ext)

        # WAV doesn't support metadata
        if not format_info.supports_metadata:
            metadata = None

        self._encode_with_ffmpeg(audio_data, sample_rate, file_path, metadata, export_task)

    def _encode_with_ffmpeg(self, audio_data, sample_rate, file_path, metadata=None, export_task=None):
        """Use ffmpeg to encode audio data"""
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files
            "-f",
            "f32le",  # Input format: 32-bit float little endian
            "-ar",
            str(sample_rate),  # Sample rate
            "-ac",
            "2",  # Stereo
            "-i",
            "-",  # Read from stdin
        ]

        # Add cover art if provided
        has_cover = self._has_valid_cover_art(metadata)
        if has_cover:
            cmd.extend(["-i", metadata["cover_art"]])

        # Map audio stream
        cmd.extend(["-map", "0:a"])

        # Map cover art if present
        if has_cover:
            cmd.extend(["-map", "1:v", "-disposition:v:0", "attached_pic"])

        # Add metadata tags
        self._add_metadata_to_command(cmd, metadata)

        cmd.append(file_path)

        # Start the subprocess and store reference in export_task
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if export_task:
            export_task.current_process = process
            
        # Check for cancellation before starting
        if export_task and export_task.is_cancelled:
            process.terminate()
            return
            
        try:
            stdout, stderr = process.communicate(input=audio_data.tobytes())
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)
        finally:
            if export_task:
                export_task.current_process = None

    def _has_valid_cover_art(self, metadata):
        """Check if metadata contains valid cover art"""
        return (
            metadata
            and metadata.get("cover_art")
            and os.path.exists(metadata["cover_art"])
        )

    def _add_metadata_to_command(self, cmd, metadata):
        """Add metadata tags to the ffmpeg command"""
        if not metadata:
            return

        if metadata.get("title"):
            cmd.extend(["-metadata", f'title={metadata["title"]}'])
        if metadata.get("artist"):
            cmd.extend(["-metadata", f'artist={metadata["artist"]}'])
