# config/export_formats.py
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

from dataclasses import dataclass
from typing import Dict
from gettext import gettext as _


@dataclass
class ExportFormat:
    """Configuration for an audio export format"""

    ext: str
    pattern: str
    name: str
    display: str
    supports_metadata: bool


class ExportFormatRegistry:
    """Registry for managing available export formats"""

    def __init__(self) -> None:
        self._formats = {
            0: ExportFormat(
                ext=".mp3",
                pattern="*.mp3",
                name=_("MP3 files"),
                display=_("MP3"),
                supports_metadata=True,
            ),
            1: ExportFormat(
                ext=".flac",
                pattern="*.flac",
                name=_("FLAC files"),
                display=_("FLAC (Lossless)"),
                supports_metadata=True,
            ),
            2: ExportFormat(
                ext=".ogg",
                pattern="*.ogg",
                name=_("Ogg files"),
                display=_("Ogg Vorbis"),
                supports_metadata=True,
            ),
            3: ExportFormat(
                ext=".wav",
                pattern="*.wav",
                name=_("WAV files"),
                display=_("WAV (Uncompressed)"),
                supports_metadata=False,
            ),
        }

    def get_format(self, format_id: int) -> ExportFormat:
        """Get format configuration by ID"""
        return self._formats.get(format_id, self._formats[0])

    def get_all_formats(self) -> Dict[int, ExportFormat]:
        """Get all available formats"""
        return self._formats.copy()

    def get_format_by_extension(self, extension: str) -> ExportFormat:
        """Get format configuration by file extension"""
        for fmt in self._formats.values():
            if fmt.ext == extension:
                return fmt
        return self._formats[0]
