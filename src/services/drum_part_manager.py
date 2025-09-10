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
import shutil
from pathlib import Path
from typing import List, Optional, Dict
from ..models.drum_part import DrumPart
from ..config.constants import DEFAULT_DRUM_PARTS


class DrumPartManager:
    def __init__(self, drumkit_dir: str):
        self.drumkit_dir = drumkit_dir
        self.custom_dir = os.path.join(drumkit_dir, "config")
        self.config_file = os.path.join(self.custom_dir, "drum_parts.json")
        self._drum_parts: List[DrumPart] = []
        self._ensure_directories()
        self._load_drum_parts()
    
    def _ensure_directories(self):
        os.makedirs(self.custom_dir, exist_ok=True)
    
    def _load_drum_parts(self):
        self._drum_parts = []
        
        # Load default drum parts
        for name in DEFAULT_DRUM_PARTS:
            file_path = os.path.join(self.drumkit_dir, f"{name}.wav")
            if os.path.exists(file_path):
                drum_part = DrumPart.create_default(name, file_path)
                self._drum_parts.append(drum_part)
        
        # Load custom drum parts from config
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    custom_data = json.load(f)
                    for data in custom_data.get('custom_parts', []):
                        if os.path.exists(data['file_path']):
                            drum_part = DrumPart.from_dict(data)
                            self._drum_parts.append(drum_part)
            except Exception as e:
                print(f"Error loading custom drum parts: {e}")
    
    def _save_custom_parts(self):
        custom_parts = [part.to_dict() for part in self._drum_parts if part.is_custom]
        data = {'custom_parts': custom_parts}
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving custom drum parts: {e}")
    
    def get_all_parts(self) -> List[DrumPart]:
        return self._drum_parts.copy()
    
    def get_part_by_id(self, part_id: str) -> Optional[DrumPart]:
        for part in self._drum_parts:
            if part.id == part_id:
                return part
        return None
    
    def get_parts_dict(self) -> Dict[str, DrumPart]:
        return {part.id: part for part in self._drum_parts}
    
    def add_custom_part(self, name: str, source_file: str) -> Optional[DrumPart]:
        try:
            # Generate unique filename
            file_ext = Path(source_file).suffix
            filename = f"{name.lower().replace(' ', '_')}{file_ext}"
            counter = 1
            base_filename = filename
            
            while os.path.exists(os.path.join(self.custom_dir, filename)):
                filename = f"{Path(base_filename).stem}_{counter}{file_ext}"
                counter += 1
            
            dest_path = os.path.join(self.custom_dir, filename)
            
            # Copy file to custom directory
            shutil.copy2(source_file, dest_path)
            
            # Create drum part
            drum_part = DrumPart.create_custom(name, dest_path)
            self._drum_parts.append(drum_part)
            
            # Save config
            self._save_custom_parts()
            
            return drum_part
            
        except Exception as e:
            print(f"Error adding custom drum part: {e}")
            return None
    
    def remove_custom_part(self, part_id: str) -> bool:
        part = self.get_part_by_id(part_id)
        if not part or not part.is_custom:
            return False
        
        try:
            # Remove file if it exists
            if os.path.exists(part.file_path):
                os.remove(part.file_path)
            
            # Remove from list
            self._drum_parts = [p for p in self._drum_parts if p.id != part_id]
            
            # Save config
            self._save_custom_parts()
            
            return True
            
        except Exception as e:
            print(f"Error removing custom drum part: {e}")
            return False
    
    def replace_part(self, part_id: str, source_file: str) -> Optional[DrumPart]:
        part = self.get_part_by_id(part_id)
        if not part:
            return None
        
        try:
            if part.is_custom:
                # For custom parts, replace the file
                shutil.copy2(source_file, part.file_path)
            else:
                # For default parts, create a custom replacement
                name = f"{part.name} (Custom)"
                return self.add_custom_part(name, source_file)
            
            return part
            
        except Exception as e:
            print(f"Error replacing drum part: {e}")
            return None
