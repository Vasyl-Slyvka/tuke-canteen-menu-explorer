# Parsing strategy

The public TUKE menu is server-rendered HTML. The parser intentionally uses
two narrow strategies instead of a broad collection of fragile text guesses.

## Current TUKE layout

The primary strategy follows the public structure validated on 16 August 2026:

- `.jedalen-small` or `.jedalen-full` identifies a canteen;
- `.group` identifies a food category;
- `.row.has_popup` identifies a menu item;
- `.data.col-xs-10` contains the name and allergen markup;
- `.data.col-xs-2` contains the price;
- `.alergens abbr` contains official numeric allergen identifiers.

The name extractor ignores text inside the allergen node. This prevents a meal
such as `Kuracie prsia 120g` with allergens `1, 7` from becoming
`Kuracie prsia 120g 1, 7`.

## Semantic fallback

For moderate layout changes, the parser also recognizes containers and fields
with semantic attributes such as `data-canteen`, `data-category`, `data-name`,
`data-price`, and `data-allergens`, plus common `canteen`, `menu-item`, `name`,
and `price` classes. The fallback is covered by a separate fixture.

It is not designed to guess arbitrary page structures. If neither strategy can
identify a menu, the library raises `MenuParseError` instead of returning an
incorrect empty result.

## Operational boundaries

- Network access is separate from parsing and has a timeout and response limit.
- Tests use local fixtures and do not depend on TUKE availability.
- Live requests read public menu pages only.
- Login, cookies, ordering, and personal data are outside the project scope.

