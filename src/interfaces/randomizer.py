# interfaces/randomizer.py
#
# Copyright 2025 revisto
#
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class IRandomizationService(ABC):
    @abstractmethod
    def generate_pattern(
        self,
        density_percent: int,
        per_part_density: Optional[Dict[str, int]],
        total_beats: int,
        parts: List[str],
    ) -> Dict[str, Dict[int, bool]]:
        """Create a randomized drum pattern.

        Returns a mapping of part -> {beat_index -> True} for active beats.
        """
        raise NotImplementedError
