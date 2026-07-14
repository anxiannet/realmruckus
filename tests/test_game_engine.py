from pathlib import Path
import random
import unittest

from engine import (
    Area,
    AttackAction,
    DeployAction,
    EffectCard,
    EffectContext,
    GameEngine,
    GameState,
    PassAction,
    Unit,
    create_deck_instances,
    load_deck,
)


ROOT = Path(__file__).resolve().parents[1]


def build_engine() -> GameEngine:
    deck_definition = load_deck(ROOT / "data" / "core_set.json")
    definitions = {card.mechanic_id: card for card in deck_definition.cards}
    cards = create_deck_instances(deck_definition)
    state = GameState((0, 1), center_size=2, rng=random.Random(3))
    state.center = [Area("C1", "G1"), Area("C2", "G2")]
    return GameEngine(
        state=state,
        definitions=definitions,
        deck=cards,
        hands={0: [], 1: []},
    )


class GameEngineTests(unittest.TestCase):
    def test_start_turn_draws_and_clears_owner_protection(self):
        engine = build_engine()
        area = Area("A1", "G1", 0, [Unit("CORE-U01", 1, 0, uid=100)])
        area.protect_until_owner_turn(0)
        engine.state.controlled[0] = [area]
        turn = engine.start_turn()
        self.assertEqual(turn.player, 0)
        self.assertEqual(len(engine.hands[0]), 1)
        self.assertFalse(area.protected)

    def test_defeat_replacement_returns_card_to_deck(self):
        engine = build_engine()
        special = Unit("CORE-U12", 3, 1, uid=200)
        original_count = len(engine.deck)
        engine.resolve_defeat(special)
        self.assertEqual(len(engine.deck), original_count + 1)
        self.assertNotIn(special, engine.discard)
        self.assertIsNone(special.owner)

    def test_extra_deploy_uses_normal_deploy_flow(self):
        engine = build_engine()
        trigger = Unit("CORE-U18", 5, 0, uid=201)
        extra = Unit("CORE-U03", 1, 0, uid=202)
        destination = engine.state.center[0]
        second_destination = engine.state.center[1]
        engine.hands[0] = [trigger, extra]
        context = engine.base_effect_context(0)
        context.selected_hand_cards = [extra]
        context.destination_area = second_destination
        self.assertTrue(engine.deploy(DeployAction(0, trigger, destination), context))
        self.assertIn(trigger, destination.units)
        self.assertIn(extra, second_destination.units)
        self.assertNotIn(extra, engine.hands[0])

    def test_immediate_attack_uses_normal_attack_flow(self):
        engine = build_engine()
        trigger = Unit("CORE-U19", 5, 0, uid=210)
        attacker = Unit("CORE-U01", 1, 0, uid=211)
        defender = Unit("CORE-U07", 1, 1, uid=212)
        origin = Area("O", "G1", 0, [attacker])
        target = Area("T", "G2", 1, [defender])
        engine.state.controlled[0] = [origin]
        engine.state.controlled[1] = [target]
        engine.hands[0] = [trigger]
        deploy_target = Area("C", "G3")
        engine.state.center = [deploy_target]
        context = engine.base_effect_context(0)
        context.selected_area = origin
        context.destination_area = target
        context.selected_units = [attacker]
        self.assertTrue(engine.deploy(DeployAction(0, trigger, deploy_target), context))
        self.assertNotIn(defender, target.units)
        self.assertIn(defender, engine.discard)

    def test_cancel_response_discards_both_effect_cards(self):
        engine = build_engine()
        source = EffectCard("CORE-E04", 0, uid=220)
        cancel = EffectCard("CORE-E02", 1, uid=221)
        area = Area("A", "G1", 0, [Unit("CORE-U01", 1, 0, uid=222)])
        engine.state.controlled[0] = [area]
        engine.hands[0] = [source]
        engine.hands[1] = [cancel]
        engine.response_policy = lambda player, card, definition: cancel if player == 1 else None
        context = engine.base_effect_context(0)
        context.selected_area = area
        self.assertFalse(engine.play_effect(0, source, context))
        self.assertFalse(area.protected)
        self.assertIn(source, engine.discard)
        self.assertIn(cancel, engine.discard)

    def test_effect_without_response_resolves(self):
        engine = build_engine()
        source = EffectCard("CORE-E04", 0, uid=230)
        area = Area("A", "G1", 0, [Unit("CORE-U01", 1, 0, uid=231)])
        engine.state.controlled[0] = [area]
        engine.hands[0] = [source]
        context = engine.base_effect_context(0)
        context.selected_area = area
        self.assertTrue(engine.play_effect(0, source, context))
        self.assertTrue(area.protected)
        self.assertEqual(area.protection_owner, 0)

    def test_immediate_group_win(self):
        engine = build_engine()
        engine.state.controlled[0] = [
            Area("A1", "G", 0, [Unit("CORE-U01", 1, 0, uid=1)]),
            Area("A2", "G", 0, [Unit("CORE-U02", 1, 0, uid=2)]),
        ]
        third = Area("A3", "G")
        engine.state.center = [third]
        unit = Unit("CORE-U03", 1, 0, uid=3)
        engine.hands[0] = [unit]
        self.assertTrue(engine.deploy(DeployAction(0, unit, third)))
        self.assertEqual(engine.winner, 0)

    def test_empty_deck_full_round_triggers_settlement(self):
        engine = build_engine()
        engine.deck.clear()
        engine.deck_exhausted = True
        engine.state.controlled[0] = [
            Area("A", "G1", 0, [Unit("CORE-U01", 1, 0, uid=1)])
        ]
        first = engine.start_turn()
        self.assertIsNone(engine.finish_turn(first, PassAction(0)))
        second = engine.start_turn()
        result = engine.finish_turn(second, PassAction(1))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.winner, 0)
        self.assertTrue(result.settlement)


if __name__ == "__main__":
    unittest.main()
