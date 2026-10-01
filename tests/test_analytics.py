from pathlib import Path

import duckdb
import pytest

DATABASE_PATH = Path(
    "data/analytics/urbanflow.duckdb"
)


pytestmark = pytest.mark.skipif(
    not DATABASE_PATH.exists(),
    reason=(
        "UrbanFlow analytics database "
        "has not been built."
    ),
)


def get_connection():
    return duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )


def test_required_analytics_objects_exist():
    con = get_connection()

    tables = con.execute(
        """
        SHOW ALL TABLES;
        """
    ).fetchdf()

    con.close()

    existing = set(
        tables["name"].tolist()
    )

    required = {
        "trips",
        "daily_metrics",
        "hourly_metrics",
        "station_metrics",
        "od_flow",
        "weather",
        "weather_ride_hourly",
    }

    assert required.issubset(existing)


def test_trip_count_is_expected():
    con = get_connection()

    total_rides = con.execute(
        """
        SELECT COUNT(*)
        FROM trips;
        """
    ).fetchone()[0]

    con.close()

    assert total_rides == 5_244_782


def test_trip_ids_are_unique():
    con = get_connection()

    result = con.execute(
        """
        SELECT
            COUNT(*) AS rows,
            COUNT(DISTINCT ride_id)
                AS unique_rides
        FROM trips;
        """
    ).fetchone()

    con.close()

    assert result[0] == result[1]


def test_trip_dates_are_august_2026():
    con = get_connection()

    min_date, max_date = (
        con.execute(
            """
            SELECT
                MIN(date),
                MAX(date)
            FROM trips;
            """
        ).fetchone()
    )

    con.close()

    assert str(min_date) == "2026-08-01"
    assert str(max_date) == "2026-08-31"


def test_trip_duration_is_positive():
    con = get_connection()

    invalid = con.execute(
        """
        SELECT COUNT(*)
        FROM trips
        WHERE duration_minutes <= 0;
        """
    ).fetchone()[0]

    con.close()

    assert invalid == 0


def test_weather_has_full_hourly_coverage():
    con = get_connection()

    rows = con.execute(
        """
        SELECT COUNT(*)
        FROM weather;
        """
    ).fetchone()[0]

    con.close()

    assert rows == 744


def test_weather_ride_join_is_complete():
    con = get_connection()

    rows = con.execute(
        """
        SELECT COUNT(*)
        FROM weather_ride_hourly;
        """
    ).fetchone()[0]

    con.close()

    assert rows == 744


def test_demand_index_is_normalized():
    con = get_connection()

    avg_index = con.execute(
        """
        SELECT AVG(demand_index)
        FROM weather_ride_hourly;
        """
    ).fetchone()[0]

    con.close()

    assert 0.99 <= avg_index <= 1.01


def test_station_imbalance_is_valid():
    con = get_connection()

    invalid = con.execute(
        """
        SELECT COUNT(*)
        FROM station_metrics
        WHERE
            imbalance_ratio < 0
            OR imbalance_ratio > 1;
        """
    ).fetchone()[0]

    con.close()

    assert invalid == 0


def test_station_activity_is_non_negative():
    con = get_connection()

    invalid = con.execute(
        """
        SELECT COUNT(*)
        FROM station_metrics
        WHERE
            departures < 0
            OR arrivals < 0
            OR total_activity < 0;
        """
    ).fetchone()[0]

    con.close()

    assert invalid == 0