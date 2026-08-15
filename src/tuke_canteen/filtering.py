"""Composable menu filters used by the CLI and library API."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable
import unicodedata

from .models import MenuItem, MenuSnapshot


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not unicodedata.combining(character)).strip()


def filter_items(
    snapshot: MenuSnapshot,
    *,
    canteen: str | None = None,
    category: str | None = None,
    max_price: Decimal | None = None,
    exclude_allergens: Iterable[int] = (),
    contains: str | None = None,
) -> tuple[MenuItem, ...]:
    if max_price is not None and max_price < 0:
        raise ValueError("max_price must not be negative")
    excluded = set(exclude_allergens)
    if any(value < 1 or value > 14 for value in excluded):
        raise ValueError("allergen identifiers must be between 1 and 14")
    canteen_query = _search_key(canteen) if canteen else None
    category_query = _search_key(category) if category else None
    text_query = _search_key(contains) if contains else None

    result = []
    for item in snapshot.items:
        if canteen_query and canteen_query not in _search_key(item.canteen):
            continue
        if category_query:
            category_key = _search_key(item.category)
            if category_key != category_query and not category_key.startswith(category_query + " "):
                continue
        if max_price is not None and item.price_eur > max_price:
            continue
        if excluded.intersection(item.allergens):
            continue
        if text_query and text_query not in _search_key(item.name):
            continue
        result.append(item)
    return tuple(result)
