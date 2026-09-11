import unittest
from datetime import date

from heatmap import build_calendar_grid


class TestBuildCalendarGrid(unittest.TestCase):
    def test_grid_shape_is_seven_by_weeks(self):
        grid, week_starts = build_calendar_grid({}, end_date=date(2026, 1, 10), weeks=4)
        self.assertEqual(len(grid), 7)
        self.assertTrue(all(len(row) == 4 for row in grid))
        self.assertEqual(len(week_starts), 4)

    def test_window_ends_on_the_sunday_of_end_dates_week(self):
        # 2026-01-10 is a Saturday.
        _, week_starts = build_calendar_grid({}, end_date=date(2026, 1, 10), weeks=1)
        # The single week column should start on the Monday of that same week.
        self.assertEqual(week_starts[0], "2026-01-05")

    def test_missing_days_default_to_zero(self):
        grid, _ = build_calendar_grid({}, end_date=date(2026, 1, 10), weeks=2)
        self.assertTrue(all(value == 0.0 for row in grid for value in row))

    def test_logged_completion_lands_in_the_correct_cell(self):
        # Monday 2026-01-05, completion 0.5 -> row 0 (Monday), first week column.
        completion = {"2026-01-05": 0.5}
        grid, week_starts = build_calendar_grid(completion, end_date=date(2026, 1, 10), weeks=1)
        self.assertEqual(week_starts[0], "2026-01-05")
        self.assertEqual(grid[0][0], 0.5)  # Monday row
        self.assertEqual(grid[1][0], 0.0)  # Tuesday row untouched

    def test_end_date_that_is_already_a_sunday_stays_the_last_column(self):
        # 2026-01-11 is a Sunday.
        completion = {"2026-01-11": 1.0}
        grid, week_starts = build_calendar_grid(completion, end_date=date(2026, 1, 11), weeks=1)
        self.assertEqual(week_starts[0], "2026-01-05")
        self.assertEqual(grid[6][0], 1.0)  # Sunday row, last column


if __name__ == "__main__":
    unittest.main()
