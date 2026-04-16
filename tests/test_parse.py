"""Tests for playlist URL / URI / ID parsing."""

import pytest
from src.spotify_client import parse_playlist_id

VALID_ID = "37i9dQZF1DXcBWIGoYBM5M"


@pytest.mark.parametrize("raw", [
    f"https://open.spotify.com/playlist/{VALID_ID}",
    f"https://open.spotify.com/playlist/{VALID_ID}?si=abc123",
    f"spotify:playlist:{VALID_ID}",
    VALID_ID,
    f"  {VALID_ID}  ",   # leading/trailing whitespace
])
def test_valid_inputs(raw):
    assert parse_playlist_id(raw) == VALID_ID


@pytest.mark.parametrize("raw", [
    "",
    "not-a-playlist",
    "https://open.spotify.com/track/37i9dQZF1DXcBWIGoYBM5M",   # track URL, not playlist
    "spotify:track:37i9dQZF1DXcBWIGoYBM5M",
    "12345",
])
def test_invalid_inputs(raw):
    assert parse_playlist_id(raw) is None
