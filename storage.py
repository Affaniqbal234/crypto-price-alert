import json
import sys


def load_watchlist(path: str = "watchlist.json") -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        print(f"Warning: {path} has malformed JSON ({exc}). Starting fresh.", file=sys.stderr)
        return []


def save_watchlist(watchlist: list[dict], path: str = "watchlist.json") -> None:
    # strip runtime-only fields before writing
    clean = [
        {"symbol": e["symbol"], "target_price": e.get("target_price")}
        for e in watchlist
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(clean, indent=2))
