from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CardDefinition:
    mechanic_id: str
    kind: str
    level: int | None
    copies: int
    effect_id: str
    timing: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class DeckDefinition:
    deck_id: str
    deck_version: str
    rules_version: str
    cards: tuple[CardDefinition, ...]
    areas: tuple[dict[str, str], ...] = ()

    @property
    def card_count(self) -> int:
        return sum(card.copies for card in self.cards)


def load_deck(path: str | Path) -> DeckDefinition:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cards = tuple(CardDefinition(**card) for card in payload["cards"])
    deck = DeckDefinition(
        deck_id=payload["deck_id"],
        deck_version=payload["deck_version"],
        rules_version=payload["rules_version"],
        cards=cards,
        areas=tuple(payload.get("areas", ())),
    )
    validate_deck(deck)
    return deck


def validate_deck(deck: DeckDefinition) -> None:
    ids: set[str] = set()
    for card in deck.cards:
        if card.mechanic_id in ids:
            raise ValueError(f"duplicate mechanic_id: {card.mechanic_id}")
        ids.add(card.mechanic_id)
        if card.kind not in {"unit", "effect"}:
            raise ValueError(f"invalid kind: {card.kind}")
        if card.kind == "unit" and card.level not in {1, 2, 3, 4, 5}:
            raise ValueError(f"invalid unit level: {card.mechanic_id}")
        if card.kind == "effect" and card.level is not None:
            raise ValueError(f"effect card has level: {card.mechanic_id}")
        if card.copies < 1:
            raise ValueError(f"invalid copies: {card.mechanic_id}")

    if deck.deck_id == "core":
        if deck.card_count != 40:
            raise ValueError(f"core deck must contain 40 cards, got {deck.card_count}")
        if len(deck.areas) != 12:
            raise ValueError(f"core area deck must contain 12 areas, got {len(deck.areas)}")
        groups: dict[str, int] = {}
        for area in deck.areas:
            groups[area["group_id"]] = groups.get(area["group_id"], 0) + 1
        if sorted(groups.values()) != [3, 3, 3, 3]:
            raise ValueError(f"area groups must be 4 groups of 3: {groups}")


def combine_decks(*decks: DeckDefinition) -> tuple[CardDefinition, ...]:
    return tuple(card for deck in decks for card in deck.cards)
