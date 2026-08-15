import unittest
from datetime import date
from decimal import Decimal

from tuke_canteen.models import CanteenMenu, MenuItem, MenuSnapshot


class ModelTests(unittest.TestCase):
    def test_item_normalizes_allergens(self):
        item = MenuItem("A", "B", "C", Decimal("1.00"), (7, 1, 7))
        self.assertEqual(item.allergens, (1, 7))

    def test_item_rejects_invalid_allergen(self):
        with self.assertRaises(ValueError):
            MenuItem("A", "B", "C", Decimal("1.00"), (15,))

    def test_canteen_rejects_item_from_another_canteen(self):
        item = MenuItem("A", "B", "C", Decimal("1.00"))
        with self.assertRaises(ValueError):
            CanteenMenu("Different", (item,))

    def test_snapshot_flattens_items(self):
        item = MenuItem("A", "B", "C", Decimal("1.00"))
        snapshot = MenuSnapshot(date(2026, 8, 17), "test", (CanteenMenu("A", (item,)),))
        self.assertEqual(snapshot.items, (item,))


if __name__ == "__main__":
    unittest.main()

