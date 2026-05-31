from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def format_price(value: float) -> str:
    return f"${value:.2f}"


def format_change(pct: float) -> Text:
    text = Text(f"{pct:+.2f}%")
    if pct > 0:
        text.stylize("green")
    elif pct < 0:
        text.stylize("red")
    return text


def build_price_table(watchlist: list[dict], prices: dict[str, dict], alerts: list[dict]) -> Table:
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Symbol", style="bold", min_width=10)
    table.add_column("Price", min_width=14)
    table.add_column("24h Change", min_width=12)
    table.add_column("Alert Target", min_width=14)

    if not watchlist:
        table.add_row("[dim]No coins yet. Run: python main.py add BTCUSDT[/dim]", "", "", "")
        return table

    alerted = {a["symbol"] for a in alerts}

    for entry in watchlist:
        symbol = entry["symbol"]
        data = prices.get(symbol, {})
        price_str = format_price(data["price"]) if "price" in data else "N/A"
        change_text = format_change(data["change_pct"]) if "change_pct" in data else Text("N/A")
        target_str = format_price(entry["target_price"]) if entry.get("target_price") else "—"
        row_style = "on dark_red" if symbol in alerted else ""
        table.add_row(symbol, price_str, change_text, target_str, style=row_style)

    return table


def build_alerts_panel(alerts: list[dict], watchlist: list[dict]) -> Panel | None:
    if not any(e.get("target_price") for e in watchlist):
        return None

    if not alerts:
        return Panel(Text("No alerts triggered.", style="dim"),
                     title="[bold yellow]Alerts[/bold yellow]", border_style="yellow")

    lines = Text()
    for i, alert in enumerate(alerts):
        lines.append(f"  {alert['symbol']}", style="bold yellow")
        lines.append(f"  hit {format_price(alert['target_price'])} — "
                     f"now {format_price(alert['current_price'])} ({alert['direction']})\n")

    return Panel(lines, title="[bold red]⚠ Alerts[/bold red]", border_style="red")


def ring_bell() -> None:
    print("\a", end="", flush=True)


def build_dashboard(
    watchlist: list[dict],
    prices: dict[str, dict],
    alerts: list[dict],
    last_updated: str,
    error_msg: str | None = None,
) -> Group:
    parts = [
        Text("Crypto Price Alert Tool", style="bold cyan", justify="center"),
        Text("─" * console.width, style="dim"),
        build_price_table(watchlist, prices, alerts),
    ]

    panel = build_alerts_panel(alerts, watchlist)
    if panel:
        parts.append(panel)

    if error_msg:
        parts.append(Text(f"⚠  {error_msg}", style="bold red"))

    parts.append(Text(f"Last updated: {last_updated}", style="dim", justify="right"))

    return Group(*parts)
