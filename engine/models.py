from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CardInstance:
    mechanic_id: str
    kind: str
    level: int | None = None
    owner: Optional[int] = None
    uid: int = 0


@dataclass(init=False)
class Unit(CardInstance):
    damage: int

    def __init__(
        self,
        mechanic_id: str,
        level: int,
        owner: Optional[int] = None,
        damage: int = 0,
        uid: int = 0,
    ) -> None:
        if level not in {1, 2, 3, 4, 5}:
            raise ValueError(f"invalid unit level: {level}")
        super().__init__(mechanic_id, "unit", level, owner, uid)
        self.damage = damage

    @property
    def alive(self) -> bool:
        assert self.level is not None
        return self.damage < self.level


@dataclass(init=False)
class EffectCard(CardInstance):
    def __init__(
        self,
        mechanic_id: str,
        owner: Optional[int] = None,
        uid: int = 0,
    ) -> None:
        super().__init__(mechanic_id, "effect", None, owner, uid)


@dataclass
class Area:
    area_id: str
    group_id: str
    owner: Optional[int] = None
    units: list[Unit] = field(default_factory=list)
    protected: bool = False
    protection_owner: Optional[int] = None

    def protect_until_owner_turn(self, player: int) -> None:
        self.protected = True
        self.protection_owner = player

    def clear_protection(self) -> None:
        self.protected = False
        self.protection_owner = None


@dataclass(frozen=True)
class AttackResult:
    success: bool
    attacker_survivors: tuple[Unit, ...]
    defender_survivors: tuple[Unit, ...]
    attacker_defeated: tuple[Unit, ...] = ()
    defender_defeated: tuple[Unit, ...] = ()
    attack_order: tuple[str, ...] = ()
    target_order: tuple[str, ...] = ()


@dataclass(frozen=True)
class GameResult:
    winner: int | None
    reason: str
    turns: int
    deck_exhausted: bool
    settlement: bool = False
