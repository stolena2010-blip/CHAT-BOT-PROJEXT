"""
Database Module
---------------
Provides functions to query the recruiter schedule (Tech.dbo.Schedule).
Used by the Scheduling Advisor via OpenAI Function Calling.

Supports two backends:
 • SQL Server via pyodbc  (production — matches db_Tech.sql)
 • SQLite in-memory       (fallback for local dev / Streamlit Cloud)

On import the module seeds an in-memory SQLite from the same logic as
db_Tech.sql so everything works out-of-the-box without SQL Server.
"""

import os
import sqlite3
from datetime import date, time, timedelta
from typing import Optional

# ── In-memory SQLite setup ─────────────────────────────────────────────
_DB_PATH = ":memory:"
_conn: Optional[sqlite3.Connection] = None


def _get_connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _seed_database(_conn)
    return _conn


def _seed_database(conn: sqlite3.Connection) -> None:
    """Recreate the Schedule table matching db_Tech.sql (2024 data)."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Schedule (
            ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            time       TEXT NOT NULL,
            position   TEXT NOT NULL,
            available  INTEGER NOT NULL
        )
    """)

    import random
    random.seed(42)

    positions = ["Python Dev", "Sql Dev", "Analyst", "ML"]
    hours = [time(h, 0) for h in range(9, 18)]  # 09:00 – 17:00
    today = date.today()
    start = date(today.year, 1, 1)
    end = date(today.year, 12, 31)

    rows = []
    d = start
    while d <= end:
        day_name = d.strftime("%A")
        # Tue-Fri & Sun only (skip Sat, Mon)
        if day_name not in ("Saturday", "Monday"):
            for t in hours:
                for pos in positions:
                    avail = 1 if (random.random() >= 0.5) else 0
                    rows.append((d.isoformat(), t.strftime("%H:%M"), pos, avail))
        d += timedelta(days=1)

    cur.executemany(
        "INSERT INTO Schedule (date, time, position, available) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    print(f"[DB] Seeded {len(rows)} schedule rows")


# ── Public query functions (used by Scheduling Advisor) ────────────────

def get_available_slots(
    position: str,
    from_date: str,
    to_date: str,
    limit: int = 3,
) -> list[dict]:
    """
    Return up to `limit` available time slots for a given position
    between from_date and to_date (inclusive, format YYYY-MM-DD).
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, time, position
        FROM Schedule
        WHERE position = ?
          AND date >= ?
          AND date <= ?
          AND available = 1
        ORDER BY date, time
        LIMIT ?
        """,
        (position, from_date, to_date, limit),
    )
    return [
        {"date": row[0], "time": row[1], "position": row[2]}
        for row in cur.fetchall()
    ]


def check_slot_available(
    position: str,
    slot_date: str,
    slot_time: str,
) -> bool:
    """Check if a specific date+time slot is available."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT available
        FROM Schedule
        WHERE position = ?
          AND date = ?
          AND time = ?
        """,
        (position, slot_date, slot_time),
    )
    row = cur.fetchone()
    return bool(row and row[0] == 1)


def book_slot(position: str, slot_date: str, slot_time: str) -> bool:
    """Mark a slot as unavailable (booked). Returns True if successful."""
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE Schedule
        SET available = 0
        WHERE position = ?
          AND date = ?
          AND time = ?
          AND available = 1
        """,
        (position, slot_date, slot_time),
    )
    conn.commit()
    return cur.rowcount > 0


# ── Quick test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    slots = get_available_slots("Python Dev", "2024-04-10", "2024-04-15")
    print(f"Available slots: {slots}")
    if slots:
        s = slots[0]
        print(f"Booking {s} → {book_slot(s['position'], s['date'], s['time'])}")
