import os
import re
import sys

from hypothesis import given, settings, strategies as st
from rich.text import Text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ui import build_alerts_panel, build_price_table, format_change, format_price


def test_format_price_basic():
    assert format_price(108500.0) == "$108500.00"


def test_format_price_zero():
    assert format_price(0.0) == "$0.00"


def test_format_price_rounds_to_two_decimals():
    assert format_price(1.5) == "$1.50"


def test_format_change_positive_is_green():
    text = format_change(2.5)
    assert any("green" in str(s.style) for s in text._spans)


def test_format_change_negative_is_red():
    text = format_change(-1.0)
    assert any("red" in str(s.style) for s in text._spans)


def test_format_change_zero_has_no_style():
    text = format_change(0.0)
    assert len(text._spans) == 0


def test_alerts_panel_none_when_no_targets():
    watchlist = [{"symbol": "BTCUSDT", "target_price": None}]
    assert build_alerts_panel([], watchlist) is None


def test_alerts_panel_none_for_empty_watchlist():
    assert build_alerts_panel([], []) is None


def test_alerts_panel_exists_when_target_set():
    watchlist = [{"symbol": "BTCUSDT", "target_price": 50000.0}]
    assert build_alerts_panel([], watchlist) is not None


def test_price_table_empty_watchlist_shows_hint():
    table = build_price_table([], {}, [])
    assert len(table.columns) == 4
    assert table.row_count == 1  # the "no coins yet" hint row


def test_price_table_has_four_columns():
    watchlist = [{"symbol": "BTCUSDT", "target_price": None}]
    prices = {"BTCUSDT": {"price": 50000.0, "change_pct": 1.5}}
    assert len(build_price_table(watchlist, prices, []).columns) == 4


def test_price_table_one_row_per_coin():
    watchlist = [
        {"symbol": "BTCUSDT", "target_price": None},
        {"symbol": "ETHUSDT", "target_price": None},
    ]
    prices = {
        "BTCUSDT": {"price": 50000.0, "change_pct": 1.0},
        "ETHUSDT": {"price": 3000.0, "change_pct": -0.5},
    }
    assert build_price_table(watchlist, prices, []).row_count == 2


@given(value=st.floats(min_value=0, max_value=1e12, allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_price_always_dollar_two_decimals(value):
    result = format_price(value)
    assert result.startswith("$")
    assert re.match(r"^\$\d+\.\d{2}$", result)


@given(pct=st.floats(allow_nan=False, allow_infinity=False))
@settings(max_examples=200)
def test_change_colour_matches_sign(pct):
    text = format_change(pct)
    assert isinstance(text, Text)
    if pct > 0:
        assert any("green" in str(s.style) for s in text._spans)
    elif pct < 0:
        assert any("red" in str(s.style) for s in text._spans)
    else:
        assert len(text._spans) == 0


@given(
    symbols=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu",))),
        min_size=1, max_size=10, unique=True,
    ),
    price_vals=st.lists(
        st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False),
        min_size=1, max_size=10,
    ),
)
@settings(max_examples=100)
def test_table_always_four_columns_one_row_per_coin(symbols, price_vals):
    n = min(len(symbols), len(price_vals))
    symbols, price_vals = symbols[:n], price_vals[:n]
    watchlist = [{"symbol": s, "target_price": None} for s in symbols]
    prices = {s: {"price": p, "change_pct": 0.0} for s, p in zip(symbols, price_vals)}
    table = build_price_table(watchlist, prices, [])
    assert len(table.columns) == 4
    assert table.row_count == len(watchlist)
