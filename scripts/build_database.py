import argparse
from pathlib import Path

from urbanflow.analytics.database import (
    get_connection,
)
from urbanflow.config import (
    AnalysisPeriod,
    latest_complete_month,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the UrbanFlow DuckDB "
            "analytics layer."
        )
    )

    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help=(
            "Analysis month in YYYYMM format. "
            "Defaults to the latest complete month."
        ),
    )

    return parser.parse_args()


def resolve_period(
    value: str | None,
) -> AnalysisPeriod:
    if value is not None:
        return AnalysisPeriod.from_yyyymm(
            value
        )

    return latest_complete_month()


def sql_path(
    path: Path,
) -> str:
    return (
        path
        .resolve()
        .as_posix()
        .replace("'", "''")
    )


def build_database(
    period: AnalysisPeriod,
) -> None:
    trips_path = (
        period.trips_parquet
    )

    weather_path = (
        period.weather_parquet
    )

    if not trips_path.exists():
        raise FileNotFoundError(
            "Processed trip dataset "
            f"not found: {trips_path}"
        )

    if not weather_path.exists():
        raise FileNotFoundError(
            "Processed weather dataset "
            f"not found: {weather_path}"
        )

    trips_sql_path = sql_path(
        trips_path
    )

    weather_sql_path = sql_path(
        weather_path
    )

    conn = get_connection()

    try:
        print()
        print("=" * 60)
        print("URBANFLOW ANALYTICS BUILD")
        print("=" * 60)

        print(
            f"Period  : {period}"
        )

        print(
            f"Trips   : {trips_path}"
        )

        print(
            f"Weather : {weather_path}"
        )

        print()
        print(
            "Building UrbanFlow "
            "analytics database..."
        )

        # -------------------------------------------------
        # TRIP VIEW
        # -------------------------------------------------

        conn.execute(
            f"""
            CREATE OR REPLACE VIEW trips AS

            SELECT *
            FROM read_parquet(
                '{trips_sql_path}'
            );
            """
        )

        # -------------------------------------------------
        # DAILY METRICS
        # -------------------------------------------------

        conn.execute(
            """
            CREATE OR REPLACE TABLE daily_metrics AS

            SELECT
                date,

                COUNT(*) AS rides,

                AVG(
                    duration_minutes
                ) AS avg_duration_minutes,

                SUM(
                    CASE
                        WHEN member_casual = 'member'
                        THEN 1
                        ELSE 0
                    END
                ) AS member_rides,

                SUM(
                    CASE
                        WHEN member_casual = 'casual'
                        THEN 1
                        ELSE 0
                    END
                ) AS casual_rides

            FROM trips

            GROUP BY date

            ORDER BY date;
            """
        )

        # -------------------------------------------------
        # HOURLY METRICS
        # -------------------------------------------------

        conn.execute(
            """
            CREATE OR REPLACE TABLE hourly_metrics AS

            SELECT
                weekday,
                hour,
                COUNT(*) AS rides

            FROM trips

            GROUP BY
                weekday,
                hour

            ORDER BY
                weekday,
                hour;
            """
        )

        # -------------------------------------------------
        # STATION METRICS
        # -------------------------------------------------

        conn.execute(
            """
            CREATE OR REPLACE TABLE station_metrics AS

            WITH station_events AS (

                SELECT
                    LOWER(
                        TRIM(
                            start_station_name
                        )
                    ) AS station_key,

                    start_station_name
                        AS station_name,

                    start_station_id
                        AS source_station_id,

                    start_lat
                        AS latitude,

                    start_lng
                        AS longitude,

                    1::BIGINT
                        AS departures,

                    0::BIGINT
                        AS arrivals

                FROM trips

                WHERE
                    start_station_name
                        IS NOT NULL
                    AND start_station_id
                        IS NOT NULL
                    AND start_lat
                        IS NOT NULL
                    AND start_lng
                        IS NOT NULL

                UNION ALL

                SELECT
                    LOWER(
                        TRIM(
                            end_station_name
                        )
                    ) AS station_key,

                    end_station_name
                        AS station_name,

                    end_station_id
                        AS source_station_id,

                    end_lat
                        AS latitude,

                    end_lng
                        AS longitude,

                    0::BIGINT
                        AS departures,

                    1::BIGINT
                        AS arrivals

                FROM trips

                WHERE
                    end_station_name
                        IS NOT NULL
                    AND end_station_id
                        IS NOT NULL
                    AND end_lat
                        IS NOT NULL
                    AND end_lng
                        IS NOT NULL
            ),

            aggregated AS (

                SELECT
                    station_key,

                    ANY_VALUE(
                        station_name
                    ) AS station_name,

                    COUNT(
                        DISTINCT source_station_id
                    ) AS source_station_id_count,

                    MEDIAN(
                        latitude
                    ) AS latitude,

                    MEDIAN(
                        longitude
                    ) AS longitude,

                    SUM(
                        departures
                    ) AS departures,

                    SUM(
                        arrivals
                    ) AS arrivals

                FROM station_events

                GROUP BY
                    station_key
            )

            SELECT
                station_key,
                station_name,
                source_station_id_count,
                latitude,
                longitude,
                departures,
                arrivals,

                arrivals - departures
                    AS net_flow,

                arrivals + departures
                    AS total_activity,

                CAST(
                    ABS(
                        arrivals - departures
                    )
                    AS DOUBLE
                )
                /
                NULLIF(
                    arrivals + departures,
                    0
                ) AS imbalance_ratio

            FROM aggregated;
            """
        )

        # -------------------------------------------------
        # OD FLOW
        # -------------------------------------------------

        conn.execute(
            """
            CREATE OR REPLACE TABLE od_flow AS

            WITH normalized_routes AS (

                SELECT
                    LOWER(
                        TRIM(
                            start_station_name
                        )
                    ) AS start_station_key,

                    start_station_name,

                    LOWER(
                        TRIM(
                            end_station_name
                        )
                    ) AS end_station_key,

                    end_station_name

                FROM trips

                WHERE
                    start_station_name
                        IS NOT NULL
                    AND end_station_name
                        IS NOT NULL
            )

            SELECT
                start_station_key,

                ANY_VALUE(
                    start_station_name
                ) AS start_station_name,

                end_station_key,

                ANY_VALUE(
                    end_station_name
                ) AS end_station_name,

                COUNT(*) AS rides

            FROM normalized_routes

            WHERE
                start_station_key
                    != end_station_key

            GROUP BY
                start_station_key,
                end_station_key;
            """
        )

        # -------------------------------------------------
        # WEATHER VIEW
        # -------------------------------------------------

        conn.execute(
            f"""
            CREATE OR REPLACE VIEW weather AS

            SELECT *
            FROM read_parquet(
                '{weather_sql_path}'
            );
            """
        )

        # -------------------------------------------------
        # WEATHER-ADJUSTED RIDE DEMAND
        # -------------------------------------------------

        conn.execute(
            """
            CREATE OR REPLACE TABLE
                weather_ride_hourly AS

            WITH rides_hourly AS (

                SELECT
                    date,
                    hour,

                    ANY_VALUE(
                        weekday
                    ) AS weekday,

                    COUNT(*)
                        AS rides,

                    MEDIAN(
                        duration_minutes
                    ) AS median_duration_minutes

                FROM trips

                GROUP BY
                    date,
                    hour
            ),

            baseline AS (

                SELECT
                    weekday,
                    hour,

                    AVG(
                        rides
                    ) AS expected_rides

                FROM rides_hourly

                GROUP BY
                    weekday,
                    hour
            )

            SELECT
                r.date,
                r.weekday,
                r.hour,
                r.rides,
                r.median_duration_minutes,
                b.expected_rides,

                r.rides * 1.0
                /
                NULLIF(
                    b.expected_rides,
                    0
                ) AS demand_index,

                (
                    r.rides * 1.0
                    /
                    NULLIF(
                        b.expected_rides,
                        0
                    )
                    - 1
                ) * 100
                    AS demand_vs_expected_pct,

                w.temperature_c,
                w.relative_humidity_pct,
                w.precipitation_mm,
                w.wind_speed_kmh,

                CASE
                    WHEN
                        w.precipitation_mm = 0
                    THEN
                        'No precipitation'

                    WHEN
                        w.precipitation_mm < 2.5
                    THEN
                        'Light precipitation'

                    ELSE
                        'Moderate / heavy precipitation'
                END AS precipitation_category

            FROM rides_hourly r

            INNER JOIN baseline b
                ON r.weekday = b.weekday
                AND r.hour = b.hour

            INNER JOIN weather w
                ON r.date = w.date
                AND r.hour = w.hour

            ORDER BY
                r.date,
                r.hour;
            """
        )

        print()
        print("=" * 60)
        print("ANALYTICS DATABASE READY")
        print("=" * 60)

        tables = conn.execute(
            """
            SHOW ALL TABLES;
            """
        ).fetchdf()

        print(
            tables
        )

    finally:
        conn.close()


def main() -> None:
    args = parse_args()

    period = resolve_period(
        args.period
    )

    build_database(
        period
    )


if __name__ == "__main__":
    main()