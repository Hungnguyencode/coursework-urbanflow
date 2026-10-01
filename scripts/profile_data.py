import polars as pl

SOURCE = "data/raw/citibike/2026-08/*.csv"


def load_trips() -> pl.LazyFrame:
    return (
        pl.scan_csv(
            SOURCE,
            schema_overrides={
                "start_station_id": pl.String,
                "end_station_id": pl.String,
            },
        )
        .with_columns(
            pl.col("started_at")
            .str.to_datetime(strict=False),

            pl.col("ended_at")
            .str.to_datetime(strict=False),
        )
    )


def main() -> None:
    trips = load_trips()

    print("\n" + "=" * 60)
    print("SCHEMA")
    print("=" * 60)

    print(trips.collect_schema())

    print("\n" + "=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)

    overview = trips.select(
        pl.len().alias("rows"),
        pl.col("ride_id")
        .n_unique()
        .alias("unique_ride_ids"),

        pl.col("started_at")
        .min()
        .alias("min_started_at"),

        pl.col("started_at")
        .max()
        .alias("max_started_at"),

        pl.col("ended_at")
        .min()
        .alias("min_ended_at"),

        pl.col("ended_at")
        .max()
        .alias("max_ended_at"),
    ).collect()

    print(overview)

    print("\n" + "=" * 60)
    print("NULL COUNTS")
    print("=" * 60)

    null_counts = (
        trips
        .select(
            [
                pl.col(column)
                .null_count()
                .alias(column)
                for column in trips.collect_schema().names()
            ]
        )
        .collect()
        .transpose(
            include_header=True,
            header_name="column",
            column_names=["null_count"],
        )
        .sort(
            "null_count",
            descending=True,
        )
    )

    print(null_counts)

    print("\n" + "=" * 60)
    print("DATA QUALITY")
    print("=" * 60)

    quality = trips.select(
        (
            pl.col("ended_at")
            <= pl.col("started_at")
        )
        .sum()
        .alias("non_positive_duration"),

        (
            ~pl.col("start_lat")
            .is_between(-90, 90)
        )
        .sum()
        .alias("invalid_start_lat"),

        (
            ~pl.col("start_lng")
            .is_between(-180, 180)
        )
        .sum()
        .alias("invalid_start_lng"),

        (
            ~pl.col("end_lat")
            .is_between(-90, 90)
        )
        .sum()
        .alias("invalid_end_lat"),

        (
            ~pl.col("end_lng")
            .is_between(-180, 180)
        )
        .sum()
        .alias("invalid_end_lng"),
    ).collect()

    print(quality)

    print("\n" + "=" * 60)
    print("MEMBER TYPE")
    print("=" * 60)

    member_counts = (
        trips
        .group_by("member_casual")
        .agg(
            pl.len().alias("rides")
        )
        .sort(
            "rides",
            descending=True,
        )
        .collect()
    )

    print(member_counts)

    print("\n" + "=" * 60)
    print("BIKE TYPE")
    print("=" * 60)

    bike_counts = (
        trips
        .group_by("rideable_type")
        .agg(
            pl.len().alias("rides")
        )
        .sort(
            "rides",
            descending=True,
        )
        .collect()
    )

    print(bike_counts)


if __name__ == "__main__":
    main()