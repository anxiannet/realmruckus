from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Unit:
    mechanic_id: str
    level: int
    owner: Optional[int] = None
    damage: int = 0

    @property
    def alive(self) -> bool:
        return self.damage < self.level


@dataclass
class Area:
    area_id: str
    group_id: str
    owner: Optional[int] = None
    units: list[Unit] = field(default_factory=list)
    protected: bool = False


@dataclass(frozen=True)
class AttackResult:
    success: bool
    attacker_survivors: tuple[Unit, ...]
    defender_survivors: tuple[Unit, ...]
