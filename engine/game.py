from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .actions import AttackAction, DeployAction, PassAction, is_legal_attack, is_legal_deploy
from .combat import AttackResult, resolve_attack
from .data import CardDefinition
from .effects import EffectContext, execute_effect
from .models import Area, CardInstance, EffectCard, GameResult, Unit
from .state import GameState
from .turns import TurnState


ResponsePolicy = Callable[[int, CardInstance, CardDefinition], EffectCard | None]
EffectContextFactory = Callable[[CardDefinition, EffectContext], EffectContext]


@dataclass
class GameEngine:
    state: GameState
    definitions: dict[str, CardDefinition]
    deck: list[CardInstance]
    hands: dict[int, list[CardInstance]]
    discard: list[CardInstance] = field(default_factory=list)
    current_player_index: int = 0
    turns: int = 0
    hand_limit: int = 7
    winner: int | None = None
    deck_exhausted: bool = False
    no_progress_players: set[int] = field(default_factory=set)
    response_policy: ResponsePolicy | None = None

    @property
    def current_player(self) -> int:
        return self.state.players[self.current_player_index]

    def definition_for(self, card: CardInstance) -> CardDefinition:
        try:
            return self.definitions[card.mechanic_id]
        except KeyError as exc:
            raise KeyError(f"missing definition: {card.mechanic_id}") from exc

    def draw(self, player: int, count: int = 1) -> int:
        drawn = 0
        for _ in range(count):
            if not self.deck:
                self.deck_exhausted = True
                break
            card = self.deck.pop(0)
            card.owner = player
            self.hands[player].append(card)
            drawn += 1
        return drawn

    def start_turn(self) -> TurnState:
        player = self.current_player
        self.turns += 1
        self.clear_expired_protection(player)
        turn = TurnState(player)
        turn.advance()  # DRAW
        self.draw(player)
        turn.advance()  # CHOOSE_ACTION
        return turn

    def clear_expired_protection(self, player: int) -> None:
        for area in self.state.controlled[player]:
            if area.protected and area.protection_owner == player:
                area.clear_protection()

    def deploy(self, action: DeployAction, context: EffectContext | None = None) -> bool:
        if not is_legal_deploy(self.state, action):
            return False
        if action.unit not in self.hands[action.player]:
            return False
        self.hands[action.player].remove(action.unit)
        destination = action.destination
        gained = destination.owner is None
        if gained:
            if destination in self.state.center:
                self.state.center.remove(destination)
            destination.owner = action.player
            self.state.controlled[action.player].append(destination)
            self.state.refill_center()
        destination.units.append(action.unit)
        action.unit.owner = action.player
        self.no_progress_players.clear()
        if self._mark_winner():
            return True
        definition = self.definition_for(action.unit)
        if definition.timing == "on_enter":
            effect_context = context or self.base_effect_context(action.player)
            self.resolve_card_effect(action.unit, definition, effect_context)
        self.state.recycle_empty_areas()
        self._mark_winner()
        return True

    def attack(self, action: AttackAction) -> AttackResult | None:
        if not is_legal_attack(self.state, action):
            return None
        result = resolve_attack(list(action.attackers), list(action.target.units))
        origin = action.origin
        target = action.target
        for unit in action.attackers:
            if unit in origin.units:
                origin.units.remove(unit)
        target.units.clear()
        for unit in (*result.attacker_defeated, *result.defender_defeated):
            self.resolve_defeat(unit)
        if result.success:
            old_owner = target.owner
            if old_owner is not None and target in self.state.controlled[old_owner]:
                self.state.controlled[old_owner].remove(target)
            target.owner = action.player
            target.clear_protection()
            target.units = list(result.attacker_survivors)
            for unit in target.units:
                unit.owner = action.player
            self.state.controlled[action.player].append(target)
            self.no_progress_players.clear()
        else:
            target.units = list(result.defender_survivors)
            for unit in result.attacker_survivors:
                origin.units.append(unit)
        self.state.recycle_empty_areas()
        self._mark_winner()
        return result

    def play_effect(
        self,
        player: int,
        card: EffectCard,
        context: EffectContext,
    ) -> bool:
        if card not in self.hands[player]:
            return False
        definition = self.definition_for(card)
        if definition.kind != "effect" or definition.timing not in {"main_action", "response"}:
            return False
        self.hands[player].remove(card)
        cancelled = self.open_response_window(player, card, definition)
        resolved = False
        if not cancelled:
            resolved = execute_effect(definition, context)
        card.owner = None
        self.discard.append(card)
        self.state.recycle_empty_areas()
        self._mark_winner()
        if resolved:
            self.no_progress_players.clear()
        return resolved

    def open_response_window(
        self,
        actor: int,
        source: CardInstance,
        definition: CardDefinition,
    ) -> bool:
        if definition.timing == "response" or self.response_policy is None:
            return False
        for player in self.state.players:
            if player == actor:
                continue
            response = self.response_policy(player, source, definition)
            if response is None or response not in self.hands[player]:
                continue
            response_definition = self.definition_for(response)
            if response_definition.effect_id != "CANCEL_EFFECT":
                continue
            self.hands[player].remove(response)
            response.owner = None
            self.discard.append(response)
            return True
        return False

    def resolve_card_effect(
        self,
        card: CardInstance,
        definition: CardDefinition,
        context: EffectContext,
    ) -> bool:
        if definition.effect_id == "PLAY_EXTRA_UNIT":
            return self.resolve_extra_deploy(context)
        if definition.effect_id == "IMMEDIATE_ATTACK":
            return self.resolve_immediate_attack(context)
        return execute_effect(definition, context)

    def resolve_extra_deploy(self, context: EffectContext) -> bool:
        if len(context.selected_hand_cards) != 1:
            return False
        card = context.selected_hand_cards[0]
        if not isinstance(card, Unit) or context.destination_area is None:
            return False
        return self.deploy(
            DeployAction(context.actor, card, context.destination_area),
            context=self.base_effect_context(context.actor),
        )

    def resolve_immediate_attack(self, context: EffectContext) -> bool:
        if context.selected_area is None or context.destination_area is None:
            return False
        if not context.selected_units:
            return False
        action = AttackAction(
            player=context.actor,
            origin=context.selected_area,
            target=context.destination_area,
            attackers=tuple(context.selected_units),
        )
        return self.attack(action) is not None

    def resolve_defeat(self, card: Unit) -> None:
        definition = self.definition_for(card)
        card.owner = None
        card.damage = 0
        if definition.effect_id == "REPLACE_DISCARD_WITH_DECK_SHUFFLE":
            self.deck.append(card)
            self.state.rng.shuffle(self.deck)
        else:
            self.discard.append(card)

    def base_effect_context(self, actor: int) -> EffectContext:
        return EffectContext(
            state=self.state,
            hands=self.hands,
            deck=self.deck,
            discard=self.discard,
            actor=actor,
        )

    def finish_turn(self, turn: TurnState, action: object | None = None) -> GameResult | None:
        player = turn.player
        progressed = False
        if isinstance(action, PassAction) or action is None:
            pass
        elif isinstance(action, DeployAction):
            progressed = self.deploy(action)
        elif isinstance(action, AttackAction):
            progressed = self.attack(action) is not None
        else:
            progressed = bool(action)
        if progressed:
            turn.mark_action_used()
            turn.public_card_played = isinstance(action, DeployAction)
            self.no_progress_players.clear()
        else:
            self.no_progress_players.add(player)
        while len(self.hands[player]) > self.hand_limit:
            card = self.hands[player].pop()
            card.owner = None
            self.discard.append(card)
        if self.winner is not None:
            return GameResult(self.winner, "immediate_win", self.turns, self.deck_exhausted)
        if self.deck_exhausted and self.no_progress_players == set(self.state.players):
            return self.resolve_final_settlement()
        self.current_player_index = (self.current_player_index + 1) % len(self.state.players)
        return None

    def resolve_final_settlement(self) -> GameResult:
        scores = {player: self.state.final_score(player) for player in self.state.players}
        best = max(scores.values())
        leaders = [player for player, score in scores.items() if score == best]
        winner = leaders[0] if len(leaders) == 1 else None
        self.winner = winner
        reason = "settlement" if winner is not None else "draw"
        return GameResult(winner, reason, self.turns, True, settlement=True)

    def _mark_winner(self) -> bool:
        winner = self.state.check_winner()
        if winner is None:
            return False
        self.winner = winner
        return True
