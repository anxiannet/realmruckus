from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .data import CardDefinition
from .models import Area, Unit
from .state import GameState


@dataclass
class EffectContext:
    state: GameState
    hands: dict[int, list[Unit]]
    deck: list[Unit]
    discard: list[Unit]
    actor: int
    selected_player: int | None = None
    selected_area: Area | None = None
    selected_units: list[Unit] = field(default_factory=list)
    selected_hand_cards: list[Unit] = field(default_factory=list)
    social_response: bool = False
    cancelled: bool = False

    def draw(self, player: int, count: int) -> int:
        drawn = 0
        for _ in range(count):
            if not self.deck:
                break
            card = self.deck.pop(0)
            card.owner = player
            self.hands[player].append(card)
            drawn += 1
        return drawn

    def find_area(self, unit: Unit) -> Area | None:
        for areas in self.state.controlled.values():
            for area in areas:
                if unit in area.units:
                    return area
        return None

    def remove_unit(self, unit: Unit, *, to_hand: bool, new_owner: int | None = None) -> None:
        area = self.find_area(unit)
        if area is None:
            raise ValueError("selected unit is not in play")
        area.units.remove(unit)
        if new_owner is not None:
            unit.owner = new_owner
        if to_hand:
            if unit.owner is None:
                raise ValueError("unit has no owner")
            self.hands[unit.owner].append(unit)
        else:
            unit.owner = None
            self.discard.append(unit)
        self.state.recycle_empty_areas()


EffectHandler = Callable[[CardDefinition, EffectContext], bool]
_HANDLERS: dict[str, EffectHandler] = {}


def handler(effect_id: str) -> Callable[[EffectHandler], EffectHandler]:
    def register(function: EffectHandler) -> EffectHandler:
        _HANDLERS[effect_id] = function
        return function
    return register


def execute_effect(definition: CardDefinition, context: EffectContext) -> bool:
    if context.cancelled:
        return False
    try:
        function = _HANDLERS[definition.effect_id]
    except KeyError as exc:
        raise NotImplementedError(f"effect not registered: {definition.effect_id}") from exc
    return function(definition, context)


def registered_effect_ids() -> frozenset[str]:
    return frozenset(_HANDLERS)


def _count(parameters: dict[str, Any], key: str = "count", default: int = 1) -> int:
    return int(parameters.get(key, default))


@handler("DRAW_CARDS")
def draw_cards(definition: CardDefinition, context: EffectContext) -> bool:
    return context.draw(context.actor, _count(definition.parameters)) > 0


@handler("DRAW_THEN_DISCARD")
def draw_then_discard(definition: CardDefinition, context: EffectContext) -> bool:
    context.draw(context.actor, _count(definition.parameters, "draw"))
    count = _count(definition.parameters, "discard")
    if len(context.selected_hand_cards) != count:
        return False
    for card in context.selected_hand_cards:
        if card not in context.hands[context.actor]:
            return False
    for card in context.selected_hand_cards:
        context.hands[context.actor].remove(card)
        card.owner = None
        context.discard.append(card)
    return True


@handler("RETURN_OWN_UNIT")
def return_own_unit(definition: CardDefinition, context: EffectContext) -> bool:
    count = _count(definition.parameters)
    if len(context.selected_units) != count:
        return False
    if any(unit.owner != context.actor for unit in context.selected_units):
        return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True)
    return True


@handler("DEFEAT_UNIT_BY_LEVEL")
def defeat_unit_by_level(definition: CardDefinition, context: EffectContext) -> bool:
    if len(context.selected_units) != _count(definition.parameters):
        return False
    exact = definition.parameters.get("level_exact")
    maximum = definition.parameters.get("level_max")
    for unit in context.selected_units:
        if exact is not None and unit.level != exact:
            return False
        if maximum is not None and unit.level > maximum:
            return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=False)
    return True


@handler("RETURN_UNIT_BY_LEVEL")
def return_unit_by_level(definition: CardDefinition, context: EffectContext) -> bool:
    if len(context.selected_units) != _count(definition.parameters):
        return False
    exact = definition.parameters.get("level_exact")
    maximum = definition.parameters.get("level_max")
    for unit in context.selected_units:
        if exact is not None and unit.level != exact:
            return False
        if maximum is not None and unit.level > maximum:
            return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True)
    return True


@handler("RETURN_MULTIPLE_UNITS")
def return_multiple_units(definition: CardDefinition, context: EffectContext) -> bool:
    count = _count(definition.parameters)
    if len(context.selected_units) != count:
        return False
    maximum = definition.parameters.get("level_max")
    if maximum is not None and any(unit.level > maximum for unit in context.selected_units):
        return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True)
    return True


@handler("TAKE_UNIT_TO_HAND")
def take_unit_to_hand(definition: CardDefinition, context: EffectContext) -> bool:
    if len(context.selected_units) != _count(definition.parameters):
        return False
    exact = definition.parameters.get("level_exact")
    if exact is not None and any(unit.level != exact for unit in context.selected_units):
        return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True, new_owner=context.actor)
    return True


@handler("FORCE_OTHER_PLAYER_DISCARD")
def force_other_player_discard(definition: CardDefinition, context: EffectContext) -> bool:
    target = context.selected_player
    if target is None or target == context.actor:
        return False
    count = _count(definition.parameters)
    if len(context.selected_hand_cards) != count:
        return False
    if any(card not in context.hands[target] for card in context.selected_hand_cards):
        return False
    for card in context.selected_hand_cards:
        context.hands[target].remove(card)
        card.owner = None
        context.discard.append(card)
    return True


@handler("RETURN_ALL_UNITS_IN_AREA")
def return_all_units_in_area(definition: CardDefinition, context: EffectContext) -> bool:
    area = context.selected_area
    if area is None or area.owner is None or area.protected:
        return False
    for unit in list(area.units):
        context.remove_unit(unit, to_hand=True)
    return True


@handler("DEFEAT_LOW_LEVEL_UNITS_IN_AREA")
def defeat_low_level_units_in_area(definition: CardDefinition, context: EffectContext) -> bool:
    area = context.selected_area
    if area is None or area.owner is None or area.protected:
        return False
    levels = set(definition.parameters.get("levels", ()))
    targets = [unit for unit in area.units if unit.level in levels]
    for unit in targets:
        context.remove_unit(unit, to_hand=False)
    return bool(targets)


@handler("PROTECT_AREA")
def protect_area(definition: CardDefinition, context: EffectContext) -> bool:
    area = context.selected_area
    if area is None or area.owner != context.actor:
        return False
    area.protected = True
    return True


@handler("SOCIAL_CALL_DRAW")
def social_call_draw(definition: CardDefinition, context: EffectContext) -> bool:
    target = context.selected_player
    if not context.social_response or target is None or target == context.actor:
        return False
    context.draw(context.actor, _count(definition.parameters, "self_draw"))
    context.draw(target, _count(definition.parameters, "target_draw"))
    return True


@handler("CANCEL_EFFECT")
def cancel_effect(definition: CardDefinition, context: EffectContext) -> bool:
    context.cancelled = True
    return True
