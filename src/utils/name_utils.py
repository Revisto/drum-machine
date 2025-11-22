# utils/name_utils.py
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

from pathlib import Path
from gettext import gettext as _


def extract_name_from_path(file_path):
    """Extract display name from file path
    
    Args:
        file_path: Path to the file (str or Path object)
        
    Returns:
        str: Display name extracted from filename, or "Custom Sound" if empty
    """
    path = Path(file_path)
    name = path.stem.replace("_", " ").replace("-", " ").title()
    return name if name.strip() else _("Custom Sound")

