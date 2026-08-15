import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from tuke_canteen.parser import MenuParseError, parse_menu

FIXTURES = Path(__file__).parent / "fixtures"


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.html = (FIXTURES / "official_menu.html").read_text(encoding="utf-8")

    def test_parses_official_layout(self):
        snapshot = parse_menu(self.html, source_url="https://example.test/menu")
        self.assertEqual(snapshot.menu_date, date(2026, 8, 17))
        self.assertEqual(len(snapshot.canteens), 2)
        self.assertEqual(len(snapshot.items), 4)

    def test_extracts_name_without_allergen_numbers(self):
        item = parse_menu(self.html).items[0]
        self.assertEqual(item.name, "Pol.domáca zeleninová 350ml")
        self.assertEqual(item.allergens, (1, 9))

    def test_parses_decimal_comma_price(self):
        item = parse_menu(self.html).items[1]
        self.assertEqual(item.price_eur, Decimal("4.50"))

    def test_extracts_opening_hours_and_announcement(self):
        snapshot = parse_menu(self.html)
        self.assertEqual(snapshot.canteens[0].opens_at, "10:30:00")
        self.assertEqual(snapshot.canteens[0].closes_at, "13:00:00")
        self.assertEqual(snapshot.canteens[1].announcement, "Objednávky prijímame do 8:00.")

    def test_semantic_fallback_layout(self):
        html = (FIXTURES / "semantic_menu.html").read_text(encoding="utf-8")
        snapshot = parse_menu(html)
        self.assertEqual(snapshot.menu_date, date(2026, 8, 18))
        self.assertEqual(snapshot.items[0].name, "Tofu bowl 300g")
        self.assertEqual(snapshot.items[0].allergens, (6, 11))
        self.assertEqual(snapshot.items[0].price_eur, Decimal("3.75"))

    def test_date_can_fall_back_to_url(self):
        html = self.html.replace("Jedálny lístok (17.08.2026)", "Jedálny lístok")
        snapshot = parse_menu(html, source_url="https://example.test/menu/2026-08-19")
        self.assertEqual(snapshot.menu_date, date(2026, 8, 19))

    def test_empty_document_is_rejected(self):
        with self.assertRaises(MenuParseError):
            parse_menu("  ")

    def test_unrecognized_document_is_rejected(self):
        with self.assertRaises(MenuParseError):
            parse_menu("<h1>Not a menu</h1>", source_url="https://example.test/2026-08-17")

    def test_incomplete_row_becomes_warning(self):
        broken = self.html.replace("<div class=\"data col-xs-2\">4,20 €</div>", "", 1)
        snapshot = parse_menu(broken)
        self.assertEqual(len(snapshot.items), 3)
        self.assertEqual(len(snapshot.warnings), 1)


if __name__ == "__main__":
    unittest.main()

