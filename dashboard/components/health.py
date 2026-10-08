import duckdb
import streamlit as st
from components.ui import (
    sidebar_health_status,
)

from urbanflow.config import DATABASE_PATH


@st.cache_data
def load_data_health() -> dict:
    conn = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        total_rides = conn.execute(
            """
            SELECT COUNT(*)
            FROM trips;
            """
        ).fetchone()[0]

        weather_rows = conn.execute(
            """
            SELECT COUNT(*)
            FROM weather;
            """
        ).fetchone()[0]

        joined_rows = conn.execute(
            """
            SELECT COUNT(*)
            FROM weather_ride_hourly;
            """
        ).fetchone()[0]

        object_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'main';
            """
        ).fetchone()[0]

        min_date, max_date = conn.execute(
            """
            SELECT
                MIN(date),
                MAX(date)
            FROM trips;
            """
        ).fetchone()

        return {
            "total_rides": total_rides,
            "weather_rows": weather_rows,
            "joined_rows": joined_rows,
            "object_count": object_count,
            "min_date": min_date,
            "max_date": max_date,
        }

    finally:
        conn.close()

def render_sidebar_health(
    *,
    expected_hours: int,
) -> None:
    health = load_data_health()

    sidebar_health_status(
        total_rides=health["total_rides"],
        weather_rows=health["weather_rows"],
        joined_rows=health["joined_rows"],
        expected_hours=expected_hours,
        object_count=health["object_count"],
    )