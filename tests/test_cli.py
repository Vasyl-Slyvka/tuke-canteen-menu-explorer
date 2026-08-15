import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tuke_canteen.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "official_menu.html"


class CliTests(unittest.TestCase):
    def test_offline_json_with_filters(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([
                "--input-html", str(FIXTURE),
                "--canteen", "Jedlikova",
                "--exclude-allergen", "7",
                "--format", "json",
            ])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["count"], 2)

    def test_csv_can_be_written_to_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "menu.csv"
            code = main([
                "--input-html", str(FIXTURE),
                "--format", "csv",
                "--output", str(output_path),
            ])
            self.assertEqual(code, 0)
            self.assertTrue(output_path.read_text(encoding="utf-8").startswith("date,canteen"))

    def test_no_matches_is_not_an_error(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--input-html", str(FIXTURE), "--contains", "not-present"])
        self.assertEqual(code, 0)
        self.assertIn("No matching", output.getvalue())

    def test_missing_input_file_returns_controlled_error(self):
        errors = io.StringIO()
        with redirect_stderr(errors):
            code = main(["--input-html", "does-not-exist.html"])
        self.assertEqual(code, 1)
        self.assertIn("error:", errors.getvalue())

    def test_non_positive_timeout_returns_controlled_error(self):
        errors = io.StringIO()
        with redirect_stderr(errors):
            code = main(["--input-html", str(FIXTURE), "--timeout", "0"])
        self.assertEqual(code, 1)
        self.assertIn("timeout must be positive", errors.getvalue())


if __name__ == "__main__":
    unittest.main()

