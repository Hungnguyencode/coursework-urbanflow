from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

DATABASE_PATH = (
    DATA_DIR
    / "analytics"
    / "urbanflow.duckdb"
)


@dataclass(
    frozen=True,
)
class AnalysisPeriod:
    year: int
    month: int

    def __post_init__(
        self,
    ) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(
                "month must be between 1 and 12"
            )

    @property
    def yyyymm(
        self,
    ) -> str:
        return (
            f"{self.year}"
            f"{self.month:02d}"
        )

    @property
    def folder_name(
        self,
    ) -> str:
        return (
            f"{self.year}-"
            f"{self.month:02d}"
        )

    @property
    def file_suffix(
        self,
    ) -> str:
        return (
            f"{self.year}_"
            f"{self.month:02d}"
        )

    @property
    def start_date(
        self,
    ) -> date:
        return date(
            self.year,
            self.month,
            1,
        )

    @property
    def end_date(
        self,
    ) -> date:
        last_day = monthrange(
            self.year,
            self.month,
        )[1]

        return date(
            self.year,
            self.month,
            last_day,
        )

    @property
    def expected_hours(
        self,
    ) -> int:
        days = monthrange(
            self.year,
            self.month,
        )[1]

        return days * 24

    @property
    def raw_citibike_dir(
        self,
    ) -> Path:
        return (
            DATA_DIR
            / "raw"
            / "citibike"
            / self.folder_name
        )

    @property
    def trips_parquet(
        self,
    ) -> Path:
        return (
            DATA_DIR
            / "processed"
            / "trips"
            / (
                "trips_"
                f"{self.file_suffix}"
                ".parquet"
            )
        )

    @property
    def weather_parquet(
        self,
    ) -> Path:
        return (
            DATA_DIR
            / "processed"
            / "weather"
            / (
                "weather_"
                f"{self.file_suffix}"
                ".parquet"
            )
        )

    @classmethod
    def from_yyyymm(
        cls,
        value: str,
    ) -> "AnalysisPeriod":
        if (
            len(value) != 6
            or not value.isdigit()
        ):
            raise ValueError(
                "Period must use YYYYMM format."
            )

        return cls(
            year=int(value[:4]),
            month=int(value[4:]),
        )

    def __str__(
        self,
    ) -> str:
        return self.folder_name


def latest_complete_month(
    today: date | None = None,
) -> AnalysisPeriod:
    current = (
        today
        if today is not None
        else (
            datetime.now(
                tz=UTC
            )
            .astimezone()
            .date()
        )
    )

    if current.month == 1:
        return AnalysisPeriod(
            current.year - 1,
            12,
        )

    return AnalysisPeriod(
        current.year,
        current.month - 1,
    )