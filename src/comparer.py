import json
from rapidfuzz import fuzz, process
from rich.console import Console
from rich.table import Table

console = Console()

def load_competitors(path="data/sample_competitors.json"):
    """Load competitor lists from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def find_conflicts(portfolio_names, competitor_data, threshold=85, debug=True):
    """Compare scraped company/portfolio names against a competitor list with colorized table output."""
    direct_hits = []
    adjacent_hits = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Portfolio Name", style="bold cyan")
    table.add_column("Direct Match", justify="center")
    table.add_column("Score (Direct)", justify="center")
    table.add_column("Adjacent Match", justify="center")
    table.add_column("Score (Adj)", justify="center")

    for name in portfolio_names:
        result_direct = process.extractOne(name, competitor_data["direct"], scorer=fuzz.ratio)
        if result_direct:
            match_direct, score_d, _ = result_direct
        else:
            match_direct, score_d = None, 0

        result_adj = process.extractOne(name, competitor_data["adjacent"], scorer=fuzz.ratio)
        if result_adj:
            match_adj, score_a, _ = result_adj
        else:
            match_adj, score_a = None, 0

        if score_d >= threshold:
            direct_hits.append(match_direct)
        elif score_a >= threshold:
            adjacent_hits.append(match_adj)

        table.add_row(
            name,
            str(match_direct or "-"),
            f"{score_d:.1f}",
            str(match_adj or "-"),
            f"{score_a:.1f}"
        )

    console.print(table)
    console.print(f"\n[bold yellow][SUMMARY][/bold yellow] Threshold: {threshold}")
    console.print(f"[bold red]Direct Conflicts:[/bold red] {len(direct_hits)}")
    console.print(f"[bold yellow]Adjacent Conflicts:[/bold yellow] {len(adjacent_hits)}")
    console.print(f"[bold green]Clean:[/bold green] {len(portfolio_names) - len(direct_hits) - len(adjacent_hits)}\n")

    return direct_hits, adjacent_hits