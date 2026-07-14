import random
import unittest

from engine import (
    Area,
    AttackAction,
    CardDefinition,
    DeployAction,
    EffectContext,
    GameState,
    TurnPhase,
    TurnState,
    Unit,
    execute_effect,
    is_legal_attack,
    is_legal_deploy,
    registered_effect_ids,
)


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState((0, 1), rng=random.Random(1))
        self.center = Area("A0", "G0")
        self.own = Area("A1", "G1", 0, [Unit("U1", 2, 0)])
        self.enemy = Area("A2", "G2", 1, [Unit("U2", 2, 1)])
        self.state.center = [self.center]
        self.state.controlled[0] = [self.own]
        self.state.controlled[1] = [self.enemy]

    def test_deploy_to_center_or_own_area(self):
        unit = Unit("U3", 1, 0)
        self.assertTrue(is_legal_deploy(self.state, DeployAction(0, unit, self.center)))
        self.assertTrue(is_legal_deploy(self.state, DeployAction(0, unit, self.own)))
        self.assertFalse(is_legal_deploy(self.state, DeployAction(0, unit, self.enemy)))

    def test_attack_legality(self):
        action = AttackAction(0, self.own, self.enemy, (self.own.units[0],))
        self.assertTrue(is_legal_attack(self.state, action))
        self.enemy.protected = True
        self.assertFalse(is_legal_attack(self.state, action))


class TurnTests(unittest.TestCase):
    def test_turn_phase_order_and_single_action(self):
        turn = TurnState(0)
        self.assertEqual(turn.phase, TurnPhase.START)
        while not turn.complete:
            turn.advance()
        self.assertEqual(turn.phase, TurnPhase.END)
        turn = TurnState(0)
        turn.mark_action_used()
        with self.assertRaises(RuntimeError):
            turn.mark_action_used()


class EffectTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState((0, 1), center_size=1, rng=random.Random(1))
        self.own_unit = Unit("CORE-U01", 1, 0)
        self.enemy_unit = Unit("CORE-U07", 1, 1)
        self.own_area = Area("A1", "G1", 0, [self.own_unit])
        self.enemy_area = Area("A2", "G2", 1, [self.enemy_unit])
        self.state.controlled[0] = [self.own_area]
        self.state.controlled[1] = [self.enemy_area]
        self.hands = {0: [], 1: []}
        self.deck = [Unit("DRAW", 1)]
        self.discard = []

    def definition(self, effect_id, parameters=None):
        return CardDefinition(
            mechanic_id="TEST",
            kind="unit",
            level=1,
            copies=1,
            effect_id=effect_id,
            timing="on_enter",
            parameters=parameters or {},
        )

    def context(self, **kwargs):
        return EffectContext(
            state=self.state,
            hands=self.hands,
            deck=self.deck,
            discard=self.discard,
            actor=0,
            **kwargs,
        )

    def test_draw_cards(self):
        ok = execute_effect(self.definition("DRAW_CARDS", {"count": 1}), self.context())
        self.assertTrue(ok)
        self.assertEqual(len(self.hands[0]), 1)

    def test_return_enemy_unit_changes_no_ownership_by_default(self):
        ok = execute_effect(
            self.definition("RETURN_UNIT_BY_LEVEL", {"count": 1, "level_exact": 1}),
            self.context(selected_units=[self.enemy_unit]),
        )
        self.assertTrue(ok)
        self.assertIn(self.enemy_unit, self.hands[1])
        self.assertEqual(self.state.area_returns, 1)

    def test_take_unit_to_hand_changes_ownership(self):
        ok = execute_effect(
            self.definition("TAKE_UNIT_TO_HAND", {"count": 1, "level_exact": 1}),
            self.context(selected_units=[self.enemy_unit]),
        )
        self.assertTrue(ok)
        self.assertIn(self.enemy_unit, self.hands[0])
        self.assertEqual(self.enemy_unit.owner, 0)

    def test_protect_area(self):
        ok = execute_effect(
            self.definition("PROTECT_AREA", {"count": 1}),
            self.context(selected_area=self.own_area),
        )
        self.assertTrue(ok)
        self.assertTrue(self.own_area.protected)

    def test_registry_contains_foundational_handlers(self):
        required = {
            "DRAW_CARDS",
            "RETURN_OWN_UNIT",
            "DEFEAT_UNIT_BY_LEVEL",
            "RETURN_UNIT_BY_LEVEL",
            "TAKE_UNIT_TO_HAND",
            "PROTECT_AREA",
            "CANCEL_EFFECT",
        }
        self.assertTrue(required.issubset(registered_effect_ids()))


if __name__ == "__main__":
    unittest.main()
