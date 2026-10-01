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
        WITH departures AS (
            SELECT
                start_station_id AS station_id,
                start_station_name AS station_name,
                AVG(start_lat) AS latitude,
                AVG(start_lng) AS longitude,
                COUNT(*) AS departures
            FROM trips
            WHERE
                start_station_id IS NOT NULL
                AND start_station_name IS NOT NULL
                AND start_lat IS NOT NULL
                AND start_lng IS NOT NULL
            GROUP BY
                start_station_id,
                start_station_name
        ),

        arrivals AS (
            SELECT
                end_station_id AS station_id,
                COUNT(*) AS arrivals
            FROM trips
            WHERE
                end_station_id IS NOT NULL
            GROUP BY
                end_station_id
        )

        SELECT
            d.station_id,
            d.station_name,
            d.latitude,
            d.longitude,
            d.departures,
            COALESCE(
                a.arrivals,
                0
            ) AS arrivals,

            COALESCE(
                a.arrivals,
                0
            ) - d.departures
                AS net_flow

        FROM departures d

        LEFT JOIN arrivals a
            ON d.station_id = a.station_id;
        """
    )

    conn.execute(
        """
        CREATE OR REPLACE TABLE od_flow AS
        SELECT
            start_station_id,
            start_station_name,
            end_station_id,
            end_station_name,
            COUNT(*) AS rides
        FROM trips

        WHERE
            start_station_id IS NOT NULL
            AND end_station_id IS NOT NULL
            AND start_station_id != end_station_id

        GROUP BY
            start_station_id,
            start_station_name,
            end_station_id,
            end_station_name;
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