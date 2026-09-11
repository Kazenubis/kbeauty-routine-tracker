import unittest
from datetime import date, timedelta

from routine_db import (
    ROUTINE_STEPS,
    completion_by_date,
    current_streak,
    get_connection,
    get_day_status,
    is_day_complete,
    log_step,
    longest_streak,
)

TEST_STEPS = ["Cleanser", "Toner", "Moisturizer"]  # a smaller set keeps tests short


def complete_day(conn, d, steps=TEST_STEPS):
    for step in steps:
        log_step(conn, d, step, True)


class TestLoggingAndStatus(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_unlogged_steps_default_to_incomplete(self):
        status = get_day_status(self.conn, "2026-01-01", TEST_STEPS)
        self.assertEqual(status, {"Cleanser": False, "Toner": False, "Moisturizer": False})

    def test_logging_a_step_marks_it_complete(self):
        log_step(self.conn, "2026-01-01", "Cleanser", True)
        status = get_day_status(self.conn, "2026-01-01", TEST_STEPS)
        self.assertTrue(status["Cleanser"])
        self.assertFalse(status["Toner"])

    def test_relogging_a_step_updates_rather_than_duplicates(self):
        log_step(self.conn, "2026-01-01", "Cleanser", True)
        log_step(self.conn, "2026-01-01", "Cleanser", False)
        status = get_day_status(self.conn, "2026-01-01", TEST_STEPS)
        self.assertFalse(status["Cleanser"])

    def test_is_day_complete_requires_every_step(self):
        log_step(self.conn, "2026-01-01", "Cleanser", True)
        log_step(self.conn, "2026-01-01", "Toner", True)
        self.assertFalse(is_day_complete(self.conn, "2026-01-01", TEST_STEPS))
        log_step(self.conn, "2026-01-01", "Moisturizer", True)
        self.assertTrue(is_day_complete(self.conn, "2026-01-01", TEST_STEPS))

    def test_default_routine_steps_include_essence(self):
        # The K-beauty-specific detail: essence gets its own step, unlike
        # a generic Western routine tracker.
        self.assertIn("Essence", ROUTINE_STEPS)


class TestCurrentStreak(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_no_entries_gives_zero_streak(self):
        self.assertEqual(current_streak(self.conn, as_of=date(2026, 1, 10), steps=TEST_STEPS), 0)

    def test_three_consecutive_complete_days(self):
        today = date(2026, 1, 10)
        for offset in range(3):
            complete_day(self.conn, today - timedelta(days=offset))
        self.assertEqual(current_streak(self.conn, as_of=today, steps=TEST_STEPS), 3)

    def test_incomplete_today_does_not_zero_out_an_existing_streak(self):
        today = date(2026, 1, 10)
        complete_day(self.conn, today - timedelta(days=1))
        complete_day(self.conn, today - timedelta(days=2))
        # today itself: nothing logged yet
        self.assertEqual(current_streak(self.conn, as_of=today, steps=TEST_STEPS), 2)

    def test_a_gap_breaks_the_streak(self):
        today = date(2026, 1, 10)
        complete_day(self.conn, today)
        complete_day(self.conn, today - timedelta(days=1))
        # gap at today - 2
        complete_day(self.conn, today - timedelta(days=3))
        self.assertEqual(current_streak(self.conn, as_of=today, steps=TEST_STEPS), 2)

    def test_a_partially_completed_day_counts_as_a_gap(self):
        today = date(2026, 1, 10)
        complete_day(self.conn, today)
        log_step(self.conn, today - timedelta(days=1), "Cleanser", True)  # only 1 of 3 steps
        self.assertEqual(current_streak(self.conn, as_of=today, steps=TEST_STEPS), 1)


class TestLongestStreak(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_longest_streak_beats_a_shorter_current_streak(self):
        base = date(2026, 1, 1)
        # A 4-day streak early on...
        for offset in range(4):
            complete_day(self.conn, base + timedelta(days=offset))
        # ...then a gap, then a shorter 2-day streak more recently.
        for offset in range(10, 12):
            complete_day(self.conn, base + timedelta(days=offset))
        self.assertEqual(longest_streak(self.conn, steps=TEST_STEPS), 4)
        self.assertEqual(
            current_streak(self.conn, as_of=base + timedelta(days=11), steps=TEST_STEPS), 2
        )

    def test_empty_history_gives_zero(self):
        self.assertEqual(longest_streak(self.conn, steps=TEST_STEPS), 0)


class TestCompletionByDate(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_fraction_reflects_partial_completion(self):
        log_step(self.conn, "2026-01-01", "Cleanser", True)
        log_step(self.conn, "2026-01-01", "Toner", True)
        result = completion_by_date(self.conn, steps=TEST_STEPS)
        self.assertAlmostEqual(result["2026-01-01"], 2 / 3)

    def test_only_dates_with_at_least_one_entry_appear(self):
        log_step(self.conn, "2026-01-01", "Cleanser", True)
        result = completion_by_date(self.conn, steps=TEST_STEPS)
        self.assertEqual(list(result.keys()), ["2026-01-01"])


if __name__ == "__main__":
    unittest.main()
