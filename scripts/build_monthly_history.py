
import argparse
import json
from calendar import monthrange
from datetime import datetime
from pathlib import Path

import duckdb

from urbanflow.config import AnalysisPeriod, PROJECT_ROOT


HISTORY_PATH = (
    PROJECT_ROOT / "dashboard" / "data" / "monthly_history.json"
)

TRIPS_DIR = PROJECT_ROOT / "data" / "processed" / "trips"


def read_history():
    if not HISTORY_PATH.exists():
        return {"schema_version": 1, "months": {}}

    data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported monthly history schema.")

    return data


def build_month(period: AnalysisPeriod):
    trips_path = period.trips_parquet
    weather_path = period.weather_parquet

    if not trips_path.exists() or not weather_path.exists():
        raise FileNotFoundError(
            f"Missing processed Parquet files for {period}"
        )

    days = monthrange(period.year, period.month)[1]
    expected_hours = days * 24

    con = duckdb.connect(":memory:")

    try:
        summary = con.execute(
            """
            SELECT
                COUNT(*) AS total_rides,
                COUNT(DISTINCT ride_id) AS unique_rides,
                COUNT(DISTINCT date) AS observed_days,
                MIN(date) AS first_date,
                MAX(date) AS last_date,
                MEDIAN(duration_minutes) AS median_duration,
                COUNT(*) FILTER (
                    WHERE member_casual = 'member'
                ) AS member_rides,
                COUNT(*) FILTER (
                    WHERE rideable_type = 'electric_bike'
                ) AS electric_rides
            FROM read_parquet(?)
            """,
            [str(trips_path)],
        ).fetchone()

        weather = con.execute(
            """
            SELECT
                COUNT(*) AS weather_hours,
                COUNT(precipitation_mm) AS valid_rain_hours,
                COUNT(*) FILTER (
                    WHERE precipitation_mm > 0
                ) AS wet_hours,
                AVG(temperature_c) AS mean_temp
            FROM read_parquet(?)
            """,
            [str(weather_path)],
        ).fetchone()

        (
            total,
            unique,
            observed_days,
            first_date,
            last_date,
            median_duration,
            members,
            electric,
        ) = summary

        if total <= 0 or total != unique:
            raise ValueError(f"Invalid ride IDs for {period}")

        if (
            observed_days != days
            or first_date != period.start_date
            or last_date != period.end_date
        ):
            raise ValueError(f"Incomplete trip date coverage: {period}")

        if weather[0] != expected_hours or weather[1] != expected_hours:
            raise ValueError(f"Incomplete weather coverage: {period}")

        rows = con.execute(
            """
            WITH hourly_rides AS (
                SELECT date, hour, COUNT(*) AS rides
                FROM read_parquet(?)
                GROUP BY date, hour
            )
            SELECT
                CAST(r.date AS VARCHAR) AS ride_date,
                r.hour,
                r.rides,
                w.precipitation_mm
            FROM hourly_rides r
            INNER JOIN read_parquet(?) w
              ON r.date = w.date AND r.hour = w.hour
            ORDER BY r.date, r.hour
            """,
            [str(trips_path), str(weather_path)],
        ).fetchall()

    finally:
        con.close()

    if len(rows) != expected_hours:
        raise ValueError(f"Incomplete hourly join for {period}")

    if sum(int(r[2]) for r in rows) != total:
        raise ValueError(f"Hourly trip total mismatch for {period}")

    daily_map = {}
    hourly_data = []

    for date_str, hour, rides, rain in rows:
        date_str = str(date_str)
        rides = int(rides)
        rain = float(rain)

        if date_str not in daily_map:
            daily_map[date_str] = {
                "date": date_str,
                "rides": 0,
                "rainfall_mm": 0.0,
            }

        daily_map[date_str]["rides"] += rides
        daily_map[date_str]["rainfall_mm"] += rain

        hourly_data.append({
            "date": date_str,
            "hour": int(hour),
            "rides": rides,
            "precipitation_mm": round(rain, 4),
        })

    daily_data = list(daily_map.values())

    for row in daily_data:
        row["rainfall_mm"] = round(row["rainfall_mm"], 3)

    return {
        "period": str(period),
        "total_rides": int(total),
        "days": days,
        "avg_per_day": round(total / days, 4),
        "median_duration": round(float(median_duration), 4),
        "member_share": round(members / total * 100, 5),
        "electric_share": round(electric / total * 100, 5),
        "weather_hours": int(weather[0]),
        "wet_hours": int(weather[2]),
        "wet_hour_share": round(
            weather[2] / weather[0] * 100, 5
        ),
        "mean_temperature": round(float(weather[3]), 4),
        "daily": daily_data,
        "hourly": hourly_data,
    }


def update_month(period: AnalysisPeriod):
    record = build_month(period)
    history = read_history()

    # Upsert: rebuild the month if it exists, never duplicate it.
    history["months"][str(period)] = record
    history["months"] = dict(sorted(history["months"].items()))
    history["updated_at"] = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = HISTORY_PATH.with_suffix(".json.tmp")

    temp_path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(HISTORY_PATH)

    print(
        f"[HISTORY SAVED] {period}: "
        f"{record['total_rides']:,} trips | "
        f"{record['avg_per_day']:,.0f} rides/day"
    )

    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", help="YYYYMM")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.period:
        periods = [AnalysisPeriod.from_yyyymm(args.period)]
    else:
        periods = []
        for path in sorted(TRIPS_DIR.glob("trips_????_??.parquet")):
            suffix = path.stem.removeprefix("trips_").replace("_", "")
            period = AnalysisPeriod.from_yyyymm(suffix)

            if period.yyyymm < "202608":
                continue

            if period.weather_parquet.exists():
                periods.append(period)

    if not periods:
        raise RuntimeError("No eligible monthly Parquet pairs found.")

    for period in periods:
        update_month(period)

    print("MONTHLY HISTORY BUILD COMPLETE")


if __name__ == "__main__":
    main()
