from pathlib import Path

import httpx
import polars as pl

ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


def download_weather(
    start_date: str,
    end_date: str,
    output_path: Path,
) -> Path:
    """
    Download hourly historical weather for New York City.

    A single city-level location is used as a weather proxy
    for the Citi Bike service area.
    """

    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "timezone": "America/New_York",
    }

    print(
        f"Downloading weather: "
        f"{start_date} → {end_date}"
    )

    response = httpx.get(
        ARCHIVE_URL,
        params=params,
        timeout=60.0,
        follow_redirects=True,
    )

    response.raise_for_status()

    payload = response.json()

    hourly = payload["hourly"]

    df = pl.DataFrame(
        {
            "timestamp": hourly["time"],
            "temperature_c":
                hourly["temperature_2m"],
            "relative_humidity_pct":
                hourly["relative_humidity_2m"],
            "precipitation_mm":
                hourly["precipitation"],
            "wind_speed_kmh":
                hourly["wind_speed_10m"],
        }
    ).with_columns(
        pl.col("timestamp")
        .str.to_datetime(
            strict=False,
        )
    ).with_columns(
        pl.col("timestamp")
        .dt.date()
        .alias("date"),

        pl.col("timestamp")
        .dt.hour()
        .alias("hour"),
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.write_parquet(
        output_path,
        compression="zstd",
    )

    print(
        f"Weather rows: {df.height}"
    )

    print(
        f"Saved: {output_path}"
    )

    return output_path