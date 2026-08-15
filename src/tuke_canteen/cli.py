"""Command-line interface for live and offline menu exploration."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .client import DEFAULT_MENU_URL, MenuFetchError, build_menu_url, fetch_html
from .filtering import filter_items
from .parser import MenuParseError, parse_menu
from .reporting import render_csv, render_json, render_table


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD format") from exc


def _price(value: str) -> Decimal:
    try:
        result = Decimal(value.replace(",", "."))
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("price must be a decimal number") from exc
    if result < 0:
        raise argparse.ArgumentTypeError("price must not be negative")
    return result


def _allergen(value: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("allergen must be a number from 1 to 14") from exc
    if not 1 <= result <= 14:
        raise argparse.ArgumentTypeError("allergen must be a number from 1 to 14")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tuke-menu",
        description="Explore the public TUKE canteen menu.",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", default=DEFAULT_MENU_URL, help="public menu URL")
    source.add_argument("--input-html", type=Path, help="parse a saved HTML file instead")
    parser.add_argument("--date", type=_iso_date, help="menu date in YYYY-MM-DD format")
    parser.add_argument("--canteen", help="case-insensitive canteen name filter")
    parser.add_argument("--category", help="case-insensitive category filter")
    parser.add_argument("--max-price", type=_price, help="maximum price in EUR")
    parser.add_argument(
        "--exclude-allergen",
        action="append",
        type=_allergen,
        default=[],
        metavar="ID",
        help="exclude allergen ID (repeatable, 1-14)",
    )
    parser.add_argument("--contains", help="case-insensitive text filter")
    parser.add_argument("--format", choices=("table", "json", "csv"), default="table")
    parser.add_argument("--output", type=Path, help="write output to a file")
    parser.add_argument("--timeout", type=float, default=10.0, help="network timeout in seconds")
    return parser


def _load_snapshot(args: argparse.Namespace):
    if args.input_html:
        html = args.input_html.read_text(encoding="utf-8")
        source_url = args.input_html.resolve().as_uri()
    else:
        source_url = build_menu_url(args.url, args.date)
        html = fetch_html(source_url, timeout=args.timeout)
    return parse_menu(html, source_url=source_url)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0:
            raise ValueError("timeout must be positive")
        snapshot = _load_snapshot(args)
        items = filter_items(
            snapshot,
            canteen=args.canteen,
            category=args.category,
            max_price=args.max_price,
            exclude_allergens=args.exclude_allergen,
            contains=args.contains,
        )
        renderer = {"table": render_table, "json": render_json, "csv": render_csv}[args.format]
        output = renderer(snapshot, items)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8", newline="")
        else:
            sys.stdout.write(output)
        return 0
    except (MenuFetchError, MenuParseError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

