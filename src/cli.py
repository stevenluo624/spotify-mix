"""
Terminal UI built on Rich (display) + Questionary (interactive prompts).

questionary is used in place of inquirer — it is actively maintained,
handles all terminals correctly, and supports the same features.
"""

from __future__ import annotations

import questionary
from questionary import Style as QStyle

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich         import box
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

_Q_STYLE = QStyle(
    [
        ("qmark",       "fg:#00c853 bold"),
        ("question",    "bold"),
        ("answer",      "fg:#00c853 bold"),
        ("pointer",     "fg:#00c853 bold"),
        ("highlighted", "fg:#00c853 bold"),
        ("selected",    "fg:#00c853"),
    ]
)

_MIX_OPTIONS: list[tuple[str, str]] = [
    (
        "Consistent Vibe   — Minimise BPM variance for a seamless, steady groove",
        "consistent",
    ),
    (
        "Slow Build-Up     — Start mellow, steadily climb to peak energy",
        "buildup",
    ),
    (
        "Sectioned / Wave  — Low → Mid → High energy blocks with harmonic flow",
        "sectioned",
    ),
]

STYLE_NAMES: dict[str, str] = {
    "consistent": "Consistent Vibe",
    "buildup":    "Slow Build-Up",
    "sectioned":  "Sectioned Wave",
}

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def print_banner() -> None:
    title = Text("  Spotify Mix  ", style="bold green", justify="center")
    console.print(
        Panel(
            title,
            subtitle="[dim]Harmonic DJ Mix Generator[/dim]",
            border_style="green",
            padding=(0, 4),
        )
    )
    console.print()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def prompt_playlist_url() -> str | None:
    """Ask for a playlist URL/URI/ID. Returns None if the user quits."""
    return questionary.text(
        "Enter a Spotify playlist URL, URI, or ID:",
        validate=lambda v: bool(v.strip()) or "Please enter a value",
        style=_Q_STYLE,
    ).ask()


def prompt_mix_style() -> str | None:
    """
    Present the three energy-flow options.
    Returns the style key string, or None if the user cancels.
    """
    labels  = [label for label, _ in _MIX_OPTIONS]
    key_map = {label: key for label, key in _MIX_OPTIONS}

    choice = questionary.select(
        "How do you want to structure the energy of this mix?",
        choices=labels,
        style=_Q_STYLE,
    ).ask()

    return key_map.get(choice) if choice else None


def prompt_confirm(message: str) -> bool:
    result = questionary.confirm(message, style=_Q_STYLE).ask()
    return bool(result)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_track_table(tracks: list[dict], style_name: str) -> None:
    """Render the reordered track list as a Rich table."""
    table = Table(
        title=f"[bold green]Mix Order — {style_name}[/bold green]",
        box=box.ROUNDED,
        header_style="bold magenta",
        border_style="green",
        show_lines=False,
    )

    table.add_column("#",        style="dim",    width=4,  justify="right")
    table.add_column("Track",    style="white",  min_width=32)
    table.add_column("Artist",   style="cyan",   min_width=20)
    table.add_column("BPM",      style="yellow", width=8,  justify="right")
    table.add_column("Camelot",  style="green",  width=9,  justify="center")
    table.add_column("Energy",   style="dim",    width=8,  justify="left")

    for i, track in enumerate(tracks, 1):
        camelot = f"{track['camelot_num']}{track['camelot_letter']}"
        table.add_row(
            str(i),
            track["name"][:40],
            track["artist"][:25],
            f"{track['tempo']:.1f}",
            camelot,
            _energy_bar(track.get("energy", 0.5)),
        )

    console.print(table)


def _energy_bar(energy: float, width: int = 7) -> str:
    filled = round(energy * width)
    bar    = "█" * filled + "░" * (width - filled)
    if energy >= 0.7:
        return f"[bold red]{bar}[/bold red]"
    elif energy >= 0.4:
        return f"[yellow]{bar}[/yellow]"
    else:
        return f"[dim]{bar}[/dim]"


def print_success(playlist_url: str, name: str) -> None:
    console.print(
        f"\n[bold green]✓ Playlist created:[/bold green] [white]{name}[/white]"
    )
    console.print(
        f"[bold green]  Open in Spotify:[/bold green] "
        f"[underline cyan]{playlist_url}[/underline cyan]\n"
    )


def print_error(message: str) -> None:
    console.print(f"\n[bold red]✗ Error:[/bold red] {message}\n")


def spinner(description: str) -> Progress:
    """Return a transient Rich Progress spinner context-manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn(f"[cyan]{description}[/cyan]"),
        transient=True,
        console=console,
    )
