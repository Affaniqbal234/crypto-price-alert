import json
import os
import sys
import tempfile

import pytest
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from storage import load_watchlist, save_watchlist


def test_missing_file_returns_empty(tmp_path):
    assert load_watchlist(str(tmp_path / "nope.json")) == []


def test_malformed_json_returns_empty_and_warns(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text("{not valid", encoding="utf-8")
    result = load_watchlist(str(p))
    assert result == []
    assert "Warning" in capsys.readouterr().err


def test_valid_file_loads_correctly(tmp_path):
    data = [{"symbol": "BTCUSDT", "target_price": 100000.0}]
    p = tmp_path / "watchlist.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    assert load_watchlist(str(p)) == data


def test_empty_array_file(tmp_path):
    p = tmp_path / "watchlist.json"
    p.write_text("[]", encoding="utf-8")
    assert load_watchlist(str(p)) == []


def test_save_persists_symbol_and_target(tmp_path):
    path = str(tmp_path / "w.json")
    save_watchlist([{"symbol": "ETHUSDT", "target_price": 3000.0}], path)
    assert json.load(open(path)) == [{"symbol": "ETHUSDT", "target_price": 3000.0}]


def test_save_strips_last_side(tmp_path):
    path = str(tmp_path / "w.json")
    save_watchlist([{"symbol": "BTCUSDT", "target_price": 50000.0, "last_side": "below"}], path)
    saved = json.load(open(path))
    assert "last_side" not in saved[0]


def test_save_null_target(tmp_path):
    path = str(tmp_path / "w.json")
    save_watchlist([{"symbol": "ADAUSDT", "target_price": None}], path)
    assert json.load(open(path)) == [{"symbol": "ADAUSDT", "target_price": None}]


def test_save_empty_list(tmp_path):
    path = str(tmp_path / "w.json")
    save_watchlist([], path)
    assert json.load(open(path)) == []


# save → load should give back exactly what you put in
@given(
    watchlist=st.lists(
        st.fixed_dictionaries({
            "symbol": st.text(min_size=1, max_size=20),
            "target_price": st.one_of(
                st.none(),
                st.floats(min_value=0.01, allow_nan=False, allow_infinity=False),
            ),
        }),
        max_size=20,
    )
)
@settings(max_examples=200)
def test_round_trip(watchlist):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "w.json")
        save_watchlist(watchlist, path)
        assert load_watchlist(path) == watchlist
