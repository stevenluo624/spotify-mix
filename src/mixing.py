"""
Three mixing algorithms corresponding to the three energy-flow styles.

Each function receives a list of enriched track dicts
(must have: tempo, camelot_num, camelot_letter, energy)
and returns the tracks in the desired playback order.

Cost formula used by the greedy nearest-neighbour steps
-------------------------------------------------------
  cost(A → B) = W_BPM  * (|bpm_A - bpm_B| / BPM_SCALE)
              + W_HARM  * harmonic_distance(A, B)

  BPM_SCALE normalises BPM differences into the 0–1 range (same range
  as the 0–1 harmonic weight). Default weights give BPM and harmony
  roughly equal priority.
"""

from __future__ import annotations

from .camelot import harmonic_distance

# ---------------------------------------------------------------------------
# Transition cost parameters
# ---------------------------------------------------------------------------

W_BPM:     float = 0.5   # weight for normalised BPM difference
W_HARM:    float = 0.5   # weight for harmonic distance (0–7 scale → normalised)
BPM_SCALE: float = 60.0  # typical max BPM delta used for normalisation
HARM_MAX:  float = 7.0   # max harmonic distance used for normalisation


def _transition_cost(t1: dict, t2: dict) -> float:
    """Smooth-transition cost from track *t1* to track *t2* (lower = better)."""
    bpm_delta = abs(t1["tempo"] - t2["tempo"])
    harm      = harmonic_distance(
        t1["camelot_num"], t1["camelot_letter"],
        t2["camelot_num"], t2["camelot_letter"],
    )
    return W_BPM * (bpm_delta / BPM_SCALE) + W_HARM * (harm / HARM_MAX)


def _greedy_from(seed: dict, pool: list[dict]) -> list[dict]:
    """
    Greedy nearest-neighbour walk starting from *seed* through *pool*.
    Modifies *pool* in-place (empties it). Returns the ordered list.
    """
    ordered: list[dict] = []
    remaining = list(pool)
    current   = seed

    while remaining:
        nxt = min(remaining, key=lambda t: _transition_cost(current, t))
        ordered.append(nxt)
        remaining.remove(nxt)
        current = nxt

    return ordered


# ---------------------------------------------------------------------------
# Option A — Consistent Vibe
# ---------------------------------------------------------------------------

def mix_consistent(tracks: list[dict]) -> list[dict]:
    """
    Greedy nearest-neighbour mix that minimises the combined BPM + harmonic
    cost at every step.

    The starting track is the one closest to the median BPM (gives the
    algorithm the most flexibility in both directions).
    """
    if len(tracks) <= 1:
        return list(tracks)

    sorted_by_bpm = sorted(tracks, key=lambda t: t["tempo"])
    median_bpm    = sorted_by_bpm[len(tracks) // 2]["tempo"]
    start         = min(tracks, key=lambda t: abs(t["tempo"] - median_bpm))

    pool = [t for t in tracks if t is not start]
    return [start] + _greedy_from(start, pool)


# ---------------------------------------------------------------------------
# Option B — Slow Build-Up
# ---------------------------------------------------------------------------

def mix_build_up(tracks: list[dict], bracket_size: int = 4) -> list[dict]:
    """
    Global ascending BPM sort + intra-bracket harmonic refinement.

    1. Sort all tracks by BPM (ascending).
    2. Split into consecutive windows of *bracket_size* tracks.
    3. Within each window, use greedy harmonic ordering seeded by the
       last track that was placed (so transitions between brackets are
       also smooth).

    The result steadily rises in energy while keeping local micro-
    transitions as harmonic as possible.
    """
    if len(tracks) <= 1:
        return list(tracks)

    bpm_sorted = sorted(tracks, key=lambda t: t["tempo"])
    result: list[dict] = []

    for i in range(0, len(bpm_sorted), bracket_size):
        bracket = list(bpm_sorted[i : i + bracket_size])

        if len(bracket) == 1:
            result.extend(bracket)
            continue

        # Seed = last placed track; for first bracket start at lowest BPM
        if result:
            seed    = result[-1]
            # Pick the bracket entry that connects best from the seed
            start   = min(bracket, key=lambda t: harmonic_distance(
                seed["camelot_num"],   seed["camelot_letter"],
                t["camelot_num"],      t["camelot_letter"],
            ))
        else:
            start = bracket[0]   # lowest BPM in the first window

        bracket.remove(start)
        bracket_ordered = [start] + _greedy_from(start, bracket)
        result.extend(bracket_ordered)

    return result


# ---------------------------------------------------------------------------
# Option C — Sectioned / Wave
# ---------------------------------------------------------------------------

def mix_sectioned(tracks: list[dict], n_sections: int = 3) -> list[dict]:
    """
    Cluster tracks into Low → Mid → High energy sections, then apply
    greedy harmonic ordering within each section.

    Clustering strategy
    -------------------
    Uses scikit-learn KMeans on BPM if available; falls back to simple
    equal-quantile bucketing so the tool works without sklearn.

    Section order: Low energy → Mid energy → High energy (rising arc).
    """
    if len(tracks) <= 1:
        return list(tracks)

    sections: list[list[dict]] = _cluster_by_bpm(tracks, n_sections)

    result: list[dict] = []
    for section in sections:
        if not section:
            continue

        seed  = result[-1] if result else section[0]
        start = min(section, key=lambda t: harmonic_distance(
            seed["camelot_num"],   seed["camelot_letter"],
            t["camelot_num"],      t["camelot_letter"],
        ))
        pool = [t for t in section if t is not start]
        result.extend([start] + _greedy_from(start, pool))

    return result


def _cluster_by_bpm(tracks: list[dict], n: int) -> list[list[dict]]:
    """
    Return *n* lists of tracks ordered Low → High by median BPM.
    Tries KMeans first; falls back to equal-size quantile split.
    """
    try:
        import numpy as np
        from sklearn.cluster import KMeans  # type: ignore

        bpms   = np.array([[t["tempo"]] for t in tracks], dtype=float)
        km     = KMeans(n_clusters=n, random_state=42, n_init=10)
        labels = km.fit_predict(bpms)

        centroids      = km.cluster_centers_.flatten()
        rank_of_cluster = {
            cluster_id: rank
            for rank, cluster_id in enumerate(np.argsort(centroids))
        }

        buckets: list[list[dict]] = [[] for _ in range(n)]
        for track, label in zip(tracks, labels):
            buckets[rank_of_cluster[label]].append(track)
        return buckets

    except ImportError:
        # Simple quantile split — sort by BPM, divide into n equal chunks
        bpm_sorted = sorted(tracks, key=lambda t: t["tempo"])
        chunk      = max(1, len(bpm_sorted) // n)
        buckets    = []
        for i in range(n):
            start = i * chunk
            end   = start + chunk if i < n - 1 else len(bpm_sorted)
            buckets.append(bpm_sorted[start:end])
        return buckets
