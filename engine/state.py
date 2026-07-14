from __future__ import annotations

import random
from dataclasses import dataclass, field

from .models import Area


@dataclass
class GameState:
    players: tuple[int, ...]
    center_size: int = 3
    max_units_per_area: int = 3
    rng: random.Random = field(default_factory=random.Random)
    center: list[Area] = field(default_factory=list)
    area_deck: list[Area] = field(default_factory=list)
    controlled: dict[int, list[Area]] = field(default_factory=dict)
    area_returns: int = 0

    def __post_init__(self) -> None:
        for player in self.players:
            self.controlled.setdefault(player, [])

    def refill_center(self) -> None:
        while len(self.center) < self.center_size and self.area_deck:
            area = self.area_deck.pop(0)
            area.owner = None
            area.units.clear()
            area.protected = False
            self.center.append(area)

    def recycle_empty_areas(self) -> None:
        changed = True
        while changed:
            changed = False
            for player in self.players:
                for area in list(self.controlled[player]):
                    if area.units:
                        continue
                    self.controlled[player].remove(area)
                    area.owner = None
                    area.protected = False
                    self.area_deck.append(area)
                    self.rng.shuffle(self.area_deck)
                    self.area_returns += 1
                    changed = True
            self.refill_center()

    def check_winner(self) -> int | None:
        for player in self.players:
            counts: dict[str, int] = {}
            for area in self.controlled[player]:
                counts[area.group_id] = counts.get(area.group_id, 0) + 1
            if any(count >= 3 for count in counts.values()):
                return player
        return None

    def final_score(self, player: int) -> tuple[int, int, int, int]:
        areas = self.controlled[player]
        total_levels = sum(unit.level for area in areas for unit in area.units)
        by_group: dict[str, int] = {}
        for area in areas:
            by_group[area.group_id] = by_group.get(area.group_id, 0) + 1
        max_group = max(by_group.values(), default=0)
        unit_count = sum(len(area.units) for area in areas)
        return len(areas), total_levels, max_group, unit_count
