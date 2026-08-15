"""Stable JSON, CSV, and terminal representations."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence

from .models import MenuItem, MenuSnapshot


def render_json(snapshot: MenuSnapshot, items: Sequence[MenuItem]) -> str:
    payload = {
        "menu_date": snapshot.menu_date.isoformat(),
        "source_url": snapshot.source_url,
        "count": len(items),
        "items": [item.as_dict() for item in items],
        "warnings": list(snapshot.warnings),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_csv(snapshot: MenuSnapshot, items: Sequence[MenuItem]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["date", "canteen", "category", "name", "price_eur", "allergens"])
    for item in items:
        writer.writerow(
            [
                snapshot.menu_date.isoformat(),
                item.canteen,
                item.category,
                item.name,
                f"{item.price_eur:.2f}",
                ",".join(str(value) for value in item.allergens),
            ]
        )
    return stream.getvalue()


def _truncate(value: str, width: int) -> str:
    return value if len(value) <= width else value[: width - 1] + "…"


def render_table(snapshot: MenuSnapshot, items: Sequence[MenuItem]) -> str:
    if not items:
        return f"TUKE menu for {snapshot.menu_date.isoformat()}\nNo matching menu items.\n"
    headers = ("Canteen", "Category", "Meal", "EUR", "Allergens")
    rows = [
        (
            _truncate(item.canteen, 25),
            _truncate(item.category, 20),
            _truncate(item.name, 45),
            f"{item.price_eur:.2f}",
            ",".join(str(value) for value in item.allergens) or "-",
        )
        for item in items
    ]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]

    def line(values: Sequence[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values)).rstrip()

    separator = "-+-".join("-" * width for width in widths)
    body = "\n".join([line(headers), separator, *(line(row) for row in rows)])
    return f"TUKE menu for {snapshot.menu_date.isoformat()} ({len(items)} items)\n{body}\n"

