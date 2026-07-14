from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .data import CardDefinition
from .models import Area, CardInstance, Unit
from .state import GameState


@dataclass
class EffectContext:
    state: GameState
    hands: dict[int, list[CardInstance]]
    deck: list[CardInstance]
    discard: list[CardInstance]
    actor: int
    selected_player: int | None = None
    selected_area: Area | None = None
    destination_area: Area | None = None
    selected_units: list[Unit] = field(default_factory=list)
    selected_hand_cards: list[CardInstance] = field(default_factory=list)
    selected_actor_cards: list[CardInstance] = field(default_factory=list)
    selected_target_cards: list[CardInstance] = field(default_factory=list)
    selected_deck_cards: list[CardInstance] = field(default_factory=list)
    revealed_cards: list[CardInstance] = field(default_factory=list)
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

    def discard_cards(self, player: int, cards: list[CardInstance]) -> bool:
        if any(card not in self.hands[player] for card in cards):
            return False
        for card in cards:
            self.hands[player].remove(card)
            card.owner = None
            self.discard.append(card)
        return True

    def find_area(self, unit: Unit) -> Area | None:
        for areas in self.state.controlled.values():
            for area in areas:
                if unit in area.units:
                    return area
        return None

    def all_units_in_play(self) -> list[Unit]:
        return [
            unit
            for areas in self.state.controlled.values()
            for area in areas
            for unit in area.units
        ]

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


def _valid_other_player(context: EffectContext) -> int | None:
    target = context.selected_player
    if target is None or target == context.actor or target not in context.hands:
        return None
    return target


@handler("DRAW_CARDS")
def draw_cards(definition: CardDefinition, context: EffectContext) -> bool:
    return context.draw(context.actor, _count(definition.parameters)) > 0


@handler("DRAW_THEN_DISCARD")
def draw_then_discard(definition: CardDefinition, context: EffectContext) -> bool:
    context.draw(context.actor, _count(definition.parameters, "draw"))
    count = _count(definition.parameters, "discard")
    if len(context.selected_hand_cards) != count:
        return False
    return context.discard_cards(context.actor, context.selected_hand_cards)


@handler("VIEW_RANDOM_HAND_CARD")
def view_random_hand_card(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None or not context.hands[target]:
        return False
    count = min(_count(definition.parameters), len(context.hands[target]))
    context.revealed_cards[:] = context.state.rng.sample(context.hands[target], count)
    return True


@handler("SOCIAL_CALL_EXCHANGE")
def social_call_exchange(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None or not context.social_response:
        return False
    context.draw(context.actor, _count(definition.parameters, "each_draw"))
    context.draw(target, _count(definition.parameters, "each_draw"))
    discard_count = _count(definition.parameters, "each_discard")
    if len(context.selected_actor_cards) != discard_count:
        return False
    if len(context.selected_target_cards) != discard_count:
        return False
    if not context.discard_cards(context.actor, context.selected_actor_cards):
        return False
    return context.discard_cards(target, context.selected_target_cards)


@handler("SOCIAL_CALL_DRAW")
def social_call_draw(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if not context.social_response or target is None:
        return False
    context.draw(context.actor, _count(definition.parameters, "self_draw"))
    context.draw(target, _count(definition.parameters, "target_draw"))
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


@handler("RECOVER_UNIT_FROM_DISCARD")
def recover_unit_from_discard(definition: CardDefinition, context: EffectContext) -> bool:
    count = _count(definition.parameters)
    level = int(definition.parameters["level"])
    if len(context.selected_hand_cards) != count:
        return False
    for card in context.selected_hand_cards:
        if card not in context.discard or not isinstance(card, Unit) or card.level != level:
            return False
    for card in context.selected_hand_cards:
        context.discard.remove(card)
        card.owner = context.actor
        context.hands[context.actor].append(card)
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
        if maximum is not None and int(unit.level) > int(maximum):
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
        if maximum is not None and int(unit.level) > int(maximum):
            return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True)
    return True


@handler("LOOK_TOP_AND_CHOOSE")
def look_top_and_choose(definition: CardDefinition, context: EffectContext) -> bool:
    look = min(_count(definition.parameters, "look"), len(context.deck))
    choose = _count(definition.parameters, "draw")
    if look == 0 or len(context.selected_deck_cards) != choose:
        return False
    top = context.deck[:look]
    if any(card not in top for card in context.selected_deck_cards):
        return False
    context.deck[:look] = []
    for card in context.selected_deck_cards:
        top.remove(card)
        card.owner = context.actor
        context.hands[context.actor].append(card)
    context.deck.extend(top)
    return True


@handler("TAKE_RANDOM_HAND_CARD")
def take_random_hand_card(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None or not context.hands[target]:
        return False
    count = min(_count(definition.parameters), len(context.hands[target]))
    chosen = context.state.rng.sample(context.hands[target], count)
    for card in chosen:
        context.hands[target].remove(card)
        card.owner = context.actor
        context.hands[context.actor].append(card)
    context.revealed_cards[:] = chosen
    return True


@handler("SECRET_SWAP_HAND_CARD")
def secret_swap_hand_card(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None:
        return False
    each = _count(definition.parameters, "each_choose")
    if len(context.selected_actor_cards) != each or len(context.selected_target_cards) != each:
        return False
    if any(card not in context.hands[context.actor] for card in context.selected_actor_cards):
        return False
    if any(card not in context.hands[target] for card in context.selected_target_cards):
        return False
    for card in context.selected_actor_cards:
        context.hands[context.actor].remove(card)
        card.owner = target
        context.hands[target].append(card)
    for card in context.selected_target_cards:
        context.hands[target].remove(card)
        card.owner = context.actor
        context.hands[context.actor].append(card)
    return True


@handler("RETURN_MULTIPLE_UNITS")
def return_multiple_units(definition: CardDefinition, context: EffectContext) -> bool:
    count = _count(definition.parameters)
    if len(context.selected_units) != count:
        return False
    maximum = definition.parameters.get("level_max")
    if maximum is not None and any(int(unit.level) > int(maximum) for unit in context.selected_units):
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


@handler("TAKE_UNIT_TO_CONTROLLED_AREA")
def take_unit_to_controlled_area(definition: CardDefinition, context: EffectContext) -> bool:
    destination = context.destination_area
    if destination is None or destination.owner != context.actor:
        return False
    if len(destination.units) >= context.state.max_units_per_area:
        return False
    if len(context.selected_units) != _count(definition.parameters):
        return False
    exact = definition.parameters.get("level_exact")
    if exact is not None and any(unit.level != exact for unit in context.selected_units):
        return False
    for unit in list(context.selected_units):
        source = context.find_area(unit)
        if source is None or source is destination:
            return False
        source.units.remove(unit)
        unit.owner = context.actor
        destination.units.append(unit)
    context.state.recycle_empty_areas()
    return True


@handler("FORCE_OTHER_PLAYER_DISCARD")
def force_other_player_discard(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None:
        return False
    count = _count(definition.parameters)
    if len(context.selected_hand_cards) != count:
        return False
    return context.discard_cards(target, context.selected_hand_cards)


@handler("CONDITIONAL_DRAW")
def conditional_draw(definition: CardDefinition, context: EffectContext) -> bool:
    required = str(definition.parameters["required_mechanic_id"])
    if not any(unit.mechanic_id == required for unit in context.all_units_in_play()):
        return False
    return context.draw(context.actor, _count(definition.parameters)) > 0


@handler("PAY_DISCARD_RETURN_UNIT")
def pay_discard_return_unit(definition: CardDefinition, context: EffectContext) -> bool:
    cost = _count(definition.parameters, "cost_discard")
    if len(context.selected_hand_cards) != cost:
        return False
    if len(context.selected_units) != _count(definition.parameters):
        return False
    if not context.discard_cards(context.actor, context.selected_hand_cards):
        return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True)
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


@handler("SOCIAL_CALL_TAKE_UNIT")
def social_call_take_unit(definition: CardDefinition, context: EffectContext) -> bool:
    target = _valid_other_player(context)
    if target is None or not context.social_response:
        return False
    if len(context.selected_units) != _count(definition.parameters):
        return False
    if any(unit.owner != target for unit in context.selected_units):
        return False
    for unit in list(context.selected_units):
        context.remove_unit(unit, to_hand=True, new_owner=context.actor)
    return True


@handler("PROTECT_AREA")
def protect_area(definition: CardDefinition, context: EffectContext) -> bool:
    area = context.selected_area
    if area is None or area.owner != context.actor:
        return False
    area.protected = True
    return True


@handler("CANCEL_EFFECT")
def cancel_effect(definition: CardDefinition, context: EffectContext) -> bool:
    context.cancelled = True
    return True
