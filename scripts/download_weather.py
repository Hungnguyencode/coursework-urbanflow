import argparse

from urbanflow.config import (
    AnalysisPeriod,
    latest_complete_month,
)
from urbanflow.ingestion.weather import (
    download_weather,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download historical weather data "
            "for an UrbanFlow analysis month."
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


def download_period_weather(
    period: AnalysisPeriod,
) -> None:
    output_path = (
        period.weather_parquet
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 60)
    print("URBANFLOW WEATHER INGESTION")
    print("=" * 60)

    print(
        f"Period : {period}"
    )

    print(
        "Start  : "
        f"{period.start_date}"
    )

    print(
        "End    : "
        f"{period.end_date}"
    )

    print(
        "Hours  : "
        f"{period.expected_hours}"
    )

    print(
        f"Output : {output_path}"
    )

    download_weather(
        start_date=(
            period.start_date.isoformat()
        ),
        end_date=(
            period.end_date.isoformat()
        ),
        output_path=output_path,
    )

    print()
    print("=" * 60)
    print("WEATHER INGESTION COMPLETED")
    print("=" * 60)


def main() -> None:
    args = parse_args()

    period = resolve_period(
        args.period
    )

    download_period_weather(
        period
    )


if __name__ == "__main__":
    main()