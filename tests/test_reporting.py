import csv
import io
import json
import unittest
from pathlib import Path

from tuke_canteen.parser import parse_menu
from tuke_canteen.reporting import render_csv, render_json, render_table


class ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (Path(__file__).parent / "fixtures" / "official_menu.html").read_text(encoding="utf-8")
        cls.snapshot = parse_menu(html, source_url="https://example.test/menu")

    def test_json_is_machine_readable_and_unicode_safe(self):
        payload = json.loads(render_json(self.snapshot, self.snapshot.items))
        self.assertEqual(payload["count"], 4)
        self.assertEqual(payload["items"][0]["price_eur"], "0.90")
        self.assertIn("domáca", payload["items"][0]["name"])

    def test_csv_has_stable_columns(self):
        rows = list(csv.DictReader(io.StringIO(render_csv(self.snapshot, self.snapshot.items))))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1]["allergens"], "1,7")

    def test_table_contains_summary_and_items(self):
        rendered = render_table(self.snapshot, self.snapshot.items)
        self.assertIn("4 items", rendered)
        self.assertIn("Jedáleň Jedlíkova 7", rendered)

    def test_empty_table_has_clear_message(self):
        rendered = render_table(self.snapshot, ())
        self.assertIn("No matching menu items", rendered)


if __name__ == "__main__":
    unittest.main()

