"""Seeds routine.db with a few weeks of realistic history, purely so the
README screenshot doesn't show an empty first-run state. Not part of the
app itself — delete routine.db any time to start fresh."""

import random
from datetime import date, timedelta

from routine_db import ROUTINE_STEPS, get_connection, log_step

DB_PATH = "routine.db"


def main():
    conn = get_connection(DB_PATH)
    today = date.today()
    rng = random.Random(3)

    # A clean 6-day streak leading up to today, then patchier weeks before
    # that — a realistic "built the habit recently" shape.
    for offset in range(6):
        d = today - timedelta(days=offset)
        for step in ROUTINE_STEPS:
            log_step(conn, d, step, True)

    for offset in range(6, 70):
        d = today - timedelta(days=offset)
        for step in ROUTINE_STEPS:
            log_step(conn, d, step, rng.random() < 0.6)

    print(f"Seeded {DB_PATH} with 70 days of demo history.")


if __name__ == "__main__":
    main()
