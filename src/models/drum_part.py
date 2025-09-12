# models/drum_part.py
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

import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DrumPart:
    id: str
    name: str
    file_path: str
    is_custom: bool = False

    @classmethod
    def create_default(cls, name: str, file_path: str):
        return cls(
            id=f"default_{name}",
            name=name.replace("-", " ").title(),
            file_path=file_path,
            is_custom=False,
        )

    @classmethod
    def create_custom(cls, name: str, file_path: str):
        return cls(id=str(uuid.uuid4()), name=name, file_path=file_path, is_custom=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "is_custom": self.is_custom,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
