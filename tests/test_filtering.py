import unittest
from decimal import Decimal
from pathlib import Path

from tuke_canteen.filtering import filter_items
from tuke_canteen.parser import parse_menu


class FilteringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (Path(__file__).parent / "fixtures" / "official_menu.html").read_text(encoding="utf-8")
        cls.snapshot = parse_menu(html)

    def test_canteen_filter_is_case_insensitive(self):
        items = filter_items(self.snapshot, canteen="jedlikova")
        self.assertEqual(len(items), 3)

    def test_category_filter_is_case_insensitive(self):
        items = filter_items(self.snapshot, category="mäsité")
        self.assertEqual(len(items), 2)

    def test_price_filter_is_inclusive(self):
        items = filter_items(self.snapshot, max_price=Decimal("4.10"))
        self.assertEqual({item.price_eur for item in items}, {Decimal("0.90"), Decimal("4.10")})

    def test_excludes_any_matching_allergen(self):
        items = filter_items(self.snapshot, exclude_allergens=(7,))
        self.assertEqual([item.name for item in items], ["Pol.domáca zeleninová 350ml", "Bravčové stehno na hubách 94g"])

    def test_text_filter(self):
        items = filter_items(self.snapshot, contains="kuracie")
        self.assertEqual(len(items), 1)

    def test_invalid_allergen_is_rejected(self):
        with self.assertRaises(ValueError):
            filter_items(self.snapshot, exclude_allergens=(0,))


if __name__ == "__main__":
    unittest.main()

