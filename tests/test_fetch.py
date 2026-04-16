"""
Tests for fetch_playlist_tracks — covers the item-filtering logic
that was responsible for the 'no playable tracks' bug.
"""

from unittest.mock import MagicMock
from src.spotify_client import fetch_playlist_tracks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _track_item(track_id, name="Song", artist="Artist", type_="track", key="item"):
    """
    Build a playlist item dict as Spotify's API returns it.
    playlist_items() uses key="item"; the older playlist_tracks() used key="track".
    """
    return {
        key: {
            "id":      track_id,
            "name":    name,
            "type":    type_,
            "artists": [{"name": artist}],
        }
    }

def _make_sp(items, name="Test Playlist"):
    """Return a mock Spotify client that serves a single-page playlist."""
    sp = MagicMock()
    sp.playlist.return_value = {"name": name}
    sp.playlist_items.return_value = {"items": items, "next": None}
    return sp


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_normal_tracks_returned():
    items = [
        _track_item("id1", "Song A", "Artist A"),
        _track_item("id2", "Song B", "Artist B"),
    ]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert [t["id"] for t in tracks] == ["id1", "id2"]


def test_playlist_name_returned():
    sp = _make_sp([], name="My Chill Mix")
    name, _ = fetch_playlist_tracks(sp, "pid")
    assert name == "My Chill Mix"


# ---------------------------------------------------------------------------
# Filtering edge cases (these are the ones that caused the bug)
# ---------------------------------------------------------------------------

def test_item_key_used_by_playlist_items():
    """playlist_items() puts the track under 'item', not 'track'."""
    items = [_track_item("id1", key="item"), _track_item("id2", key="item")]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert [t["id"] for t in tracks] == ["id1", "id2"]


def test_track_key_fallback():
    """Fallback to 'track' key still works for older response shapes."""
    items = [_track_item("id1", key="track")]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert tracks[0]["id"] == "id1"


def test_null_track_skipped():
    """Spotify returns item=null for deleted or unavailable tracks."""
    items = [{"item": None}, _track_item("id1")]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert len(tracks) == 1
    assert tracks[0]["id"] == "id1"


def test_track_without_type_field_kept():
    """
    The type field is not guaranteed to be present.
    The previous bug: checking type != 'track' filtered these out.
    """
    item = {"item": {"id": "id1", "name": "Song", "artists": [{"name": "Artist"}]}}
    # Note: no 'type' key in the track dict
    sp = _make_sp([item])
    _, tracks = fetch_playlist_tracks(sp, "pid")
    assert len(tracks) == 1, "Track without type field should NOT be filtered"


def test_episode_skipped():
    """Podcast episodes in a playlist have type='episode'."""
    items = [
        _track_item("ep1", "Episode 1", "Some Podcast", type_="episode"),
        _track_item("id1", "Song A", "Artist A"),
    ]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert len(tracks) == 1
    assert tracks[0]["id"] == "id1"


def test_local_file_skipped():
    """Local files have no Spotify ID (id=None)."""
    items = [
        {"item": {"id": None, "name": "local.mp3", "type": "track", "artists": []}},
        _track_item("id1"),
    ]
    _, tracks = fetch_playlist_tracks(_make_sp(items), "pid")
    assert len(tracks) == 1


def test_empty_playlist():
    _, tracks = fetch_playlist_tracks(_make_sp([]), "pid")
    assert tracks == []


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def test_pagination_followed():
    """Results spanning two pages should both be collected."""
    page1 = {"items": [_track_item("id1")], "next": "cursor"}
    page2 = {"items": [_track_item("id2")], "next": None}

    sp = MagicMock()
    sp.playlist.return_value = {"name": "Test"}
    sp.playlist_items.return_value = page1
    sp.next.return_value = page2

    _, tracks = fetch_playlist_tracks(sp, "pid")
    assert [t["id"] for t in tracks] == ["id1", "id2"]
