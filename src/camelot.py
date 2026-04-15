"""
Camelot Wheel mapping and harmonic distance calculation.

The Camelot Wheel is a 24-position system used by DJs to find compatible keys:
  - 12 'B' positions for major keys  (outer ring)
  - 12 'A' positions for minor keys  (inner ring)
  - Numbers 1–12 arranged in a circle of perfect fifths

Compatible transitions (distance = 1):
  - Adjacent numbers, same mode   → e.g., 8B → 9B  (a perfect fifth up)
  - Same number, opposite mode    → e.g., 8B → 8A  (relative major/minor)

Distance = 0 means the same key (perfect match).
The maximum meaningful distance is 7 (opposite side of the wheel + mode shift).

Spotify key integers:  0=C, 1=C#, 2=D, 3=D#, 4=E, 5=F,
                       6=F#, 7=G, 8=G#, 9=A, 10=A#, 11=B, -1=unknown
Spotify mode integers: 0=minor, 1=major
"""

from __future__ import annotations

# (spotify_key, spotify_mode) → (camelot_number, camelot_letter)
CAMELOT_MAP: dict[tuple[int, int], tuple[int, str]] = {
    # Major keys → 'B' suffix
    (0,  1): (8,  'B'),   # C  major  → 8B
    (1,  1): (3,  'B'),   # C# major  → 3B
    (2,  1): (10, 'B'),   # D  major  → 10B
    (3,  1): (5,  'B'),   # Eb major  → 5B
    (4,  1): (12, 'B'),   # E  major  → 12B
    (5,  1): (7,  'B'),   # F  major  → 7B
    (6,  1): (2,  'B'),   # F# major  → 2B
    (7,  1): (9,  'B'),   # G  major  → 9B
    (8,  1): (4,  'B'),   # Ab major  → 4B
    (9,  1): (11, 'B'),   # A  major  → 11B
    (10, 1): (6,  'B'),   # Bb major  → 6B
    (11, 1): (1,  'B'),   # B  major  → 1B
    # Minor keys → 'A' suffix
    (0,  0): (5,  'A'),   # C  minor  → 5A
    (1,  0): (12, 'A'),   # C# minor  → 12A
    (2,  0): (7,  'A'),   # D  minor  → 7A
    (3,  0): (2,  'A'),   # Eb minor  → 2A
    (4,  0): (9,  'A'),   # E  minor  → 9A
    (5,  0): (4,  'A'),   # F  minor  → 4A
    (6,  0): (11, 'A'),   # F# minor  → 11A
    (7,  0): (6,  'A'),   # G  minor  → 6A
    (8,  0): (1,  'A'),   # Ab minor  → 1A
    (9,  0): (8,  'A'),   # A  minor  → 8A
    (10, 0): (3,  'A'),   # Bb minor  → 3A
    (11, 0): (10, 'A'),   # B  minor  → 10A
}

KEY_NAMES  = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MODE_NAMES = {0: 'min', 1: 'maj'}

_UNKNOWN = (0, '?')


def get_camelot(spotify_key: int, mode: int) -> tuple[int, str]:
    """
    Convert a Spotify (key, mode) pair to a Camelot (number, letter) tuple.
    Returns (0, '?') when the key is unknown (Spotify reports -1).
    """
    return CAMELOT_MAP.get((spotify_key, mode), _UNKNOWN)


def camelot_to_str(number: int, letter: str) -> str:
    """Format a Camelot position as a string, e.g. '8B' or '12A'."""
    if number == 0:
        return '??'
    return f"{number}{letter}"


def harmonic_distance(num1: int, letter1: str, num2: int, letter2: str) -> int:
    """
    Minimum harmonic distance between two Camelot wheel positions.

    Algorithm
    ---------
    1. Compute the circular step-distance on the 1–12 number ring:
         raw = |num1 - num2|
         num_dist = min(raw, 12 - raw)        ← wrap around at 12

    2. Add a mode penalty if the letters differ (A vs B):
         mode_dist = 0 if same, else 1

    3. Total distance = num_dist + mode_dist

    Examples
    --------
    8B → 8B   distance = 0   (identical)
    8B → 9B   distance = 1   (adjacent, same mode — perfect fifth)
    8B → 8A   distance = 1   (relative major/minor)
    8B → 7A   distance = 2   (one step + mode change)
    8B → 2B   distance = 6   (opposite side of the wheel)
    """
    if num1 == 0 or num2 == 0:
        return 6   # unknown key → assign a high penalty

    raw      = abs(num1 - num2)
    num_dist = min(raw, 12 - raw)
    mode_dist = 0 if letter1 == letter2 else 1
    return num_dist + mode_dist
