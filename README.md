# Spotify Mix

A Python CLI tool that takes any Spotify playlist, analyses the audio features of every track, and reorders them into a perfectly sequenced DJ mix using harmonic key matching and BPM-aware algorithms. The result is saved as a new private playlist in your Spotify account.

## Features

- **Camelot Wheel harmonic mixing** — maps every track's key to the Camelot system and minimises dissonant key transitions
- **Three energy-flow styles** to choose from at runtime
- **Rich terminal UI** — spinner feedback, colour-coded energy bars, and a formatted mix-order table
- **Handles large playlists** — all Spotify API calls are paginated and batched

## Energy Flow Styles

| Style | Algorithm |
|---|---|
| **Consistent Vibe** | Greedy nearest-neighbour minimising combined BPM delta + harmonic distance at every step |
| **Slow Build-Up** | Global ascending BPM sort; within each 4-track bracket, greedy harmonic ordering for smooth micro-transitions |
| **Sectioned / Wave** | K-Means clusters tracks into Low → Mid → High energy blocks; greedy harmonic sort within each section |

## Requirements

- Python 3.10+
- A free [Spotify Developer](https://developer.spotify.com/dashboard) app (takes ~2 minutes to create)

## Installation

```bash
git clone https://github.com/your-username/spotify-mix.git
cd spotify-mix

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Spotify Developer Setup

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and sign in.
2. Click **Create app**. Give it any name and description.
3. Under **Redirect URIs** add: `http://localhost:8888/callback`
4. Tick the **Web API** checkbox and click **Save**.
5. Open **Settings** and copy your **Client ID** and **Client Secret**.

## Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

> `.env` and `.spotify_cache` are listed in `.gitignore` and will never be committed.

## Usage

```bash
python main.py
```

On the first run a browser window opens for Spotify OAuth. After approving access it redirects to `localhost:8888` — if your browser shows a "page not found", copy the full redirect URL from the address bar and paste it into the terminal. The token is cached in `.spotify_cache` for all subsequent runs.

**Accepted playlist input formats:**

```
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
37i9dQZF1DXcBWIGoYBM5M
```

## Sample Workflow

```
$ python main.py

  Spotify Mix
  Harmonic DJ Mix Generator

✓ Signed in as Jane Doe (janedoe)

? Enter a Spotify playlist URL, URI, or ID:
  https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

✓ Found 50 tracks in "All Out 2010s"

⠸ Analysing audio features…

? How do you want to structure the energy of this mix?
  ❯ Consistent Vibe   — Minimise BPM variance for a seamless, steady groove
    Slow Build-Up     — Start mellow, steadily climb to peak energy
    Sectioned / Wave  — Low → Mid → High energy blocks with harmonic flow

╭────────────────────────────────────────────────────────────────────────╮
│                    Mix Order — Consistent Vibe                         │
├────┬──────────────────────────────┬─────────────────┬───────┬─────┬────────┤
│  # │ Track                        │ Artist          │   BPM │ Key │ Energy │
├────┼──────────────────────────────┼─────────────────┼───────┼─────┼────────┤
│  1 │ Midnight City                │ M83             │ 105.0 │ 8B  │ ████░░░│
│  2 │ Do I Wanna Know?             │ Arctic Monkeys  │ 108.0 │ 7B  │ █████░░│
│  3 │ Somebody That I Used to Know │ Gotye           │ 109.0 │ 8A  │ █████░░│
│  4 │ Levels                       │ Avicii          │ 126.0 │ 9B  │ ███████│
│  … │ …                            │ …               │     … │  …  │      … │
╰────┴──────────────────────────────┴─────────────────┴───────┴─────┴────────╯

? Create "All Out 2010s — Consistent Vibe Mix" on your Spotify account? Yes

✓ Playlist created: All Out 2010s — Consistent Vibe Mix
  Open in Spotify: https://open.spotify.com/playlist/...
```

The Camelot key column lets you verify harmonic compatibility at a glance — adjacent numbers and matching letters are always smooth transitions.

## Project Structure

```
spotify-mix/
├── src/
│   ├── __init__.py
│   ├── auth.py            # Spotify OAuth (reads .env, caches token)
│   ├── camelot.py         # Camelot Wheel mapping and harmonic distance
│   ├── cli.py             # Rich table output + Questionary interactive prompts
│   ├── mixing.py          # Three mixing algorithms
│   └── spotify_client.py  # API calls: fetch tracks, audio features, create playlist
├── scripts/
│   └── run.sh             # Convenience wrapper (activates .venv and runs main.py)
├── main.py                # Entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## How Harmonic Distance Works

Spotify reports each track's key as an integer (0 = C … 11 = B) and mode (0 = minor, 1 = major). These are converted to Camelot positions — numbers 1–12 on a circle of fifths, suffixed `A` (minor) or `B` (major).

Distance between two positions:

```
circular_dist = min(|n1 - n2|, 12 - |n1 - n2|)   ← wraps around at 12
mode_penalty  = 0 if same letter, else 1
total         = circular_dist + mode_penalty
```

A distance of **0** is a perfect match; **1** is a compatible blend (adjacent fifth or relative major/minor); **2+** introduces increasing harmonic tension.
