from pathlib import Path
import unittest

from engine import (
    EffectCard,
    Unit,
    create_deck_instances,
    generate_attack_results,
    load_deck,
)


ROOT = Path(__file__).resolve().parents[1]


class CardInstanceTests(unittest.TestCase):
    def test_core_deck_builds_unit_and_effect_instances(self):
        deck = load_deck(ROOT / "data" / "core_set.json")
        cards = create_deck_instances(deck)
        self.assertEqual(len(cards), 40)
        self.assertEqual(len({card.uid for card in cards}), 40)
        self.assertEqual(sum(isinstance(card, Unit) for card in cards), 36)
        self.assertEqual(sum(isinstance(card, EffectCard) for card in cards), 4)

    def test_effect_card_has_no_level(self):
        card = EffectCard("CORE-E01", uid=8)
        self.assertEqual(card.kind, "effect")
        self.assertIsNone(card.level)


class BattlePlanTests(unittest.TestCase):
    def test_enumerates_attacker_orders_and_targets(self):
        attackers = [
            Unit("A1", 1, uid=1),
            Unit("A2", 2, uid=2),
        ]
        defenders = [
            Unit("D1", 1, uid=3),
            Unit("D2", 2, uid=4),
        ]
        results = generate_attack_results(attackers, defenders)
        self.assertGreater(len(results), 1)
        self.assertGreater(len({result.attack_order for result in results}), 1)
        self.assertGreater(len({result.target_order for result in results}), 1)

    def test_enumeration_does_not_mutate_input(self):
        attackers = [Unit("A", 3, damage=0, uid=1)]
        defenders = [Unit("D", 2, damage=0, uid=2)]
        generate_attack_results(attackers, defenders)
        self.assertEqual(attackers[0].damage, 0)
        self.assertEqual(defenders[0].damage, 0)

    def test_mutual_defeat_is_not_success(self):
        results = generate_attack_results(
            [Unit("A", 2, uid=1)],
            [Unit("D", 2, uid=2)],
        )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)


if __name__ == "__main__":
    unittest.main()
