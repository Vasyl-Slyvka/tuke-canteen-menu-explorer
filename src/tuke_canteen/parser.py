"""Parser for the public TUKE canteen page and a semantic fallback layout."""

from __future__ import annotations

import copy
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from lxml import etree
from lxml import html as lxml_html

from .models import CanteenMenu, MenuItem, MenuSnapshot

DATE_RE = re.compile(r"(?<!\d)(\d{1,2})\.(\d{1,2})\.(\d{4})(?!\d)")
ISO_DATE_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
PRICE_RE = re.compile(r"(?<!\d)(\d+(?:[.,]\d{1,2})?)\s*(?:€|EUR)", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")


class MenuParseError(ValueError):
    """Raised when a document is not recognizable as a canteen menu."""


def _class(name: str) -> str:
    return f"contains(concat(' ', normalize-space(@class), ' '), ' {name} ')"


def _clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", value.replace("\xa0", " ")).strip()


def _node_text(node: etree._Element | None) -> str:
    return _clean_text(" ".join(node.itertext())) if node is not None else ""


def _first(node: etree._Element, expression: str) -> etree._Element | None:
    matches = node.xpath(expression)
    return matches[0] if matches else None


def _find_date(document: etree._Element, source_url: str) -> date:
    candidates: list[str] = []
    for node in document.xpath("//*[self::h1 or self::h2 or self::h3 or self::h4 or self::time]"):
        candidates.append(_node_text(node))
        if node.get("datetime"):
            candidates.append(node.get("datetime"))
    candidates.append(urlparse(source_url).path)
    for candidate in candidates:
        match = DATE_RE.search(candidate)
        if match:
            try:
                return datetime.strptime(match.group(0), "%d.%m.%Y").date()
            except ValueError:
                continue
        match = ISO_DATE_RE.search(candidate)
        if match:
            try:
                return date.fromisoformat(match.group(0))
            except ValueError:
                continue
    raise MenuParseError("menu date was not found")


def _canteen_containers(document: etree._Element) -> list[etree._Element]:
    primary = document.xpath(f"//*[{_class('jedalen-small')} or {_class('jedalen-full')}]")
    if primary:
        return primary
    return document.xpath(
        f"//*[(@data-canteen) or "
        f"((self::section or self::article) and ({_class('canteen')}))]"
    )


def _canteen_name(container: etree._Element) -> str:
    heading = _first(container, ".//*[self::h1 or self::h2]")
    return _node_text(heading) or _clean_text(container.get("data-canteen", ""))


def _wrapper_for(container: etree._Element) -> etree._Element:
    parent = container.getparent()
    if parent is not None:
        classes = set(parent.get("class", "").split())
        if classes.intersection({"col-md-4", "canteen-wrapper"}):
            return parent
    return container


def _opening_hours(container: etree._Element) -> tuple[str | None, str | None]:
    wrapper = _wrapper_for(container)
    timeline = _first(wrapper, f".//*[{_class('timeline')} or @data-opening-hours]")
    if timeline is None:
        return None, None
    start = _first(timeline, f".//*[{_class('start')} or @data-opens-at]")
    end = _first(timeline, f".//*[{_class('end')} or @data-closes-at]")
    opens_at = None
    closes_at = None
    if start is not None:
        opens_at = _clean_text(start.get("data-time") or start.get("data-opens-at") or _node_text(start))
    if end is not None:
        closes_at = _clean_text(end.get("data-time") or end.get("data-closes-at") or _node_text(end))
    return opens_at or None, closes_at or None


def _category_groups(container: etree._Element) -> list[etree._Element]:
    primary = container.xpath(f".//*[{_class('group')}]")
    if primary:
        return primary
    return container.xpath(
        f".//*[(@data-category) or {_class('menu-group')} or "
        f"(self::section and {_class('category')})]"
    )


def _category_name(group: etree._Element) -> str:
    if group.get("data-category"):
        return _clean_text(group.get("data-category"))
    node = _first(
        group,
        f".//*[{_class('header')} or @data-category-name or self::h3 or self::h4]",
    )
    return _node_text(node)


def _item_rows(group: etree._Element) -> list[etree._Element]:
    rows = group.xpath(
        f".//*[(({_class('row')} and {_class('has_popup')}) or "
        f"@data-menu-item or {_class('menu-item')} or {_class('meal')})]"
    )
    if rows:
        return rows
    candidates = []
    for row in group.xpath(f".//*[{_class('row')}]"):
        if row.xpath(f".//*[{_class('header')}]"):
            continue
        price = row.xpath(f".//*[@data-price or {_class('price')} or ({_class('data')} and {_class('col-xs-2')})]")
        if price:
            candidates.append(row)
    return candidates


def _name_without_allergens(node: etree._Element) -> str:
    cleaned = copy.deepcopy(node)
    allergen_nodes = cleaned.xpath(
        f".//*[{_class('alergens')} or {_class('allergens')} or @data-allergens]"
    )
    for allergen in allergen_nodes:
        parent = allergen.getparent()
        if parent is not None:
            if allergen.tail:
                previous = allergen.getprevious()
                if previous is not None:
                    previous.tail = (previous.tail or "") + allergen.tail
                else:
                    parent.text = (parent.text or "") + allergen.tail
            parent.remove(allergen)
    return _node_text(cleaned)


def _price(row: etree._Element) -> Decimal | None:
    node = _first(
        row,
        f".//*[@data-price or {_class('price')} or ({_class('data')} and {_class('col-xs-2')})]",
    )
    raw = (node.get("data-price") or _node_text(node)) if node is not None else _node_text(row)
    match = PRICE_RE.search(raw)
    used_plain_number = False
    if not match and node is not None and node.get("data-price"):
        match = re.search(r"\d+(?:[.,]\d{1,2})?", raw)
        used_plain_number = True
    if not match:
        return None
    try:
        price_text = match.group(0) if used_plain_number else match.group(1)
        return Decimal(price_text.replace(",", ".")).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _allergens(row: etree._Element) -> tuple[int, ...]:
    values: set[int] = set()
    nodes = row.xpath(
        f".//*[{_class('alergens')} or {_class('allergens')} or @data-allergens]"
    )
    for node in nodes:
        raw_parts = [node.get("data-allergens", ""), _node_text(node)]
        raw_parts.extend(_node_text(abbr) for abbr in node.xpath(".//abbr"))
        for raw in raw_parts:
            for token in re.findall(r"(?<!\d)(\d{1,2})(?!\d)", raw):
                value = int(token)
                if 1 <= value <= 14:
                    values.add(value)
    if not nodes:
        for abbr in row.xpath(".//abbr"):
            text = _node_text(abbr)
            if text.isdigit() and 1 <= int(text) <= 14:
                values.add(int(text))
    return tuple(sorted(values))


def _parse_item(row: etree._Element, *, canteen: str, category: str) -> MenuItem | None:
    name_node = _first(
        row,
        f".//*[@data-name or {_class('meal-name')} or {_class('name')} or "
        f"({_class('data')} and {_class('col-xs-10')})]",
    )
    if name_node is None:
        return None
    name = _clean_text(name_node.get("data-name", "")) or _name_without_allergens(name_node)
    price = _price(row)
    if not name or price is None:
        return None
    return MenuItem(
        canteen=canteen,
        category=category,
        name=name,
        price_eur=price,
        allergens=_allergens(row),
    )


def parse_menu(html: str, *, source_url: str = "") -> MenuSnapshot:
    """Parse public menu HTML without making any network requests."""
    if not html or not html.strip():
        raise MenuParseError("menu document is empty")
    try:
        document = lxml_html.fromstring(html)
    except (etree.ParserError, ValueError) as exc:
        raise MenuParseError("menu document is not valid HTML") from exc
    menu_date = _find_date(document, source_url)
    containers = _canteen_containers(document)
    if not containers:
        raise MenuParseError("no canteen sections were found")

    canteens: list[CanteenMenu] = []
    warnings: list[str] = []
    for container in containers:
        canteen_name = _canteen_name(container)
        if not canteen_name:
            warnings.append("skipped a canteen section without a name")
            continue
        items: list[MenuItem] = []
        for group in _category_groups(container):
            category = _category_name(group)
            if not category:
                warnings.append(f"{canteen_name}: skipped a category without a name")
                continue
            for row in _item_rows(group):
                item = _parse_item(row, canteen=canteen_name, category=category)
                if item is None:
                    warnings.append(f"{canteen_name}/{category}: skipped an incomplete menu row")
                else:
                    items.append(item)
        opens_at, closes_at = _opening_hours(container)
        announcement_node = _first(container, f".//*[{_class('announcement')} or @data-announcement]")
        announcement = _node_text(announcement_node) or None
        canteens.append(
            CanteenMenu(
                name=canteen_name,
                items=tuple(items),
                opens_at=opens_at,
                closes_at=closes_at,
                announcement=announcement,
            )
        )
    if not canteens:
        raise MenuParseError("no valid canteen sections were found")
    return MenuSnapshot(
        menu_date=menu_date,
        source_url=source_url,
        canteens=tuple(canteens),
        warnings=tuple(warnings),
    )
