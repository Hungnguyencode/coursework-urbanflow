import argparse

import duckdb
import polars as pl

from urbanflow.config import (
    DATABASE_PATH,
    AnalysisPeriod,
    latest_complete_month,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate UrbanFlow processed data "
            "and analytics outputs."
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


def check_file(
    path,
    label: str,
) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"{label} not found: {path}"
        )

    size_mb = (
        path.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"[PASS] {label}: "
        f"{size_mb:.2f} MB"
    )


def check_trips(
    period: AnalysisPeriod,
) -> None:
    df = pl.scan_parquet(
        period.trips_parquet
    )

    result = (
        df.select(
            pl.len().alias(
                "rows"
            ),

            pl.col("ride_id")
            .n_unique()
            .alias(
                "unique_rides"
            ),

            pl.col("started_at")
            .min()
            .alias(
                "min_started_at"
            ),

            pl.col("started_at")
            .max()
            .alias(
                "max_started_at"
            ),

            pl.col("duration_minutes")
            .min()
            .alias(
                "min_duration"
            ),
        )
        .collect()
        .row(
            0,
            named=True,
        )
    )

    if result["rows"] <= 0:
        raise ValueError(
            "Trip dataset is empty."
        )

    if (
        result["rows"]
        != result["unique_rides"]
    ):
        raise ValueError(
            "Duplicate ride IDs detected."
        )

    if result["min_duration"] <= 0:
        raise ValueError(
            "Non-positive trip duration detected."
        )

    min_date = (
        result["min_started_at"]
        .date()
    )

    max_date = (
        result["max_started_at"]
        .date()
    )

    if min_date != period.start_date:
        raise ValueError(
            "Trip dataset starts on "
            f"{min_date}, expected "
            f"{period.start_date}."
        )

    if max_date != period.end_date:
        raise ValueError(
            "Trip dataset ends on "
            f"{max_date}, expected "
            f"{period.end_date}."
        )

    print(
        "[PASS] Trips: "
        f"{result['rows']:,} rows"
    )

    print(
        "[PASS] Unique ride IDs: "
        f"{result['unique_rides']:,}"
    )

    print(
        "[PASS] Trip range: "
        f"{result['min_started_at']} "
        "→ "
        f"{result['max_started_at']}"
    )

    print(
        "[PASS] Trip durations: "
        "all positive"
    )


def check_weather(
    period: AnalysisPeriod,
) -> None:
    df = pl.read_parquet(
        period.weather_parquet
    )

    if df.height != period.expected_hours:
        raise ValueError(
            "Weather dataset should contain "
            f"{period.expected_hours} rows, "
            f"got {df.height}."
        )

    nulls = (
        df.null_count()
        .sum_horizontal()
        .item()
    )

    if nulls != 0:
        raise ValueError(
            "Weather dataset contains "
            f"{nulls} null values."
        )

    min_date = (
        df["timestamp"]
        .min()
        .date()
    )

    max_date = (
        df["timestamp"]
        .max()
        .date()
    )

    if min_date != period.start_date:
        raise ValueError(
            "Weather dataset starts on "
            f"{min_date}, expected "
            f"{period.start_date}."
        )

    if max_date != period.end_date:
        raise ValueError(
            "Weather dataset ends on "
            f"{max_date}, expected "
            f"{period.end_date}."
        )

    print(
        "[PASS] Weather: "
        f"{period.expected_hours} "
        "hourly observations"
    )

    print(
        "[PASS] Weather nulls: 0"
    )

    print(
        "[PASS] Weather range: "
        f"{period.start_date} → "
        f"{period.end_date}"
    )


def check_database(
    period: AnalysisPeriod,
) -> None:
    con = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        required_objects = {
            "trips",
            "daily_metrics",
            "hourly_metrics",
            "station_metrics",
            "od_flow",
            "weather",
            "weather_ride_hourly",
        }

        tables = con.execute(
            """
            SHOW ALL TABLES;
            """
        ).fetchdf()

        existing = set(
            tables["name"].tolist()
        )

        missing = (
            required_objects
            - existing
        )

        if missing:
            raise ValueError(
                "Missing DuckDB objects: "
                f"{sorted(missing)}"
            )

        (
            min_date,
            max_date,
        ) = con.execute(
            """
            SELECT
                MIN(date),
                MAX(date)
            FROM trips;
            """
        ).fetchone()

        if min_date != period.start_date:
            raise ValueError(
                "DuckDB trips start on "
                f"{min_date}, expected "
                f"{period.start_date}."
            )

        if max_date != period.end_date:
            raise ValueError(
                "DuckDB trips end on "
                f"{max_date}, expected "
                f"{period.end_date}."
            )

        weather_rows = con.execute(
            """
            SELECT COUNT(*)
            FROM weather;
            """
        ).fetchone()[0]

        if (
            weather_rows
            != period.expected_hours
        ):
            raise ValueError(
                "DuckDB weather view contains "
                f"{weather_rows} rows, expected "
                f"{period.expected_hours}."
            )

        joined_rows = con.execute(
            """
            SELECT COUNT(*)
            FROM weather_ride_hourly;
            """
        ).fetchone()[0]

        if (
            joined_rows
            != period.expected_hours
        ):
            raise ValueError(
                "weather_ride_hourly contains "
                f"{joined_rows} rows, expected "
                f"{period.expected_hours}."
            )

        invalid_imbalance = (
            con.execute(
                """
                SELECT COUNT(*)
                FROM station_metrics
                WHERE
                    imbalance_ratio < 0
                    OR imbalance_ratio > 1;
                """
            )
            .fetchone()[0]
        )

        if invalid_imbalance != 0:
            raise ValueError(
                "Invalid station "
                "imbalance ratios detected."
            )

        avg_demand_index = (
            con.execute(
                """
                SELECT AVG(demand_index)
                FROM weather_ride_hourly;
                """
            )
            .fetchone()[0]
        )

        if not (
            0.99
            <= avg_demand_index
            <= 1.01
        ):
            raise ValueError(
                "Demand index is not "
                "properly normalized: "
                f"{avg_demand_index:.3f}"
            )

        print(
            "[PASS] DuckDB objects: "
            f"{len(required_objects)}"
        )

        print(
            "[PASS] DuckDB period: "
            f"{period}"
        )

        print(
            "[PASS] Weather join: "
            f"{joined_rows} / "
            f"{period.expected_hours} hours"
        )

        print(
            "[PASS] Demand index: "
            f"{avg_demand_index:.3f}"
        )

        print(
            "[PASS] Station imbalance: "
            "0%–100%"
        )

    finally:
        con.close()


def validate_period(
    period: AnalysisPeriod,
) -> None:
    print()
    print("=" * 60)
    print("URBANFLOW PROJECT HEALTH CHECK")
    print("=" * 60)

    print(
        f"Period: {period}"
    )

    print()

    check_file(
        period.trips_parquet,
        "Trip Parquet",
    )

    check_file(
        period.weather_parquet,
        "Weather Parquet",
    )

    check_file(
        DATABASE_PATH,
        "DuckDB database",
    )

    print()

    check_trips(
        period
    )

    print()

    check_weather(
        period
    )

    print()

    check_database(
        period
    )

    print()
    print("=" * 60)
    print("ALL CHECKS PASSED ✅")
    print("=" * 60)


def main() -> None:
    args = parse_args()

    period = resolve_period(
        args.period
    )

    validate_period(
        period
    )


if __name__ == "__main__":
    main()