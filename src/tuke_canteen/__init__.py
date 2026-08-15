"""Tools for exploring public TUKE canteen menus."""

from .client import DEFAULT_MENU_URL, MenuFetchError, fetch_menu
from .models import CanteenMenu, MenuItem, MenuSnapshot
from .parser import MenuParseError, parse_menu

__all__ = [
    "CanteenMenu",
    "DEFAULT_MENU_URL",
    "MenuFetchError",
    "MenuItem",
    "MenuParseError",
    "MenuSnapshot",
    "fetch_menu",
    "parse_menu",
]

__version__ = "1.0.0"

