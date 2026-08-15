"""Immutable domain models used by the parser, filters, and exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MenuItem:
    canteen: str
    category: str
    name: str
    price_eur: Decimal
    allergens: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.canteen.strip():
            raise ValueError("canteen must not be empty")
        if not self.category.strip():
            raise ValueError("category must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if self.price_eur < 0:
            raise ValueError("price_eur must not be negative")
        normalized = tuple(sorted(set(self.allergens)))
        if any(value < 1 or value > 14 for value in normalized):
            raise ValueError("allergen identifiers must be between 1 and 14")
        object.__setattr__(self, "allergens", normalized)

    def as_dict(self) -> dict[str, object]:
        return {
            "canteen": self.canteen,
            "category": self.category,
            "name": self.name,
            "price_eur": f"{self.price_eur:.2f}",
            "allergens": list(self.allergens),
        }


@dataclass(frozen=True, slots=True)
class CanteenMenu:
    name: str
    items: tuple[MenuItem, ...] = ()
    opens_at: str | None = None
    closes_at: str | None = None
    announcement: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("canteen name must not be empty")
        if any(item.canteen != self.name for item in self.items):
            raise ValueError("every item must belong to this canteen")


@dataclass(frozen=True, slots=True)
class MenuSnapshot:
    menu_date: date
    source_url: str
    canteens: tuple[CanteenMenu, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def items(self) -> tuple[MenuItem, ...]:
        return tuple(item for canteen in self.canteens for item in canteen.items)

    def as_dict(self) -> dict[str, object]:
        return {
            "menu_date": self.menu_date.isoformat(),
            "source_url": self.source_url,
            "canteens": [
                {
                    "name": canteen.name,
                    "opens_at": canteen.opens_at,
                    "closes_at": canteen.closes_at,
                    "announcement": canteen.announcement,
                    "item_count": len(canteen.items),
                }
                for canteen in self.canteens
            ],
            "items": [item.as_dict() for item in self.items],
            "warnings": list(self.warnings),
        }

