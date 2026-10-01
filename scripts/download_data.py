from pathlib import Path

from urbanflow.ingestion.citibike import (
    download_month,
    extract_zip,
)


RAW_DIR = Path(
    "data/raw/citibike"
)


def main() -> None:
    requested_year = 2026
    requested_month = 8

    zip_path, actual_period = download_month(
        year=requested_year,
        month=requested_month,
        output_dir=RAW_DIR,
    )

    year = actual_period[:4]
    month = actual_period[4:]

    extract_dir = (
        RAW_DIR
        / f"{year}-{month}"
    )

    csv_files = extract_zip(
        zip_path=zip_path,
        output_dir=extract_dir,
    )

    print()
    print("=" * 60)
    print("Citi Bike ingestion completed")
    print("=" * 60)

    print(
        f"Requested period : "
        f"{requested_year}-{requested_month:02d}"
    )

    print(
        f"Actual period    : "
        f"{year}-{month}"
    )

    print(
        f"Archive          : "
        f"{zip_path}"
    )

    print(
        f"CSV files        : "
        f"{len(csv_files)}"
    )

    print(
        f"Extracted to     : "
        f"{extract_dir}"
    )


if __name__ == "__main__":
    main()