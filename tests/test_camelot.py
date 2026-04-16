"""Tests for Camelot Wheel mapping and harmonic distance."""

import pytest
from src.camelot import get_camelot, harmonic_distance, camelot_to_str


class TestGetCamelot:
    def test_c_major(self):
        assert get_camelot(0, 1) == (8, "B")

    def test_a_minor(self):
        assert get_camelot(9, 0) == (8, "A")

    def test_b_major(self):
        assert get_camelot(11, 1) == (1, "B")

    def test_unknown_key_minus_one(self):
        # Spotify reports -1 when key detection confidence is too low
        assert get_camelot(-1, 1) == (0, "?")

    def test_unknown_key_out_of_range(self):
        assert get_camelot(99, 0) == (0, "?")

    def test_all_major_keys_have_b_letter(self):
        for key in range(12):
            _, letter = get_camelot(key, 1)
            assert letter == "B", f"Key {key} major should map to B"

    def test_all_minor_keys_have_a_letter(self):
        for key in range(12):
            _, letter = get_camelot(key, 0)
            assert letter == "A", f"Key {key} minor should map to A"

    def test_camelot_numbers_in_range(self):
        for key in range(12):
            for mode in (0, 1):
                num, _ = get_camelot(key, mode)
                assert 1 <= num <= 12, f"Camelot number out of range for key={key} mode={mode}"


class TestCamelotToStr:
    def test_known(self):
        assert camelot_to_str(8, "B") == "8B"
        assert camelot_to_str(12, "A") == "12A"

    def test_unknown(self):
        assert camelot_to_str(0, "?") == "??"


class TestHarmonicDistance:
    def test_same_position(self):
        assert harmonic_distance(8, "B", 8, "B") == 0

    def test_adjacent_same_mode(self):
        assert harmonic_distance(8, "B", 9, "B") == 1
        assert harmonic_distance(8, "B", 7, "B") == 1

    def test_relative_major_minor(self):
        # Same number, opposite mode = relative major/minor pair
        assert harmonic_distance(8, "B", 8, "A") == 1

    def test_wrap_around(self):
        # 1 and 12 are adjacent on the wheel
        assert harmonic_distance(1, "B", 12, "B") == 1
        assert harmonic_distance(12, "A", 1, "A") == 1

    def test_opposite_side(self):
        # 6 steps away = opposite side of the wheel
        assert harmonic_distance(1, "B", 7, "B") == 6

    def test_symmetry(self):
        # Distance should be the same in both directions
        assert harmonic_distance(3, "A", 9, "B") == harmonic_distance(9, "B", 3, "A")

    def test_unknown_key_penalty(self):
        assert harmonic_distance(0, "?", 8, "B") == 6
        assert harmonic_distance(8, "B", 0, "?") == 6
