from urbanflow.analytics.database import (
    get_connection,
)


PARQUET_SOURCE = (
    "data/processed/trips/"
    "trips_2026_08.parquet"
)


def main() -> None:
    conn = get_connection()

    print("Building UrbanFlow analytics database...")

    conn.execute(
        f"""
        CREATE OR REPLACE VIEW trips AS
        SELECT *
        FROM read_parquet(
            '{PARQUET_SOURCE}'
        );
        """
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE daily_metrics AS
        SELECT
            date,
            COUNT(*) AS rides,
            AVG(duration_minutes)
                AS avg_duration_minutes,
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

    conn.execute(
        """
        CREATE OR REPLACE TABLE station_metrics AS

        WITH station_events AS (

            SELECT
                LOWER(
                    TRIM(start_station_name)
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
                start_station_name IS NOT NULL
                AND start_station_id IS NOT NULL
                AND start_lat IS NOT NULL
                AND start_lng IS NOT NULL


            UNION ALL


            SELECT
                LOWER(
                    TRIM(end_station_name)
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
                end_station_name IS NOT NULL
                AND end_station_id IS NOT NULL
                AND end_lat IS NOT NULL
                AND end_lng IS NOT NULL
        ),


        aggregated AS (

            SELECT
                station_key,

                ANY_VALUE(station_name)
                    AS station_name,

                COUNT(
                    DISTINCT source_station_id
                ) AS source_station_id_count,

                MEDIAN(latitude)
                    AS latitude,

                MEDIAN(longitude)
                    AS longitude,

                SUM(departures)
                    AS departures,

                SUM(arrivals)
                    AS arrivals

            FROM station_events

            GROUP BY station_key
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
            )
                AS imbalance_ratio

        FROM aggregated;
        """
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE od_flow AS

        WITH normalized_routes AS (

            SELECT
                LOWER(
                    TRIM(start_station_name)
                ) AS start_station_key,

                start_station_name,

                LOWER(
                    TRIM(end_station_name)
                ) AS end_station_key,

                end_station_name

            FROM trips

            WHERE
                start_station_name IS NOT NULL
                AND end_station_name IS NOT NULL
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

    conn.execute(
        """
        CREATE OR REPLACE VIEW weather AS

        SELECT *
        FROM read_parquet(
            'data/processed/weather/'
            'weather_2026_08.parquet'
        );
        """
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE weather_ride_hourly AS

        WITH rides_hourly AS (

            SELECT
                date,
                hour,

                ANY_VALUE(weekday)
                    AS weekday,

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

                AVG(rides)
                    AS expected_rides

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
            / NULLIF(
                b.expected_rides,
                0
            ) AS demand_index,

            (
                r.rides * 1.0
                / NULLIF(
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
                WHEN w.precipitation_mm = 0
                    THEN 'No precipitation'

                WHEN w.precipitation_mm < 2.5
                    THEN 'Light precipitation'

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

    print(tables)

    conn.close()


if __name__ == "__main__":
    main()