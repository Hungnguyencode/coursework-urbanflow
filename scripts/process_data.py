import argparse

import polars as pl

from urbanflow.config import (
    AnalysisPeriod,
    latest_complete_month,
)
from urbanflow.processing.clean_trips import (
    clean_trips,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Clean Citi Bike trip data "
            "and write processed Parquet."
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


def process_period(
    period: AnalysisPeriod,
) -> None:
    source_pattern = str(
        period.raw_citibike_dir
        / "*.csv"
    )

    output_file = (
        period.trips_parquet
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_files = list(
        period.raw_citibike_dir.glob(
            "*.csv"
        )
    )

    if not csv_files:
        raise FileNotFoundError(
            "No Citi Bike CSV files found for "
            f"{period}: "
            f"{period.raw_citibike_dir}"
        )

    print()
    print("=" * 60)
    print("URBANFLOW TRIP PROCESSING")
    print("=" * 60)

    print(
        f"Period : {period}"
    )

    print(
        f"Source : {period.raw_citibike_dir}"
    )

    print(
        f"Files  : {len(csv_files)}"
    )

    print(
        f"Output : {output_file}"
    )

    print()
    print(
        "Reading raw Citi Bike files..."
    )

    trips = pl.scan_csv(
        source_pattern,
        schema_overrides={
            "start_station_id": pl.String,
            "end_station_id": pl.String,
        },
    )

    print(
        "Cleaning trips..."
    )

    cleaned = clean_trips(
        trips,
        year=period.year,
        month=period.month,
    )

    print(
        "Writing Parquet..."
    )

    cleaned.sink_parquet(
        output_file,
        compression="zstd",
    )

    print()
    print("=" * 60)
    print("PROCESSING COMPLETED")
    print("=" * 60)

    print(
        f"Period : {period}"
    )

    print(
        f"Output : {output_file}"
    )


def main() -> None:
    args = parse_args()

    period = resolve_period(
        args.period
    )

    process_period(
        period
    )


if __name__ == "__main__":
    main()