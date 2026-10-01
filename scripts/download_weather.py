from pathlib import Path

from urbanflow.ingestion.weather import (
    download_weather,
)

OUTPUT = Path(
    "data/processed/weather/"
    "weather_2026_08.parquet"
)


def main() -> None:
    download_weather(
        start_date="2026-08-01",
        end_date="2026-08-31",
        output_path=OUTPUT,
    )


if __name__ == "__main__":
    main()