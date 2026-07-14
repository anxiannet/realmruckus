from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import Area, Unit
from .state import GameState


class ActionType(str, Enum):
    DEPLOY = "deploy"
    ATTACK = "attack"
    PLAY_EFFECT = "play_effect"
    PASS = "pass"


@dataclass(frozen=True)
class DeployAction:
    player: int
    unit: Unit
    destination: Area
    action_type: ActionType = ActionType.DEPLOY


@dataclass(frozen=True)
class AttackAction:
    player: int
    origin: Area
    target: Area
    attackers: tuple[Unit, ...]
    action_type: ActionType = ActionType.ATTACK


@dataclass(frozen=True)
class PassAction:
    player: int
    action_type: ActionType = ActionType.PASS


def is_legal_deploy(state: GameState, action: DeployAction) -> bool:
    destination = action.destination
    if len(destination.units) >= state.max_units_per_area:
        return False
    if destination.owner is None:
        return destination in state.center
    return destination.owner == action.player and destination in state.controlled[action.player]


def is_legal_attack(state: GameState, action: AttackAction) -> bool:
    if action.origin.owner != action.player:
        return False
    if action.origin not in state.controlled[action.player]:
        return False
    if action.target.owner is None or action.target.owner == action.player:
        return False
    if action.target.protected:
        return False
    if not action.target.units:
        return False
    if not 1 <= len(action.attackers) <= state.max_units_per_area:
        return False
    if len(set(id(unit) for unit in action.attackers)) != len(action.attackers):
        return False
    return all(unit in action.origin.units for unit in action.attackers)


def legal_deploy_destinations(state: GameState, player: int) -> tuple[Area, ...]:
    destinations = [area for area in state.center if len(area.units) < state.max_units_per_area]
    destinations.extend(
        area
        for area in state.controlled[player]
        if len(area.units) < state.max_units_per_area
    )
    return tuple(destinations)


def legal_attack_targets(state: GameState, player: int) -> tuple[Area, ...]:
    return tuple(
        area
        for opponent in state.players
        if opponent != player
        for area in state.controlled[opponent]
        if area.units and not area.protected
    )
