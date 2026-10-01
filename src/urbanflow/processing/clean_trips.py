import polars as pl


def clean_trips(
    trips: pl.LazyFrame,
    year: int,
    month: int,
) -> pl.LazyFrame:
    return (
        trips
        .with_columns(
            pl.col("started_at")
            .str.to_datetime(strict=False),

            pl.col("ended_at")
            .str.to_datetime(strict=False),

            pl.col("start_station_id")
            .cast(pl.String),

            pl.col("end_station_id")
            .cast(pl.String),
        )
        .filter(
            pl.col("ride_id").is_not_null(),
            pl.col("started_at").is_not_null(),
            pl.col("ended_at").is_not_null(),
            pl.col("ended_at") > pl.col("started_at"),
        )
        .filter(
            (pl.col("started_at").dt.year() == year)
            & (pl.col("started_at").dt.month() == month)
        )
        .with_columns(
            (
                pl.col("ended_at")
                - pl.col("started_at")
            )
            .dt.total_seconds()
            .truediv(60)
            .alias("duration_minutes"),

            pl.col("started_at")
            .dt.date()
            .alias("date"),

            pl.col("started_at")
            .dt.hour()
            .alias("hour"),

            pl.col("started_at")
            .dt.weekday()
            .alias("weekday"),

            pl.col("started_at")
            .dt.day()
            .alias("day"),

            pl.col("started_at")
            .dt.month()
            .alias("month"),
        )
    )