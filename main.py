"""
main.py — CLI entry point for the Crypto Price Alert Tool.

Subcommands:
  add <SYMBOL> [--target PRICE]  — add a coin to the watchlist
  remove <SYMBOL>                — remove a coin from the watchlist
  start [--interval SECONDS]     — launch the auto-refreshing dashboard
"""

import argparse
import time
from datetime import datetime

import requests
from rich.live import Live

from api import fetch_prices
from storage import load_watchlist, save_watchlist
from ui import build_dashboard, console, ring_bell


# ---------------------------------------------------------------------------
# Alert detection
# ---------------------------------------------------------------------------

def check_alerts(watchlist: list[dict], prices: dict[str, dict]) -> list[dict]:
    """
    Direction-aware crossing detection (Requirements 6.1, 6.2).

    For each watchlist entry that has a target_price set:
      - Determines the current side ("above" or "below") relative to target.
      - Fires an alert only when the side has *changed* from the last tick
        (i.e. the price has crossed the target).
      - Mutates `last_side` on each entry in-place so the next call can
        compare against the new side.

    Returns a list of alert dicts:
        {"symbol": str, "target_price": float, "current_price": float, "direction": str}
    where `direction` is "above" (price rose to/above target) or
    "below" (price fell to/below target).
    """
    triggered: list[dict] = []

    for entry in watchlist:
        target = entry.get("target_price")
        if target is None:
            continue

        symbol = entry["symbol"]
        price_data = prices.get(symbol)
        if price_data is None:
            continue

        current_price: float = price_data["price"]
        current_side = "above" if current_price >= target else "below"
        last_side = entry.get("last_side")

        # Fire alert only on a side change (crossing), not on every tick
        if last_side is not None and current_side != last_side:
            triggered.append({
                "symbol": symbol,
                "target_price": target,
                "current_price": current_price,
                "direction": current_side,
            })

        # Always update last_side in-place
        entry["last_side"] = current_side

    return triggered


# ---------------------------------------------------------------------------
# Dashboard loop
# ---------------------------------------------------------------------------

def run_dashboard(watchlist: list[dict], interval: int = 10) -> None:
    """
    Auto-refreshing dashboard using rich.live.Live (Requirements 5.1, 5.2, 7.1–7.4).

    - Fetches prices every `interval` seconds.
    - Catches HTTPError, ConnectionError, Timeout and shows inline error message.
    - Calls ring_bell() for each triggered alert.
    - Exits cleanly on KeyboardInterrupt (no traceback).
    """
    prices: dict[str, dict] = {}
    alerts: list[dict] = []
    error_msg: str | None = None
    last_updated = "—"

    try:
        with Live(console=console, refresh_per_second=4, screen=True) as live:
            while True:
                symbols = [entry["symbol"] for entry in watchlist]
                error_msg = None

                if symbols:
                    try:
                        prices = fetch_prices(symbols)
                        alerts = check_alerts(watchlist, prices)
                        for _ in alerts:
                            ring_bell()
                    except requests.HTTPError as exc:
                        error_msg = f"API error: {exc}"
                    except requests.Timeout:
                        error_msg = "Connection timeout — retrying next cycle"
                    except requests.ConnectionError:
                        error_msg = "Connection timeout — retrying next cycle"
                    except ValueError as exc:
                        error_msg = f"Unexpected API response: {exc}"

                last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                renderable = build_dashboard(watchlist, prices, alerts, last_updated, error_msg)
                live.update(renderable)

                time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")


# ---------------------------------------------------------------------------
# Watchlist management helpers
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace) -> None:
    """Add a coin to the watchlist (Req 1.1, 1.3, 1.5)."""
    symbol = args.symbol.upper()
    target = args.target

    watchlist = load_watchlist()

    # Check for duplicate (Req 1.3)
    for entry in watchlist:
        if entry["symbol"] == symbol:
            print(f"'{symbol}' is already in your watchlist — skipping.")
            return

    entry: dict = {"symbol": symbol, "target_price": target}
    watchlist.append(entry)
    save_watchlist(watchlist)

    msg = f"Added {symbol}"
    if target is not None:
        msg += f" with target ${target:.2f}"
    print(msg)


def cmd_remove(args: argparse.Namespace) -> None:
    """Remove a coin from the watchlist (Req 1.2, 1.4)."""
    symbol = args.symbol.upper()

    watchlist = load_watchlist()

    original_len = len(watchlist)
    watchlist = [e for e in watchlist if e["symbol"] != symbol]

    if len(watchlist) == original_len:
        print(f"'{symbol}' is not in your watchlist.")
        return

    save_watchlist(watchlist)
    print(f"Removed {symbol}")


def cmd_start(args: argparse.Namespace) -> None:
    """Launch the auto-refreshing dashboard (Req 5.1)."""
    watchlist = load_watchlist()
    run_dashboard(watchlist, args.interval)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crypto-alert",
        description="Terminal-based cryptocurrency price alert tool.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- add ---
    add_parser = subparsers.add_parser("add", help="Add a coin to the watchlist")
    add_parser.add_argument("symbol", metavar="SYMBOL", help="Binance trading pair, e.g. BTCUSDT")
    add_parser.add_argument(
        "--target",
        metavar="PRICE",
        type=float,
        default=None,
        help="Optional alert target price in USD",
    )
    add_parser.set_defaults(func=cmd_add)

    # --- remove ---
    remove_parser = subparsers.add_parser("remove", help="Remove a coin from the watchlist")
    remove_parser.add_argument("symbol", metavar="SYMBOL", help="Binance trading pair to remove")
    remove_parser.set_defaults(func=cmd_remove)

    # --- start ---
    start_parser = subparsers.add_parser("start", help="Launch the auto-refreshing dashboard")
    start_parser.add_argument(
        "--interval",
        metavar="SECONDS",
        type=int,
        default=10,
        help="Refresh interval in seconds (default: 10)",
    )
    start_parser.set_defaults(func=cmd_start)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
