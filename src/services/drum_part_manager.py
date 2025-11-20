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

import os
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict
from gettext import gettext as _
from ..models.drum_part import DrumPart
from ..config.constants import DEFAULT_DRUM_PARTS, DRUM_PARTS_CONFIG_FILE

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
    def __init__(self, drumkit_dir: str):
        self.drumkit_dir = drumkit_dir
        self.custom_dir = os.path.join(drumkit_dir, "config")
        self.config_file = os.path.join(self.custom_dir, DRUM_PARTS_CONFIG_FILE)
        self._drum_parts: List[DrumPart] = []
        self._ensure_directories()
        self._load_drum_parts()

    def _ensure_directories(self):
        try:
            os.makedirs(self.custom_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating custom directory {self.custom_dir}: {e}")
            raise

    def _load_drum_parts(self):
        self._drum_parts = []

        # Check if config exists, if so load from it
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for part_data in data.get("drum_parts", []):
                        if "file_path" in part_data:
                            # Check if file exists and log if missing
                            file_exists = os.path.exists(part_data["file_path"])
                            if not file_exists:
                                print(
                                    "Missing file for drum part "
                                    f"'{part_data.get('name', 'Unknown')}': "
                                    f"{part_data['file_path']}"
                                )

                            # Load drum part regardless of file existence
                            drum_part = DrumPart.from_dict(part_data)
                            self._drum_parts.append(drum_part)

                        # Assign MIDI note IDs to parts that don't have them (migration)
                        self._assign_midi_note_ids()
            except Exception as e:
                print(f"Error loading drum parts config: {e}")
                # Fall back to defaults if config is corrupted
                self._load_default_parts()
                self._save_drum_parts()
        else:
            # No config exists, load defaults and save them
            print("No drum parts config found, loading defaults and saving...")
            self._load_default_parts()
            self._save_drum_parts()

    def _load_default_parts(self):
        """Load the default drum parts from the drumkit directory"""
        for name in DEFAULT_DRUM_PARTS:
            file_path = os.path.join(self.drumkit_dir, f"{name}.wav")
            if os.path.exists(file_path):
                midi_note_id = DEFAULT_MIDI_NOTES.get(name)
                drum_part = DrumPart.create_default(name, file_path, midi_note_id)
                self._drum_parts.append(drum_part)

    def _save_drum_parts(self):
        try:
            all_parts = [part.to_dict() for part in self._drum_parts]
            data = {"drum_parts": all_parts}

            # Ensure directory exists before writing
            self._ensure_directories()

            # Write to a temp file first, then rename to avoid corruption
            temp_file = self.config_file + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            os.replace(temp_file, self.config_file)

        except Exception as e:
            print(f"Error saving drum parts: {e}")
            # Clean up temp file if it exists
            temp_file = self.config_file + ".tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

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
        """Add a temporary drum part (for Note X parts from presets)"""
        self._drum_parts.append(drum_part)

    def add_custom_part(self, name: str, source_file: str) -> Optional[DrumPart]:
        """Add a new custom drum part from an audio file"""
        # Validate inputs
        if not name or not source_file:
            print(f"Invalid input: name='{name}', source_file='{source_file}'")
            return None

        if not os.path.exists(source_file):
            print(f"Source file does not exist: {source_file}")
            return None

        try:
            # Create drum part directly with the source file path
            midi_note_id = self._get_next_available_midi_note()
            drum_part = DrumPart.create_custom(name, source_file, midi_note_id)
            self._drum_parts.append(drum_part)

            # Save config
            self._save_drum_parts()

            return drum_part

        except Exception as e:
            print(f"Error adding drum part '{name}': {e}")
            return None

    def remove_part(self, part_id: str) -> bool:
        """Remove a drum part"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        try:
            # Remove from list
            self._drum_parts = [p for p in self._drum_parts if p.id != part_id]

            # Save config
            self._save_drum_parts()

            return True

        except Exception as e:
            print(f"Error removing drum part: {e}")
            return False

    def replace_part(
        self, part_id: str, source_file: str, new_name: str = None
    ) -> Optional[DrumPart]:
        """Update an existing drum part with a new audio file path and name"""
        # Validate inputs
        if not part_id or not source_file:
            print(f"Invalid input: part_id='{part_id}', source_file='{source_file}'")
            return None

        part = self.get_part_by_id(part_id)
        if not part:
            print(f"Drum part not found: {part_id}")
            return None

        try:
            # Extract name from filename if not provided
            if not new_name:
                new_name = (
                    Path(source_file).stem.replace("_", " ").replace("-", " ").title()
                )
                if not new_name.strip():
                    new_name = _("Custom Sound")

            # Update the part
            part.name = new_name
            part.file_path = source_file
            part.is_custom = True  # Mark as custom since it's using external file

            # Save config
            self._save_drum_parts()

            return part

        except Exception as e:
            print(f"Error updating drum part: {e}")
            return None

    def update_part_midi_note(self, part_id: str, midi_note: int) -> bool:
        """Update the MIDI note for a drum part"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        part.midi_note_id = midi_note
        self._save_drum_parts()
        return True

    def is_file_available(self, part_id: str) -> bool:
        """Check if a drum part's file is currently available"""
        part = self.get_part_by_id(part_id)
        if not part:
            return False

        return os.path.exists(part.file_path)

    def reload(self):
        """Public method to reload drum parts from configuration"""
        self._load_drum_parts()

    def _get_next_available_midi_note(self) -> int:
        """Get the next available MIDI note ID for custom parts"""
        used_notes = set()

        # Collect all used MIDI note IDs
        for part in self._drum_parts:
            if part.midi_note_id is not None:
                used_notes.add(part.midi_note_id)

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

    def _assign_midi_note_ids(self):
        """Assign MIDI note IDs to parts that don't have them (migration)"""
        for part in self._drum_parts:
            if part.midi_note_id is None:
                if part.is_custom:
                    # Assign next available note for custom parts
                    part.midi_note_id = self._get_next_available_midi_note()
                else:
                    # Assign default note for default parts
                    part_name = part.id.replace("default_", "")
                    part.midi_note_id = DEFAULT_MIDI_NOTES.get(part_name)
