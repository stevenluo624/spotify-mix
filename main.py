"""
Spotify Mix — Harmonic DJ Mix Playlist Generator
=================================================
Usage:  python main.py

Workflow
--------
1. Authenticate with Spotify OAuth
2. Prompt for a playlist URL / URI / ID
3. Fetch tracks and their audio features
4. Map keys to the Camelot Wheel
5. Let the user choose an energy-flow style
6. Run the corresponding mixing algorithm
7. Print the mix order table
8. Create a new private playlist on Spotify
"""

from __future__ import annotations

import sys

from src.auth           import get_spotify_client
from src.spotify_client import parse_playlist_id, fetch_playlist_tracks, fetch_audio_features, create_playlist
from src.camelot        import get_camelot, camelot_to_str
from src.mixing         import mix_consistent, mix_build_up, mix_sectioned
from src.cli            import (
    console,
    print_banner,
    prompt_playlist_url,
    prompt_mix_style,
    prompt_confirm,
    print_track_table,
    print_success,
    print_error,
    spinner,
    STYLE_NAMES,
)

MIX_FUNCTIONS = {
    "consistent": mix_consistent,
    "buildup":    mix_build_up,
    "sectioned":  mix_sectioned,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enrich_camelot(tracks: list[dict]) -> list[dict]:
    """Attach camelot_num, camelot_letter, and camelot_str to every track."""
    for track in tracks:
        num, letter = get_camelot(track["key"], track["mode"])
        track["camelot_num"]    = num
        track["camelot_letter"] = letter
        track["camelot_str"]    = camelot_to_str(num, letter)
    return tracks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print_banner()

    # ── 1. Authenticate ────────────────────────────────────────────────────
    try:
        with spinner("Connecting to Spotify…") as p:
            p.add_task("")
            sp   = get_spotify_client()
            user = sp.current_user()
    except EnvironmentError as exc:
        print_error(str(exc))
        sys.exit(1)
    except Exception as exc:
        print_error(f"Authentication failed: {exc}")
        sys.exit(1)

    console.print(
        f"[green]✓[/green] Signed in as "
        f"[bold]{user['display_name']}[/bold] "
        f"([dim]{user['id']}[/dim])\n"
    )

    # ── 2. Fetch playlist ──────────────────────────────────────────────────
    playlist_name: str = ""
    tracks: list[dict] = []

    while True:
        raw = prompt_playlist_url()
        if raw is None:          # user hit Ctrl-C
            sys.exit(0)

        playlist_id = parse_playlist_id(raw)
        if not playlist_id:
            print_error(
                "Could not parse that as a Spotify playlist URL, URI, or ID.\n"
                "  • URL  → https://open.spotify.com/playlist/<id>\n"
                "  • URI  → spotify:playlist:<id>\n"
                "  • ID   → 22-character alphanumeric string"
            )
            continue

        try:
            with spinner("Fetching playlist…") as p:
                p.add_task("")
                playlist_name, tracks = fetch_playlist_tracks(sp, playlist_id)
        except Exception as exc:
            print_error(f"Could not fetch playlist: {exc}")
            if not prompt_confirm("Try a different playlist?"):
                sys.exit(0)
            continue

        if not tracks:
            print_error("The playlist is empty or contains no playable tracks.")
            if not prompt_confirm("Try a different playlist?"):
                sys.exit(0)
            continue

        console.print(
            f"[green]✓[/green] Found [bold]{len(tracks)}[/bold] tracks "
            f"in [bold]\"{playlist_name}\"[/bold]\n"
        )
        break

    # ── 3. Audio features ──────────────────────────────────────────────────
    with spinner("Analysing audio features…") as p:
        p.add_task("")
        tracks = fetch_audio_features(sp, tracks)

    # ── 4. Camelot mapping ─────────────────────────────────────────────────
    tracks = _enrich_camelot(tracks)

    # ── 5. Choose mix style ────────────────────────────────────────────────
    style = prompt_mix_style()
    if style is None:
        sys.exit(0)

    style_name = STYLE_NAMES[style]

    # ── 6. Run mixing algorithm ────────────────────────────────────────────
    with spinner(f"Computing {style_name} mix…") as p:
        p.add_task("")
        ordered = MIX_FUNCTIONS[style](tracks)

    # ── 7. Display results ─────────────────────────────────────────────────
    console.print()
    print_track_table(ordered, style_name)

    # ── 8. Create playlist ─────────────────────────────────────────────────
    new_name = f"{playlist_name} — {style_name} Mix"

    if not prompt_confirm(f'\nCreate "{new_name}" on your Spotify account?'):
        console.print("[dim]No playlist created. Goodbye.[/dim]\n")
        sys.exit(0)

    try:
        with spinner("Creating playlist…") as p:
            p.add_task("")
            url = create_playlist(
                sp,
                user["id"],
                new_name,
                [t["id"] for t in ordered],
            )
        print_success(url, new_name)
    except Exception as exc:
        print_error(f"Failed to create playlist: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
