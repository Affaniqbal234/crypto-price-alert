import os
import sys

from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import check_alerts


def prices(symbol, price):
    return {symbol: {"price": price, "change_pct": 0.0}}


def test_empty_watchlist():
    assert check_alerts([], {}) == []


def test_no_target_no_alert():
    wl = [{"symbol": "BTCUSDT", "target_price": None}]
    assert check_alerts(wl, prices("BTCUSDT", 50000.0)) == []


def test_first_tick_sets_side_no_alert():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0}]
    result = check_alerts(wl, prices("BTCUSDT", 55000.0))
    assert result == []
    assert wl[0]["last_side"] == "above"


def test_no_alert_when_staying_above():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "above"}]
    assert check_alerts(wl, prices("BTCUSDT", 55000.0)) == []


def test_no_alert_when_staying_below():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}]
    assert check_alerts(wl, prices("BTCUSDT", 45000.0)) == []


def test_alert_crosses_below_to_above():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}]
    result = check_alerts(wl, prices("BTCUSDT", 50001.0))
    assert len(result) == 1
    assert result[0]["direction"] == "above"
    assert result[0]["current_price"] == 50001.0


def test_alert_crosses_above_to_below():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "above"}]
    result = check_alerts(wl, prices("BTCUSDT", 49999.0))
    assert len(result) == 1
    assert result[0]["direction"] == "below"


def test_alert_at_exact_target():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}]
    result = check_alerts(wl, prices("BTCUSDT", 50000.0))
    assert len(result) == 1
    assert result[0]["direction"] == "above"


def test_last_side_updated_after_cross():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}]
    check_alerts(wl, prices("BTCUSDT", 51000.0))
    assert wl[0]["last_side"] == "above"


def test_missing_price_data_skipped():
    wl = [{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}]
    assert check_alerts(wl, {}) == []


def test_multiple_coins_independent():
    wl = [
        {"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"},
        {"symbol": "ETHUSDT", "target_price": 3000.0, "last_side": "above"},
    ]
    result = check_alerts(wl, {
        "BTCUSDT": {"price": 51000.0, "change_pct": 0.0},  # crosses → alert
        "ETHUSDT": {"price": 3100.0, "change_pct": 0.0},   # stays above → no alert
    })
    assert len(result) == 1
    assert result[0]["symbol"] == "BTCUSDT"


@given(
    target=st.floats(min_value=1.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    offset=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_crossing_always_fires_alert(target, offset):
    price_above = target + offset
    price_below = max(target - offset, 0.001)

    entry = {"symbol": "TEST", "target_price": target, "last_side": "below"}
    result = check_alerts([entry], {"TEST": {"price": price_above, "change_pct": 0.0}})
    assert len(result) == 1 and result[0]["direction"] == "above"

    entry = {"symbol": "TEST", "target_price": target, "last_side": "above"}
    result = check_alerts([entry], {"TEST": {"price": price_below, "change_pct": 0.0}})
    assert len(result) == 1 and result[0]["direction"] == "below"
