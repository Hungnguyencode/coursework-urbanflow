import argparse
import json
import shutil
from datetime import datetime

import build_database
import download_data
import download_weather
import process_data
import validate_project

from urbanflow.config import (
    DATA_DIR,
    DATABASE_PATH,
    AnalysisPeriod,
    latest_complete_month,
)
from urbanflow.ingestion.citibike import (
    discover_archive,
)

METADATA_PATH = (
    DATA_DIR
    / "analytics"
    / "refresh_metadata.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete UrbanFlow "
            "data refresh pipeline."
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

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Re-download and rebuild processed "
            "datasets even when they already exist."
        ),
    )

    parser.add_argument(
        "--cleanup-raw",
        action="store_true",
        help=(
            "Delete downloaded Citi Bike ZIP "
            "and extracted CSV files after a "
            "successful refresh."
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


def resolve_available_period(
    requested_period: AnalysisPeriod,
) -> tuple[
    AnalysisPeriod,
    str,
]:
    archive_key, actual_value = (
        discover_archive(
            year=requested_period.year,
            month=requested_period.month,
        )
    )

    actual_period = (
        AnalysisPeriod.from_yyyymm(
            actual_value
        )
    )

    return (
        actual_period,
        archive_key,
    )


def write_refresh_metadata(
    requested_period: AnalysisPeriod,
    actual_period: AnalysisPeriod,
) -> None:
    METADATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = {
        "requested_period": str(
            requested_period
        ),
        "active_period": str(
            actual_period
        ),
        "last_refresh": (
            datetime.now()
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        ),
        "trips_parquet": str(
            actual_period.trips_parquet
        ),
        "weather_parquet": str(
            actual_period.weather_parquet
        ),
        "database": str(
            DATABASE_PATH
        ),
    }

    METADATA_PATH.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "[SAVED] Refresh metadata: "
        f"{METADATA_PATH}"
    )


def cleanup_raw_files(
    period: AnalysisPeriod,
    archive_key: str,
) -> None:
    raw_directory = (
        period.raw_citibike_dir
    )

    archive_name = (
        archive_key
        .rsplit("/", 1)[-1]
    )

    archive_path = (
        download_data.RAW_ROOT
        / archive_name
    )

    print()
    print("=" * 60)
    print("RAW DATA CLEANUP")
    print("=" * 60)

    if raw_directory.exists():
        shutil.rmtree(
            raw_directory
        )

        print(
            "[REMOVED] "
            f"{raw_directory}"
        )

    if archive_path.exists():
        archive_path.unlink()

        print(
            "[REMOVED] "
            f"{archive_path}"
        )


def run_pipeline(
    requested_period: AnalysisPeriod,
    *,
    force: bool = False,
    cleanup_raw: bool = False,
) -> AnalysisPeriod:
    print()
    print("=" * 60)
    print("URBANFLOW AUTOMATIC REFRESH")
    print("=" * 60)

    print(
        "Requested period: "
        f"{requested_period}"
    )

    print()
    print(
        "Checking Citi Bike "
        "data availability..."
    )

    (
        actual_period,
        archive_key,
    ) = resolve_available_period(
        requested_period
    )

    print(
        "Available period: "
        f"{actual_period}"
    )

    if (
        actual_period
        != requested_period
    ):
        print(
            "[INFO] Requested month "
            "is not available yet."
        )

        print(
            "[INFO] Pipeline will use "
            f"{actual_period} instead."
        )

    print()
    print("=" * 60)
    print("STEP 1/5 — TRIP DATA")
    print("=" * 60)

    if (
        actual_period.trips_parquet.exists()
        and not force
    ):
        print(
            "[REUSE] Processed trips "
            "already exist:"
        )

        print(
            actual_period.trips_parquet
        )

    else:
        ingested_period = (
            download_data.ingest_citibike(
                requested_period
            )
        )

        if (
            ingested_period
            != actual_period
        ):
            raise RuntimeError(
                "Citi Bike availability "
                "changed during refresh."
            )

        process_data.process_period(
            actual_period
        )

    print()
    print("=" * 60)
    print("STEP 2/5 — WEATHER DATA")
    print("=" * 60)

    if (
        actual_period.weather_parquet.exists()
        and not force
    ):
        print(
            "[REUSE] Weather data "
            "already exist:"
        )

        print(
            actual_period.weather_parquet
        )

    else:
        (
            download_weather
            .download_period_weather(
                actual_period
            )
        )

    print()
    print("=" * 60)
    print("STEP 3/5 — ANALYTICS DATABASE")
    print("=" * 60)

    build_database.build_database(
        actual_period
    )

    print()
    print("=" * 60)
    print("STEP 4/5 — VALIDATION")
    print("=" * 60)

    validate_project.validate_period(
        actual_period
    )

    print()
    print("=" * 60)
    print("STEP 5/5 — REFRESH METADATA")
    print("=" * 60)

    write_refresh_metadata(
        requested_period,
        actual_period,
    )

    if cleanup_raw:
        cleanup_raw_files(
            actual_period,
            archive_key,
        )

    print()
    print("=" * 60)
    print("URBANFLOW REFRESH COMPLETE ✅")
    print("=" * 60)

    print(
        "Active period : "
        f"{actual_period}"
    )

    print(
        "Database      : "
        f"{DATABASE_PATH}"
    )

    return actual_period


def main() -> None:
    args = parse_args()

    requested_period = (
        resolve_requested_period(
            args.period
        )
    )

    run_pipeline(
        requested_period,
        force=args.force,
        cleanup_raw=args.cleanup_raw,
    )


if __name__ == "__main__":
    main()