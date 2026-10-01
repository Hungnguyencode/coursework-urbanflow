from pathlib import Path

import polars as pl

from urbanflow.processing.clean_trips import clean_trips


SOURCE = "data/raw/citibike/2026-08/*.csv"

OUTPUT_DIR = Path(
    "data/processed/trips"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "trips_2026_08.parquet"
)


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Reading raw Citi Bike files...")

    trips = pl.scan_csv(
        SOURCE,
        schema_overrides={
            "start_station_id": pl.String,
            "end_station_id": pl.String,
        },
    )

    print("Cleaning trips...")

    cleaned = clean_trips(
        trips,
        year=2026,
        month=8,
    )

    print("Writing Parquet...")

    cleaned.sink_parquet(
        OUTPUT_FILE,
        compression="zstd",
    )

    print()
    print("=" * 60)
    print("PROCESSING COMPLETED")
    print("=" * 60)

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()