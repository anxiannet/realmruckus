from pathlib import Path
import unittest

from engine import combine_decks, load_deck


ROOT = Path(__file__).resolve().parents[1]


class DeckDataTests(unittest.TestCase):
    def test_core_deck_shape(self):
        core = load_deck(ROOT / "data" / "core_set.json")
        self.assertEqual(core.card_count, 40)
        self.assertEqual(len(core.cards), 23)
        self.assertEqual(len(core.areas), 12)

    def test_expansion_shape(self):
        expansion = load_deck(ROOT / "data" / "expansion_1.json")
        self.assertEqual(expansion.card_count, 10)
        self.assertEqual(len(expansion.cards), 8)

    def test_combined_deck_count(self):
        core = load_deck(ROOT / "data" / "core_set.json")
        expansion = load_deck(ROOT / "data" / "expansion_1.json")
        combined = combine_decks(core, expansion)
        self.assertEqual(sum(card.copies for card in combined), 50)

    def test_mechanic_ids_are_unique_across_sets(self):
        core = load_deck(ROOT / "data" / "core_set.json")
        expansion = load_deck(ROOT / "data" / "expansion_1.json")
        ids = [card.mechanic_id for card in combine_decks(core, expansion)]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
