#!/usr/bin/env python3
"""
Live debug script: dumps the raw Spotify API response for a playlist so you
can see exactly what the API is returning before any filtering is applied.

Usage:
    python scripts/debug_playlist.py <playlist_url_or_id>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow imports from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth           import get_spotify_client
from src.spotify_client import parse_playlist_id, fetch_playlist_tracks


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_playlist.py <playlist_url_or_id>")
        sys.exit(1)

    raw = sys.argv[1]
    playlist_id = parse_playlist_id(raw)

    if not playlist_id:
        print(f"ERROR: could not parse a playlist ID from: {raw!r}")
        sys.exit(1)

    print(f"Parsed playlist ID : {playlist_id}")

    sp   = get_spotify_client()
    user = sp.current_user()
    print(f"Authenticated as   : {user['display_name']} ({user['id']})\n")

    # ── Raw API response ────────────────────────────────────────────────────
    print("── raw playlist_items() — first page ──────────────────────────────")
    raw_result = sp.playlist_items(
        playlist_id,
        additional_types=["track"],
        market="from_token",
    )

    items = raw_result.get("items", [])
    print(f"Items on first page : {len(items)}")
    print(f"Has next page       : {bool(raw_result.get('next'))}\n")

    for i, item in enumerate(items[:3]):
        print(f"Item {i}:")
        print(json.dumps(item, indent=2, default=str))
        print()

    if not items:
        print("WARNING: The API returned zero items on the first page.")
        return

    # Show what fields are present on the first track
    first_track = items[0].get("track") or {}
    print("── Fields present on items[0]['track'] ────────────────────────────")
    print(list(first_track.keys()))
    print(f"  type field value : {first_track.get('type', '<NOT PRESENT>')}\n")

    # ── fetch_playlist_tracks result ────────────────────────────────────────
    print("── fetch_playlist_tracks() result ─────────────────────────────────")
    name, tracks = fetch_playlist_tracks(sp, playlist_id)
    print(f"Playlist name : {name!r}")
    print(f"Tracks kept   : {len(tracks)}")
    for t in tracks[:5]:
        print(f"  {t['id']}  {t['name']!r}  by {t['artist']!r}")


if __name__ == "__main__":
    main()
