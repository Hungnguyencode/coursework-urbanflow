from pathlib import Path

import duckdb


DATABASE_PATH = Path("data/analytics/urbanflow.duckdb")
OUTPUT_DIR = Path("data/powerbi")


EXPORTS = {
    "overview_summary.csv": """
        SELECT
            COUNT(*) AS total_rides,
            MEDIAN(duration_minutes) AS median_duration_minutes,
            AVG(
                CASE
                    WHEN member_casual = 'member' THEN 1
                    ELSE 0
                END
            ) * 100 AS member_share_pct,
            AVG(
                CASE
                    WHEN rideable_type = 'electric_bike' THEN 1
                    ELSE 0
                END
            ) * 100 AS electric_bike_share_pct
        FROM trips
    """,
    "daily_metrics.csv": """
        SELECT
            date,
            rides,
            avg_duration_minutes,
            member_rides,
            casual_rides
        FROM daily_metrics
        ORDER BY date
    """,
    "temporal_daily_hourly.csv": """
        SELECT
            date,
            weekday,
            hour,
            COUNT(*) AS rides
        FROM trips
        GROUP BY
            date,
            weekday,
            hour
        ORDER BY
            date,
            hour
    """,
    "station_metrics.csv": """
        SELECT
            station_key,
            station_name,
            source_station_id_count,
            latitude,
            longitude,
            departures,
            arrivals,
            net_flow,
            total_activity,
            imbalance_ratio
        FROM station_metrics
        ORDER BY total_activity DESC
    """,
    "od_flow_top_10000.csv": """
        SELECT
            start_station_key,
            start_station_name,
            end_station_key,
            end_station_name,
            rides
        FROM od_flow
        WHERE
            start_station_name IS NOT NULL
            AND end_station_name IS NOT NULL
        ORDER BY rides DESC
        LIMIT 10000
    """,
    "weather_ride_hourly.csv": """
        SELECT *
        FROM weather_ride_hourly
        ORDER BY
            date,
            hour
    """,
}


def export_query(
    conn: duckdb.DuckDBPyConnection,
    filename: str,
    query: str,
) -> None:
    output_path = (
        OUTPUT_DIR
        / filename
    )

    escaped_path = (
        output_path
        .as_posix()
        .replace("'", "''")
    )

    copy_sql = f"""
        COPY (
            {query}
        )
        TO '{escaped_path}'
        WITH (
            HEADER,
            DELIMITER ','
        );
    """

    conn.execute(
        copy_sql
    )

    size_mb = (
        output_path.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"[EXPORTED] {filename:<30} "
        f"{size_mb:>8.2f} MB"
    )


def main() -> None:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            "UrbanFlow analytics database not found. "
            "Run scripts/build_database.py first."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 60)
    print("URBANFLOW POWER BI EXPORT")
    print("=" * 60)

    conn = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        for filename, query in EXPORTS.items():
            export_query(
                conn,
                filename,
                query,
            )
    finally:
        conn.close()

    trips_path = Path(
        "data/processed/trips/"
        "trips_2026_08.parquet"
    )

    print()
    print(
        "[SOURCE] Trips fact table for Power BI:"
    )
    print(
        f"         {trips_path}"
    )

    print()
    print("=" * 60)
    print("POWER BI EXPORT COMPLETE ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()
