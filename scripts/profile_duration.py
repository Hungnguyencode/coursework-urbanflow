from urbanflow.analytics.database import get_connection


def main() -> None:
    conn = get_connection()

    result = conn.execute(
        """
        SELECT
            COUNT(*) AS rides,

            MIN(duration_minutes)
                AS min_minutes,

            QUANTILE_CONT(
                duration_minutes,
                0.50
            ) AS p50_minutes,

            QUANTILE_CONT(
                duration_minutes,
                0.95
            ) AS p95_minutes,

            QUANTILE_CONT(
                duration_minutes,
                0.99
            ) AS p99_minutes,

            AVG(duration_minutes)
                AS avg_minutes,

            MAX(duration_minutes)
                AS max_minutes

        FROM trips;
        """
    ).fetchdf()

    print()
    print("=" * 60)
    print("RIDE DURATION PROFILE")
    print("=" * 60)

    print(result.to_string(index=False))

    print()
    print("=" * 60)
    print("EXTREME RIDES")
    print("=" * 60)

    extreme = conn.execute(
        """
        SELECT
            ride_id,
            started_at,
            ended_at,
            duration_minutes,
            member_casual,
            rideable_type

        FROM trips

        ORDER BY
            duration_minutes DESC

        LIMIT 10;
        """
    ).fetchdf()

    print(extreme.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()