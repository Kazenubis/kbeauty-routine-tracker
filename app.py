"""
K-Beauty Routine Tracker — Streamlit front-end.

Log today's routine as a checklist, see the current/longest streak, and a
12-week completion heatmap. All persistence and streak math lives in
routine_db.py / heatmap.py so it's covered by unit tests without needing
to drive a browser.
"""

from datetime import date

import matplotlib.pyplot as plt
import streamlit as st

from heatmap import build_calendar_grid
from routine_db import (
    ROUTINE_STEPS,
    completion_by_date,
    current_streak,
    get_connection,
    get_day_status,
    log_step,
    longest_streak,
)

DB_PATH = "routine.db"


@st.cache_resource
def get_db():
    return get_connection(DB_PATH)


def draw_heatmap(completion):
    grid, week_starts = build_calendar_grid(completion, weeks=12)
    fig, ax = plt.subplots(figsize=(9, 2.2))
    im = ax.imshow(grid, cmap="RdPu", vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(7))
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], fontsize=8)
    tick_positions = list(range(0, len(week_starts), 2))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([week_starts[i] for i in tick_positions], fontsize=7, rotation=45, ha="right")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02, label="% steps done")
    fig.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="K-Beauty Routine Tracker", page_icon="🧴")
    conn = get_db()

    st.title("🧴 K-Beauty Routine Tracker")
    st.caption(
        "Cleanser → Toner → Essence → Serum → Moisturizer → Sunscreen — "
        "the essence step is what a Western 3-step routine usually skips."
    )

    today = date.today()
    st.subheader(f"Today — {today.isoformat()}")

    status = get_day_status(conn, today)
    for step in ROUTINE_STEPS:
        checked = st.checkbox(step, value=status[step], key=f"step-{step}")
        if checked != status[step]:
            log_step(conn, today, step, checked)

    col1, col2 = st.columns(2)
    col1.metric("Current streak", f"{current_streak(conn)} days")
    col2.metric("Longest streak", f"{longest_streak(conn)} days")

    st.subheader("Last 12 weeks")
    completion = completion_by_date(conn)
    if completion:
        st.pyplot(draw_heatmap(completion))
    else:
        st.info("Log a few days to see your completion heatmap here.")


if __name__ == "__main__":
    main()
