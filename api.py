import json
import requests

_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"


def fetch_prices(symbols: list[str]) -> dict[str, dict]:
    """Returns {symbol: {"price": float, "change_pct": float}} for each symbol."""
    response = requests.get(
        _TICKER_URL,
        params={"symbols": json.dumps(symbols, separators=(",", ":"))},
        timeout=10,
    )
    response.raise_for_status()

    result = {}
    for ticker in response.json():
        symbol = ticker.get("symbol", "<unknown>")
        if "lastPrice" not in ticker:
            raise ValueError(f"Missing 'lastPrice' in Binance response for {symbol}")
        if "priceChangePercent" not in ticker:
            raise ValueError(f"Missing 'priceChangePercent' in Binance response for {symbol}")
        result[symbol] = {
            "price": float(ticker["lastPrice"]),
            "change_pct": float(ticker["priceChangePercent"]),
        }

    return result
