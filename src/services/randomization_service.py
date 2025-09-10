# services/randomization_service.py
#
# Copyright 2025 revisto
#
# SPDX-License-Identifier: GPL-3.0-or-later

import random
from typing import Dict, List, Optional

from ..interfaces.randomizer import IRandomizationService


class RandomizationService(IRandomizationService):
    """Generates randomized drum patterns based on density percentages."""

    def generate_pattern(
        self,
        density_percent: int,
        per_part_density: Optional[Dict[str, int]],
        total_beats: int,
        parts: List[str],
    ) -> Dict[str, Dict[int, bool]]:
        density_percent = max(0, min(100, int(density_percent)))
        per_part_density = per_part_density or {}

        pattern: Dict[str, Dict[int, bool]] = {part: {} for part in parts}

        for part in parts:
            part_density = per_part_density.get(part, density_percent)
            part_density = max(0, min(100, int(part_density)))
            probability = part_density / 100.0
            for beat_index in range(total_beats):
                if random.random() < probability:
                    pattern[part][beat_index] = True

        return pattern
