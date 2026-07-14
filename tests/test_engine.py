import random
import unittest

from engine import Area, GameState, Unit, resolve_attack, resolve_duel


class CombatTests(unittest.TestCase):
    def test_simultaneous_damage(self):
        attacker = Unit("A", 3)
        defender = Unit("D", 2)
        resolve_duel(attacker, defender)
        self.assertEqual(attacker.damage, 2)
        self.assertEqual(defender.damage, 3)
        self.assertTrue(attacker.alive)
        self.assertFalse(defender.alive)

    def test_defender_damage_accumulates(self):
        attackers = [Unit("A1", 1), Unit("A2", 1)]
        defenders = [Unit("D", 2)]
        result = resolve_attack(attackers, defenders)
        self.assertFalse(result.success)
        self.assertEqual(len(result.attacker_survivors), 0)
        self.assertEqual(len(result.defender_survivors), 0)

    def test_success_requires_surviving_attacker(self):
        result = resolve_attack([Unit("A", 2)], [Unit("D", 2)])
        self.assertFalse(result.success)

    def test_survivors_recover(self):
        attacker = Unit("A", 3)
        result = resolve_attack([attacker], [Unit("D", 1)])
        self.assertTrue(result.success)
        self.assertEqual(attacker.damage, 0)


class StateTests(unittest.TestCase):
    def test_winner_controls_three_in_group(self):
        state = GameState((0, 1))
        state.controlled[0] = [
            Area("A1", "G1", 0, [Unit("U1", 1, 0)]),
            Area("A2", "G1", 0, [Unit("U2", 1, 0)]),
            Area("A3", "G1", 0, [Unit("U3", 1, 0)]),
        ]
        self.assertEqual(state.check_winner(), 0)

    def test_empty_area_recycles(self):
        state = GameState((0, 1), center_size=2, rng=random.Random(1))
        empty = Area("A1", "G1", 0, [])
        reserve = Area("A2", "G2")
        state.controlled[0] = [empty]
        state.area_deck = [reserve]
        state.recycle_empty_areas()
        self.assertIsNone(empty.owner)
        self.assertEqual(state.area_returns, 1)
        self.assertEqual(len(state.center), 2)

    def test_final_score_order(self):
        state = GameState((0, 1))
        state.controlled[0] = [Area("A1", "G1", 0, [Unit("U", 3, 0)])]
        self.assertEqual(state.final_score(0), (1, 3, 1, 1))


if __name__ == "__main__":
    unittest.main()
