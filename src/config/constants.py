# config/constants.py
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

from typing import List, Set

DEFAULT_DRUM_PARTS: List[str] = [
    "kick",
    "kick-2",
    "kick-3",
    "snare",
    "snare-2",
    "hihat",
    "hihat-2",
    "clap",
    "tom",
    "crash",
]
DEFAULT_PATTERNS: List[str] = [
    "Shoot",
    "Maybe Rock",
    "Boom Boom",
    "Night",
    "Slow",
    "Chill",
]
NUM_TOGGLES: int = 16
GROUP_TOGGLE_COUNT: int = 4

# Audio rendering constants
DEFAULT_FALLBACK_SAMPLE_SIZE: tuple = (1000, 2)

# Progress bar constants
PULSE_INTERVAL_SECONDS: float = 1.0

# Audio constants
MIXER_CHANNELS: int = 32

# DrumPartManager constants
DRUM_PARTS_CONFIG_FILE: str = "drum_parts.json"

# Supported audio file formats for input/import
SUPPORTED_INPUT_AUDIO_FORMATS: Set[str] = {".wav", ".mp3", ".ogg", ".flac"}
