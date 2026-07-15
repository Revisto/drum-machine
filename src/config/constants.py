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

from typing import List, Set, Tuple
from gettext import gettext as _

# Default drum part names shown in the UI
DEFAULT_DRUM_PARTS: List[str] = [
    _("kick"),
    _("kick-2"),
    _("kick-3"),
    _("snare"),
    _("snare-2"),
    _("hihat"),
    _("hihat-2"),
    _("clap"),
    _("tom"),
    _("crash"),
]

# Default rhythm pattern names shown in the UI
DEFAULT_PATTERNS: List[str] = [
    _("Shoot"),
    _("Maybe Rock"),
    _("Boom Boom"),
    _("Night"),
    _("Slow"),
    _("Chill"),
]

NUM_TOGGLES: int = 16
GROUP_TOGGLE_COUNT: int = 4
DEFAULT_BPM: int = 120
DEFAULT_VOLUME: int = 100

# Audio rendering constants
DEFAULT_FALLBACK_SAMPLE_SIZE: Tuple[int, int] = (1000, 2)

# Progress bar constants
PULSE_INTERVAL_SECONDS: float = 1.0

# Audio constants
MIXER_CHANNELS: int = 32

# Supported audio file formats for input/import
SUPPORTED_INPUT_AUDIO_FORMATS: Set[str] = {".wav", ".mp3", ".ogg", ".flac"}
