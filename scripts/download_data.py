import argparse

from urbanflow.config import (
    DATA_DIR,
    AnalysisPeriod,
    latest_complete_month,
)
from urbanflow.ingestion.citibike import (
    download_month,
    extract_zip,
)

RAW_ROOT = (
    DATA_DIR
    / "raw"
    / "citibike"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download and extract Citi Bike "
            "monthly trip data."
        )
    )

    parser.add_argument(
        "--period",
        type=str,
        default=None,
        help=(
            "Requested month in YYYYMM format. "
            "Defaults to the latest complete month."
        ),
    )

    return parser.parse_args()


def resolve_requested_period(
    value: str | None,
) -> AnalysisPeriod:
    if value is not None:
        return AnalysisPeriod.from_yyyymm(
            value
        )

    return latest_complete_month()


def ingest_citibike(
    requested_period: AnalysisPeriod,
) -> AnalysisPeriod:
    print()
    print("=" * 60)
    print("CITI BIKE INGESTION")
    print("=" * 60)

    print(
        "Requested period: "
        f"{requested_period}"
    )

    zip_path, actual_period_value = (
        download_month(
            year=requested_period.year,
            month=requested_period.month,
            output_dir=RAW_ROOT,
        )
    )

    actual_period = (
        AnalysisPeriod.from_yyyymm(
            actual_period_value
        )
    )

    if actual_period != requested_period:
        print()
        print(
            "Requested month is not available."
        )
        print(
            "Using latest available period: "
            f"{actual_period}"
        )

    csv_files = extract_zip(
        zip_path=zip_path,
        output_dir=(
            actual_period.raw_citibike_dir
        ),
    )

    print()
    print("=" * 60)
    print("CITI BIKE INGESTION COMPLETED")
    print("=" * 60)

    print(
        "Requested period : "
        f"{requested_period}"
    )

    print(
        "Actual period    : "
        f"{actual_period}"
    )

    print(
        "Archive          : "
        f"{zip_path}"
    )

    print(
        "CSV files        : "
        f"{len(csv_files)}"
    )

    print(
        "Extracted to     : "
        f"{actual_period.raw_citibike_dir}"
    )

    return actual_period


def main() -> None:
    args = parse_args()

    requested_period = (
        resolve_requested_period(
            args.period
        )
    )

    ingest_citibike(
        requested_period
    )


if __name__ == "__main__":
    main()