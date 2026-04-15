"""
Spotify OAuth authentication.

Reads credentials from the .env file and returns an authenticated
spotipy.Spotify client. A token cache is written to .spotify_cache so
subsequent runs skip the browser login.
"""

from __future__ import annotations

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
]


def get_spotify_client() -> spotipy.Spotify:
    """
    Authenticate via Spotify OAuth and return an authorised Spotify client.

    Raises
    ------
    EnvironmentError
        If SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET are not set in the
        environment / .env file.
    """
    client_id     = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri  = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "Missing Spotify credentials.\n"
            "Please create a .env file (copy from .env.example) and set:\n"
            "  SPOTIFY_CLIENT_ID=<your client id>\n"
            "  SPOTIFY_CLIENT_SECRET=<your client secret>"
        )

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=" ".join(SCOPES),
        cache_path=".spotify_cache",
        open_browser=True,
    )

    return spotipy.Spotify(auth_manager=auth_manager)
