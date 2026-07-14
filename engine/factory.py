from __future__ import annotations

from collections.abc import Iterable

from .data import CardDefinition, DeckDefinition
from .models import CardInstance, EffectCard, Unit


def create_card_instances(
    definitions: Iterable[CardDefinition],
    *,
    uid_start: int = 0,
) -> list[CardInstance]:
    cards: list[CardInstance] = []
    uid = uid_start
    for definition in definitions:
        for _ in range(definition.copies):
            if definition.kind == "unit":
                assert definition.level is not None
                card: CardInstance = Unit(
                    mechanic_id=definition.mechanic_id,
                    level=definition.level,
                    uid=uid,
                )
            elif definition.kind == "effect":
                card = EffectCard(
                    mechanic_id=definition.mechanic_id,
                    uid=uid,
                )
            else:
                raise ValueError(f"unsupported card kind: {definition.kind}")
            cards.append(card)
            uid += 1
    return cards


def create_deck_instances(
    deck: DeckDefinition,
    *,
    uid_start: int = 0,
) -> list[CardInstance]:
    return create_card_instances(deck.cards, uid_start=uid_start)
