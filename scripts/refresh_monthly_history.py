
import argparse
import shutil

import build_monthly_history
import download_data
import download_weather
import process_data

from urbanflow.config import (
    AnalysisPeriod,
    latest_complete_month,
)
from urbanflow.ingestion.citibike import discover_archive


FIRST_PERIOD = AnalysisPeriod(2026, 8)


def periods_between(start, end):
    year, month = start.year, start.month

    while (year, month) <= (end.year, end.month):
        yield AnalysisPeriod(year, month)

        month += 1
        if month > 12:
            year += 1
            month = 1


def refresh_one(period, known_months, force, cleanup):
    key = str(period)

    if key in known_months and not force:
        print(f"[SKIP] {key}: already indexed")
        return "SKIPPED"

    print(f"\n[CHECK] Citi Bike archive for {key}")

    archive_key, actual_value = discover_archive(
        year=period.year,
        month=period.month,
    )

    actual = AnalysisPeriod.from_yyyymm(actual_value)

    # The fallback archive must NEVER be published
    # as though it belongs to the requested month.
    if actual != period:
        print(
            f"[WAIT] {period}: not published yet. "
            f"Latest available: {actual}"
        )
        return "WAITING"

    if not period.trips_parquet.exists():
        print(f"[INGEST] Trips: {period}")
        downloaded = download_data.ingest_citibike(period)

        if downloaded != period:
            raise RuntimeError(
                "Archive changed during ingestion."
            )

        process_data.process_period(period)
    else:
        print(f"[REUSE] Trips: {period}")

    if not period.weather_parquet.exists():
        print(f"[INGEST] Weather: {period}")
        download_weather.download_period_weather(period)
    else:
        print(f"[REUSE] Weather: {period}")

    # Validation happens inside build_month().
    # History is written only after it succeeds.
    record = build_monthly_history.update_month(period)
    known_months[key] = record

    if cleanup:
        raw_dir = period.raw_citibike_dir

        if raw_dir.exists():
            shutil.rmtree(raw_dir)

        archive_name = archive_key.rsplit("/", 1)[-1]
        archive_path = download_data.RAW_ROOT / archive_name

        if archive_path.exists():
            archive_path.unlink()

    print(f"[SUCCESS] Indexed {period}")
    return "UPDATED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", default=None)
    parser.add_argument("--cleanup-raw", action="store_true")
    parser.add_argument("--force-history", action="store_true")
    args = parser.parse_args()

    latest = latest_complete_month()

    if args.period:
        selected = AnalysisPeriod.from_yyyymm(args.period)
        targets = [selected]
    else:
        targets = list(periods_between(FIRST_PERIOD, latest))

    history = build_monthly_history.read_history()
    known_months = history.get("months", {})

    print("=" * 60)
    print("URBANFLOW HISTORICAL AUTO REFRESH")
    print("Research reference: 2026-08 (protected)")
    print("Latest complete calendar month:", latest)
    print("=" * 60)

    counts = {
        "UPDATED": 0,
        "SKIPPED": 0,
        "WAITING": 0,
    }

    for period in targets:
        if (
            period.yyyymm < FIRST_PERIOD.yyyymm
            or period.yyyymm > latest.yyyymm
        ):
            raise ValueError(
                f"Period {period} is outside eligible range."
            )

        result = refresh_one(
            period,
            known_months,
            args.force_history,
            args.cleanup_raw,
        )
        counts[result] += 1

    print("\n" + "=" * 60)
    print("HISTORICAL REFRESH COMPLETE")
    print("Added/updated :", counts["UPDATED"])
    print("Already saved :", counts["SKIPPED"])
    print("Not published :", counts["WAITING"])
    print("Research DuckDB: UNCHANGED")
    print("=" * 60)


if __name__ == "__main__":
    main()
