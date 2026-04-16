"""
Spotify API interactions: parse URLs, fetch tracks & audio features,
and create the final reordered playlist.
"""

from __future__ import annotations

import re
import spotipy


# ---------------------------------------------------------------------------
# URL / URI parsing
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)")
_URI_PATTERN = re.compile(r"^spotify:playlist:([A-Za-z0-9]+)$")
_ID_PATTERN  = re.compile(r"^[A-Za-z0-9]{22}$")


def parse_playlist_id(raw: str) -> str | None:
    """
    Extract the playlist ID from any of the common Spotify input formats:

      • https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=...
      • spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
      • 37i9dQZF1DXcBWIGoYBM5M   (bare 22-char ID)

    Returns None if the input cannot be parsed.
    """
    raw = raw.strip()

    m = _URL_PATTERN.search(raw)
    if m:
        return m.group(1)

    m = _URI_PATTERN.match(raw)
    if m:
        return m.group(1)

    if _ID_PATTERN.match(raw):
        return raw

    return None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_playlist_tracks(
    sp: spotipy.Spotify,
    playlist_id: str,
) -> tuple[str, list[dict]]:
    """
    Return (playlist_name, tracks) where each track dict contains:
      id, name, artist
    Handles pagination transparently.
    Skips local files and any items without a valid track ID.
    """
    meta = sp.playlist(playlist_id, fields="name")
    playlist_name: str = meta["name"]

    tracks: list[dict] = []
    results = sp.playlist_items(
        playlist_id,
        additional_types=["track"],
        market="from_token",
    )

    while results:
        for item in results.get("items", []):
            # playlist_items() puts the track object under "item";
            # fall back to "track" for any older response shapes.
            track = item.get("item") or item.get("track")
            if not track or not track.get("id") or track.get("type") == "episode":
                continue
            tracks.append(
                {
                    "id":     track["id"],
                    "name":   track["name"],
                    "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown",
                }
            )
        results = sp.next(results) if results.get("next") else None

    return playlist_name, tracks


def fetch_audio_features(
    sp: spotipy.Spotify,
    tracks: list[dict],
) -> list[dict]:
    """
    Enrich each track dict in-place with audio features:
      tempo, key, mode, energy, valence

    Fetches in batches of 100 (Spotify API limit).
    Falls back to safe defaults when features are unavailable.
    """
    ids = [t["id"] for t in tracks]
    feature_map: dict[str, dict] = {}

    for i in range(0, len(ids), 100):
        batch   = ids[i : i + 100]
        results = sp.audio_features(batch)
        for feat in results:
            if feat:
                feature_map[feat["id"]] = feat

    enriched: list[dict] = []
    for track in tracks:
        feat = feature_map.get(track["id"])
        if feat:
            enriched.append(
                {
                    **track,
                    "tempo":   round(feat["tempo"], 1),
                    "key":     feat["key"],    # 0–11 or -1 if unknown
                    "mode":    feat["mode"],   # 0=minor, 1=major
                    "energy":  feat["energy"],
                    "valence": feat["valence"],
                }
            )
        else:
            # Missing features — neutral defaults so the track still participates
            enriched.append(
                {
                    **track,
                    "tempo":   120.0,
                    "key":     -1,
                    "mode":    1,
                    "energy":  0.5,
                    "valence": 0.5,
                }
            )

    return enriched


# ---------------------------------------------------------------------------
# Playlist creation
# ---------------------------------------------------------------------------

def create_playlist(
    sp: spotipy.Spotify,
    user_id: str,
    name: str,
    track_ids: list[str],
    description: str = "Created by Spotify Mix — harmonic DJ mix tool",
) -> str:
    """
    Create a private playlist called *name* for *user_id*, populate it with
    *track_ids* (in order, batched at 100), and return the Spotify URL.
    """
    playlist = sp.user_playlist_create(
        user=user_id,
        name=name,
        public=False,
        description=description,
    )
    playlist_id = playlist["id"]

    for i in range(0, len(track_ids), 100):
        sp.playlist_add_items(playlist_id, track_ids[i : i + 100])

    return playlist["external_urls"]["spotify"]
