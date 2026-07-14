from pathlib import Path
import random
import unittest

from engine import (
    Area,
    CardDefinition,
    EffectCard,
    EffectContext,
    GameState,
    Unit,
    execute_effect,
    load_deck,
    registered_effect_ids,
)


ROOT = Path(__file__).resolve().parents[1]


class ExtendedEffectTests(unittest.TestCase):
    def setUp(self):
        self.state = GameState((0, 1), center_size=1, rng=random.Random(7))
        self.own_area = Area("A1", "G1", 0, [Unit("CORE-U18", 5, 0, uid=1)])
        self.enemy_unit = Unit("CORE-U07", 1, 1, uid=2)
        self.enemy_area = Area("A2", "G2", 1, [self.enemy_unit])
        self.destination = Area("A3", "G3", 0, [Unit("CORE-U01", 1, 0, uid=3)])
        self.state.controlled[0] = [self.own_area, self.destination]
        self.state.controlled[1] = [self.enemy_area]
        self.hands = {
            0: [EffectCard("CORE-E01", 0, uid=10)],
            1: [Unit("CORE-U02", 1, 1, uid=11)],
        }
        self.deck = [
            EffectCard("CORE-E02", uid=20),
            Unit("CORE-U03", 1, uid=21),
            Unit("CORE-U04", 1, uid=22),
        ]
        self.discard = [Unit("CORE-U05", 1, uid=30)]

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

    def test_context_supports_effect_cards(self):
        context = self.context()
        self.assertIsInstance(context.hands[0][0], EffectCard)
        self.assertIsInstance(context.deck[0], EffectCard)

    def test_view_random_hand_card(self):
        context = self.context(selected_player=1)
        self.assertTrue(execute_effect(self.definition("VIEW_RANDOM_HAND_CARD"), context))
        self.assertEqual(context.revealed_cards, self.hands[1])

    def test_recover_unit_from_discard(self):
        recovered = self.discard[0]
        context = self.context(selected_hand_cards=[recovered])
        self.assertTrue(
            execute_effect(
                self.definition("RECOVER_UNIT_FROM_DISCARD", {"count": 1, "level": 1}),
                context,
            )
        )
        self.assertIn(recovered, self.hands[0])
        self.assertEqual(recovered.owner, 0)

    def test_look_top_and_choose_moves_rest_to_bottom(self):
        chosen = self.deck[1]
        context = self.context(selected_deck_cards=[chosen])
        self.assertTrue(
            execute_effect(
                self.definition("LOOK_TOP_AND_CHOOSE", {"look": 2, "draw": 1}),
                context,
            )
        )
        self.assertIn(chosen, self.hands[0])
        self.assertEqual(self.deck[-1].uid, 20)

    def test_random_take_changes_owner(self):
        context = self.context(selected_player=1)
        self.assertTrue(
            execute_effect(
                self.definition("TAKE_RANDOM_HAND_CARD", {"count": 1}),
                context,
            )
        )
        self.assertEqual(len(self.hands[1]), 0)
        self.assertEqual(context.revealed_cards[0].owner, 0)

    def test_secret_swap(self):
        own = self.hands[0][0]
        other = self.hands[1][0]
        context = self.context(
            selected_player=1,
            selected_actor_cards=[own],
            selected_target_cards=[other],
        )
        self.assertTrue(
            execute_effect(
                self.definition("SECRET_SWAP_HAND_CARD", {"each_choose": 1}),
                context,
            )
        )
        self.assertIn(other, self.hands[0])
        self.assertIn(own, self.hands[1])

    def test_take_unit_to_controlled_area(self):
        context = self.context(
            destination_area=self.destination,
            selected_units=[self.enemy_unit],
        )
        self.assertTrue(
            execute_effect(
                self.definition("TAKE_UNIT_TO_CONTROLLED_AREA", {"count": 1, "level_exact": 1}),
                context,
            )
        )
        self.assertIn(self.enemy_unit, self.destination.units)
        self.assertEqual(self.enemy_unit.owner, 0)
        self.assertEqual(self.state.area_returns, 1)

    def test_conditional_draw(self):
        context = self.context()
        self.assertTrue(
            execute_effect(
                self.definition(
                    "CONDITIONAL_DRAW",
                    {"required_mechanic_id": "CORE-U18", "count": 2},
                ),
                context,
            )
        )
        self.assertEqual(len(self.hands[0]), 3)

    def test_pay_discard_then_return(self):
        cost = self.hands[0][0]
        context = self.context(
            selected_hand_cards=[cost],
            selected_units=[self.enemy_unit],
        )
        self.assertTrue(
            execute_effect(
                self.definition("PAY_DISCARD_RETURN_UNIT", {"cost_discard": 1, "count": 1}),
                context,
            )
        )
        self.assertIn(cost, self.discard)
        self.assertIn(self.enemy_unit, self.hands[1])

    def test_social_call_take_unit(self):
        context = self.context(
            selected_player=1,
            selected_units=[self.enemy_unit],
            social_response=True,
        )
        self.assertTrue(
            execute_effect(
                self.definition("SOCIAL_CALL_TAKE_UNIT", {"count": 1}),
                context,
            )
        )
        self.assertIn(self.enemy_unit, self.hands[0])
        self.assertEqual(self.enemy_unit.owner, 0)


class EffectCoverageTests(unittest.TestCase):
    def test_all_data_effects_are_registered_or_orchestration_effects(self):
        core = load_deck(ROOT / "data" / "core_set.json")
        expansion = load_deck(ROOT / "data" / "expansion_1.json")
        effect_ids = {card.effect_id for card in (*core.cards, *expansion.cards)}
        orchestration = {
            "REPLACE_DISCARD_WITH_DECK_SHUFFLE",
            "PLAY_EXTRA_UNIT",
            "IMMEDIATE_ATTACK",
        }
        missing = effect_ids - registered_effect_ids() - orchestration
        self.assertEqual(missing, set())


if __name__ == "__main__":
    unittest.main()
