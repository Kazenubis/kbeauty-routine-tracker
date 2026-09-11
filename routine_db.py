"""
SQLite-backed storage and streak math for the K-Beauty Routine Tracker.
Kept entirely independent of Streamlit so it can be unit tested without
starting an app — the "habit tracker dashboard" backlog item's actual
skill (persistence + streak logic) lives here.

A K-beauty routine is the reskin's hook: it keeps "Essence" as its own
step, distinct from serum — the step most Western routines skip
entirely, and the detail that makes this a K-beauty tracker rather than
a generic skincare tracker.
"""

import sqlite3
from datetime import date, timedelta

# Order matters for display, not for the completeness check.
ROUTINE_STEPS = ["Cleanser", "Toner", "Essence", "Serum", "Moisturizer", "Sunscreen"]


def get_connection(db_path=":memory:"):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_date TEXT NOT NULL,
            step TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (entry_date, step)
        )
        """
    )
    conn.commit()
    return conn


def _to_iso(d):
    return d.isoformat() if isinstance(d, date) else d


def log_step(conn, entry_date, step, completed=True):
    entry_date = _to_iso(entry_date)
    conn.execute(
        """
        INSERT INTO entries (entry_date, step, completed) VALUES (?, ?, ?)
        ON CONFLICT(entry_date, step) DO UPDATE SET completed = excluded.completed
        """,
        (entry_date, step, int(completed)),
    )
    conn.commit()


def get_day_status(conn, entry_date, steps=None):
    """Returns {step: bool} for every step in `steps` (default all routine
    steps) — steps never logged for that day default to False."""
    steps = steps or ROUTINE_STEPS
    entry_date = _to_iso(entry_date)
    rows = conn.execute(
        "SELECT step, completed FROM entries WHERE entry_date = ?", (entry_date,)
    ).fetchall()
    logged = {step: bool(completed) for step, completed in rows}
    return {step: logged.get(step, False) for step in steps}


def is_day_complete(conn, entry_date, steps=None):
    status = get_day_status(conn, entry_date, steps)
    return all(status.values())


def current_streak(conn, as_of=None, steps=None):
    """Consecutive complete days ending at (or just before) `as_of`.

    A not-yet-finished "today" doesn't zero out the streak: if `as_of`
    itself isn't complete yet, counting starts from the day before it
    instead, so logging your routine in the evening doesn't make the app
    show a broken streak all afternoon.
    """
    as_of = as_of or date.today()
    if isinstance(as_of, str):
        as_of = date.fromisoformat(as_of)

    day = as_of
    if not is_day_complete(conn, day, steps):
        day = day - timedelta(days=1)

    count = 0
    while is_day_complete(conn, day, steps):
        count += 1
        day = day - timedelta(days=1)
    return count


def longest_streak(conn, steps=None):
    """Longest run of consecutive complete days anywhere in the logged
    history (not just the current one)."""
    dates = sorted(
        date.fromisoformat(row[0])
        for row in conn.execute("SELECT DISTINCT entry_date FROM entries").fetchall()
    )
    if not dates:
        return 0

    best = 0
    running = 0
    previous = None
    for d in dates:
        complete = is_day_complete(conn, d, steps)
        if complete and previous is not None and (d - previous).days == 1:
            running += 1
        elif complete:
            running = 1
        else:
            running = 0
        best = max(best, running)
        previous = d
    return best


def completion_by_date(conn, steps=None):
    """Returns {date_str: fraction_complete} for every date that has at
    least one logged entry — the raw data a calendar heatmap is built
    from."""
    steps = steps or ROUTINE_STEPS
    dates = sorted(
        row[0] for row in conn.execute("SELECT DISTINCT entry_date FROM entries").fetchall()
    )
    result = {}
    for d in dates:
        status = get_day_status(conn, d, steps)
        result[d] = sum(status.values()) / len(steps)
    return result
