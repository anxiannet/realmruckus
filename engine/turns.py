from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TurnPhase(str, Enum):
    START = "start"
    DRAW = "draw"
    CHOOSE_ACTION = "choose_action"
    RESOLVE_ACTION = "resolve_action"
    FORCED_EFFECTS = "forced_effects"
    RECYCLE_AREAS = "recycle_areas"
    CHECK_WIN = "check_win"
    HAND_LIMIT = "hand_limit"
    CHECK_DECK_END = "check_deck_end"
    END = "end"


_PHASE_ORDER = (
    TurnPhase.START,
    TurnPhase.DRAW,
    TurnPhase.CHOOSE_ACTION,
    TurnPhase.RESOLVE_ACTION,
    TurnPhase.FORCED_EFFECTS,
    TurnPhase.RECYCLE_AREAS,
    TurnPhase.CHECK_WIN,
    TurnPhase.HAND_LIMIT,
    TurnPhase.CHECK_DECK_END,
    TurnPhase.END,
)


@dataclass
class TurnState:
    player: int
    phase: TurnPhase = TurnPhase.START
    action_used: bool = False
    public_card_played: bool = False
    control_changed: bool = False
    log: list[str] = field(default_factory=list)

    def advance(self) -> TurnPhase:
        index = _PHASE_ORDER.index(self.phase)
        if self.phase == TurnPhase.END:
            raise RuntimeError("turn is already complete")
        self.phase = _PHASE_ORDER[index + 1]
        return self.phase

    def mark_action_used(self) -> None:
        if self.action_used:
            raise RuntimeError("main action already used")
        self.action_used = True

    @property
    def complete(self) -> bool:
        return self.phase == TurnPhase.END


def phase_order() -> tuple[TurnPhase, ...]:
    return _PHASE_ORDER
