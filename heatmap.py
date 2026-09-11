"""
Turns a {date_str: completion_fraction} dict (from routine_db.completion_by_date)
into a calendar grid a chart library can plot directly — kept separate from
both the DB layer and the Streamlit app so the grid math has its own tests
independent of matplotlib.
"""

from datetime import date, timedelta


def build_calendar_grid(completion, end_date=None, weeks=12):
    """Returns (grid, week_starts):
      - grid: 7 rows (Monday..Sunday) x `weeks` columns of completion
        fractions (0.0 for any day with no logged entry at all)
      - week_starts: the Monday date (as a string) of each column, for
        labeling the x-axis

    The window always ends on the Sunday of `end_date`'s week and spans
    exactly `weeks` full weeks, so the grid is a clean rectangle.
    """
    end_date = end_date or date.today()
    if isinstance(end_date, str):
        end_date = date.fromisoformat(end_date)

    days_after_sunday = 6 - end_date.weekday() if end_date.weekday() != 6 else 0
    window_end = end_date + timedelta(days=days_after_sunday)
    window_start = window_end - timedelta(days=weeks * 7 - 1)

    grid = [[0.0] * weeks for _ in range(7)]
    week_starts = []

    for week in range(weeks):
        monday = window_start + timedelta(days=week * 7)
        week_starts.append(monday.isoformat())
        for weekday in range(7):
            day = monday + timedelta(days=weekday)
            grid[weekday][week] = completion.get(day.isoformat(), 0.0)

    return grid, week_starts
