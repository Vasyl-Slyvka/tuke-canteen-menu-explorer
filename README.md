# TUKE Canteen Menu Explorer

[![CI](https://github.com/Vasyl-Slyvka/tuke-canteen-menu-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/Vasyl-Slyvka/tuke-canteen-menu-explorer/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A tested Python library and CLI for reading, filtering, and exporting the
public [TUKE canteen menu](https://jedalen.tuke.sk/jedalny-listok).

This portfolio edition grew from a small parsing exercise into a complete,
fail-closed data pipeline. It separates network access from HTML parsing,
supports the current TUKE page structure plus a semantic fallback, and remains
fully testable without internet access.

## Highlights

- parses multiple canteens, categories, prices, opening hours, announcements,
  and official allergen IDs;
- handles decimal-comma euro prices and removes allergen markup from meal names;
- filters by canteen, category, maximum price, excluded allergens, and text;
- exports stable terminal, JSON, and CSV representations;
- enforces HTTP timeout and response-size limits with controlled error messages;
- uses offline HTML fixtures, so CI does not depend on TUKE availability;
- includes a semantic fallback for moderate page-layout changes;
- runs CI on Python 3.10, 3.11, 3.12, and 3.13.

## Installation

```bash
git clone https://github.com/Vasyl-Slyvka/tuke-canteen-menu-explorer.git
cd tuke-canteen-menu-explorer
python -m venv .venv
```

Activate the environment and install the package:

```bash
python -m pip install -e .
```

## Usage

Display the current public menu:

```bash
tuke-menu
```

Select a date and canteen, cap the price, and avoid allergens 1 and 7:

```bash
tuke-menu \
  --date 2026-08-17 \
  --canteen "Jedlikova" \
  --max-price 4.50 \
  --exclude-allergen 1 \
  --exclude-allergen 7
```

Export JSON or CSV:

```bash
tuke-menu --format json --output menu.json
tuke-menu --category "Polievky" --format csv --output soups.csv
```

Parse an offline HTML snapshot without a network request:

```bash
tuke-menu --input-html tests/fixtures/official_menu.html --format json
```

Run as a module if the console entry point is unavailable:

```bash
python -m tuke_canteen --help
```

## Python API

```python
from decimal import Decimal

from tuke_canteen import fetch_menu
from tuke_canteen.filtering import filter_items

snapshot = fetch_menu()
affordable = filter_items(
    snapshot,
    canteen="Jedlikova",
    max_price=Decimal("4.50"),
    exclude_allergens=(1, 7),
)

for item in affordable:
    print(item.name, item.price_eur)
```

## Reliability model

The parser was validated against the official public TUKE HTML structure on
16 August 2026. Website markup is an external dependency and can change. The
parser therefore raises a typed `MenuParseError` when it cannot recognize a
menu; it does not silently report an empty result as success.

See [Parsing strategy](docs/parsing-strategy.md) for selectors, fallback rules,
and access boundaries.

## Tests

```bash
python -m unittest discover -s tests -v
```

The test suite covers domain validation, current and fallback HTML layouts,
allergen extraction, filtering, network failures, size limits, all output
formats, and CLI behavior.

## Project layout

```text
src/tuke_canteen/       library, parser, client, filters, CLI, exporters
tests/                  unit tests and offline HTML fixtures
examples/               example JSON and CSV output
docs/                   parsing and resilience notes
.github/workflows/      Python 3.10-3.13 CI
```

## Scope and disclaimer

This is an independent educational project and is not affiliated with or
endorsed by the Technical University of Košice. It reads public menu pages
only. It does not log in, place orders, store cookies, or process personal
account data. Menu availability and prices remain authoritative only on the
official TUKE website.

## License

[MIT](LICENSE)

