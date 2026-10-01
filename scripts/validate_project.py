from pathlib import Path

import duckdb
import polars as pl


TRIPS_PARQUET = Path(
    "data/processed/trips/trips_2026_08.parquet"
)

WEATHER_PARQUET = Path(
    "data/processed/weather/weather_2026_08.parquet"
)

DATABASE = Path(
    "data/analytics/urbanflow.duckdb"
)


def check_file(
    path: Path,
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


def check_trips() -> None:
    df = pl.scan_parquet(
        TRIPS_PARQUET
    )

    result = (
        df.select(
            pl.len().alias("rows"),

            pl.col("ride_id")
            .n_unique()
            .alias("unique_rides"),

            pl.col("started_at")
            .min()
            .alias("min_started_at"),

            pl.col("started_at")
            .max()
            .alias("max_started_at"),
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


def check_weather() -> None:
    df = pl.read_parquet(
        WEATHER_PARQUET
    )

    if df.height != 744:
        raise ValueError(
            "Weather dataset should "
            f"contain 744 rows, got {df.height}."
        )

    nulls = (
        df.null_count()
        .sum_horizontal()
        .item()
    )

    if nulls != 0:
        raise ValueError(
            f"Weather contains {nulls} nulls."
        )

    print(
        "[PASS] Weather: "
        "744 hourly observations"
    )

    print(
        "[PASS] Weather nulls: 0"
    )


def check_database() -> None:
    con = duckdb.connect(
        str(DATABASE),
        read_only=True,
    )

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

    weather_rows = con.execute(
        """
        SELECT COUNT(*)
        FROM weather_ride_hourly;
        """
    ).fetchone()[0]

    if weather_rows != 744:
        raise ValueError(
            "weather_ride_hourly "
            f"contains {weather_rows} rows."
        )

    invalid_imbalance = con.execute(
        """
        SELECT COUNT(*)
        FROM station_metrics
        WHERE
            imbalance_ratio < 0
            OR imbalance_ratio > 1;
        """
    ).fetchone()[0]

    if invalid_imbalance != 0:
        raise ValueError(
            "Invalid station "
            "imbalance ratios detected."
        )

    print(
        "[PASS] DuckDB objects: "
        f"{len(required_objects)}"
    )

    print(
        "[PASS] Weather join: "
        "744 / 744 hours"
    )

    print(
        "[PASS] Station imbalance: "
        "0%–100%"
    )

    con.close()


def main() -> None:
    print()
    print("=" * 60)
    print("URBANFLOW PROJECT HEALTH CHECK")
    print("=" * 60)

    check_file(
        TRIPS_PARQUET,
        "Trip Parquet",
    )

    check_file(
        WEATHER_PARQUET,
        "Weather Parquet",
    )

    check_file(
        DATABASE,
        "DuckDB database",
    )

    print()

    check_trips()

    print()

    check_weather()

    print()

    check_database()

    print()
    print("=" * 60)
    print("ALL CHECKS PASSED ✅")
    print("=" * 60)


if __name__ == "__main__":
    main()