# services/drum_part_manager.py
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

import logging
import os
import uuid
from typing import List, Optional, Dict
from ..models.drum_part import DrumPart
from ..config.constants import DEFAULT_DRUM_PARTS

# Default MIDI note mapping for default drum parts
DEFAULT_MIDI_NOTES = {
    "kick": 36,
    "kick-2": 35,
    "kick-3": 34,
    "snare": 38,
    "snare-2": 37,
    "hihat": 42,
    "hihat-2": 44,
    "clap": 39,
    "tom": 41,
    "crash": 49,
}


class DrumPartManager:
    def __init__(self, user_data_dir: str, bundled_sounds_dir: str = None):
        # User-writable directory for custom sounds
        self.user_data_dir = user_data_dir
        # Read-only directory with bundled default sounds (e.g., in snap)
        self.bundled_sounds_dir = bundled_sounds_dir or user_data_dir
        self._drum_parts: List[DrumPart] = []
        self._load_default_parts()

    def _load_default_parts(self):
        """Load the default drum parts from the bundled sounds directory"""
        for name in DEFAULT_DRUM_PARTS:
            file_path = os.path.join(self.bundled_sounds_dir, f"{name}.wav")
            if os.path.exists(file_path):
                midi_note_id = DEFAULT_MIDI_NOTES.get(name)
                drum_part = DrumPart.create_default(name, file_path, midi_note_id)
                self._drum_parts.append(drum_part)

    def get_all_parts(self) -> List[DrumPart]:
        return self._drum_parts.copy()

    def get_part_by_id(self, part_id: str) -> Optional[DrumPart]:
        for part in self._drum_parts:
            if part.id == part_id:
                return part
        return None

    def get_parts_dict(self) -> Dict[str, DrumPart]:
        return {part.id: part for part in self._drum_parts}

    def get_part_by_midi_note(self, midi_note: int) -> Optional[DrumPart]:
        """Get a drum part by its MIDI note ID"""
        for part in self._drum_parts:
            if part.midi_note_id == midi_note:
                return part
        return None

    def get_or_create_part_for_midi_note(self, midi_note: int) -> DrumPart:
        """Get an existing drum part for a MIDI note, or create a temporary one
        if it doesn't exist"""
        part = self.get_part_by_midi_note(midi_note)
        if part:
            return part

        # Create a temporary part for unknown MIDI note
        temp_part = DrumPart(
            id=str(uuid.uuid4()),
            name=f"Note {midi_note}",
            file_path="",
            is_custom=True,
            midi_note_id=midi_note,
        )
        self._drum_parts.append(temp_part)
        return temp_part

    def add_temporary_part(self, drum_part: DrumPart):
        """Add a temporary drum part (for Note X parts from patterns)"""
        self._drum_parts.append(drum_part)

    def add_custom_part(self, name: str, source_file: str) -> Optional[DrumPart]:
        """Add a new custom drum part from an audio file"""
        # Validate inputs
        if not name or not source_file:
            logging.error(f"Invalid input: name='{name}', source_file='{source_file}'")
            return None

        if not os.path.exists(source_file):
            logging.error(f"Source file does not exist: {source_file}")
            return None

        # Create drum part directly with the source file path
        midi_note_id = self._get_next_available_midi_note()
        drum_part = DrumPart.create_custom(name, source_file, midi_note_id)
        self._drum_parts.append(drum_part)
        return drum_part

    def remove_part(self, part_id: str) -> bool:
        """Remove a drum part"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        self._drum_parts = [p for p in self._drum_parts if p.id != part_id]
        return True

    def reorder_part(self, part_id: str, new_index: int) -> bool:
        """Move a drum part to a new position in the list.

        Args:
            part_id: The ID of the drum part to move
            new_index: The target index (0 to len-1)

        Returns:
            True if reorder was successful, False otherwise
        """
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        if new_index < 0 or new_index >= len(self._drum_parts):
            logging.warning(f"Invalid reorder index: {new_index}")
            return False

        current_index = self._drum_parts.index(part)
        if current_index == new_index:
            return True

        self._drum_parts.remove(part)
        self._drum_parts.insert(new_index, part)
        return True

    def get_part_index(self, part_id: str) -> int:
        """Get the index of a drum part in the list"""
        for i, part in enumerate(self._drum_parts):
            if part.id == part_id:
                return i
        return -1

    def replace_part(
        self, part_id: str, source_file: str, new_name: str
    ) -> Optional[DrumPart]:
        """Update an existing drum part with a new audio file path and name"""
        # Validate inputs
        if not part_id or not source_file:
            logging.error(
                f"Invalid input: part_id='{part_id}', source_file='{source_file}'"
            )
            return None

        part = self.get_part_by_id(part_id)
        if not part:
            logging.error(f"Drum part not found: {part_id}")
            return None

        part.name = new_name
        part.file_path = source_file
        part.is_custom = True
        return part

    def update_part_midi_note(self, part_id: str, midi_note: int) -> bool:
        """Update the MIDI note for a drum part"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        part.midi_note_id = midi_note
        return True

    def is_file_available(self, part_id: str) -> bool:
        """Check if a drum part's file is currently available"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        return os.path.exists(part.file_path)

    def reset_to_defaults(self):
        """Reset drum parts to defaults, removing all custom samples"""
        self._drum_parts = []
        self._load_default_parts()

    def _collect_used_notes(self) -> set:
        """Collect all currently used MIDI notes"""
        return {
            part.midi_note_id
            for part in self._drum_parts
            if part.midi_note_id is not None
        }

    def _get_next_available_midi_note(self) -> int:
        """
        Get the next available MIDI note ID for custom parts based on current state
        """
        used_notes = self._collect_used_notes()
        return self._compute_next_midi_note(used_notes)

    def _compute_next_midi_note(self, used_notes: set) -> Optional[int]:
        """Compute the next available MIDI note given a set of used notes"""
        # Start from 35 (GM percussion range start) for better compatibility
        # GM percussion standard is 35-81, but we check up to 127 for flexibility
        for note in range(35, 128):
            if note not in used_notes:
                return note

        # If we run out of standard percussion notes, check lower range (0-34)
        for note in range(0, 35):
            if note not in used_notes:
                return note

        return None
