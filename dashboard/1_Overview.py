from datetime import date
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st
from components.charts import style_figure
from components.filters import render_trip_filters
from components.kpis import metric_row

DATABASE_PATH = Path(
    "data/analytics/urbanflow.duckdb"
)

ANALYSIS_START = date(
    2026,
    8,
    1,
)

ANALYSIS_END = date(
    2026,
    8,
    31,
)


st.set_page_config(
    page_title="UrbanFlow",
    page_icon="🚲",
    layout="wide",
)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------


@st.cache_resource
def get_connection():
    return duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )


# ---------------------------------------------------------
# FILTER HELPERS
# ---------------------------------------------------------


def build_trip_filter(
    start_date,
    end_date,
    rider_type=None,
    bike_type=None,
):
    conditions = [
        "date BETWEEN ? AND ?",
    ]

    parameters = [
        start_date,
        end_date,
    ]

    if rider_type is not None:
        conditions.append(
            "member_casual = ?"
        )

        parameters.append(
            rider_type
        )

    if bike_type is not None:
        conditions.append(
            "rideable_type = ?"
        )

        parameters.append(
            bike_type
        )

    where_clause = (
        " WHERE "
        + " AND ".join(conditions)
    )

    return (
        where_clause,
        parameters,
    )


# ---------------------------------------------------------
# DATA LOADERS
# ---------------------------------------------------------


@st.cache_data
def load_summary(
    start_date,
    end_date,
    rider_type,
    bike_type,
):
    conn = get_connection()

    where_clause, params = (
        build_trip_filter(
            start_date,
            end_date,
            rider_type,
            bike_type,
        )
    )

    query = f"""
        SELECT
            COUNT(*) AS total_rides,

            MEDIAN(
                duration_minutes
            ) AS median_duration,

            AVG(
                CASE
                    WHEN member_casual = 'member'
                    THEN 1
                    ELSE 0
                END
            ) * 100 AS member_share,

            AVG(
                CASE
                    WHEN rideable_type = 'electric_bike'
                    THEN 1
                    ELSE 0
                END
            ) * 100 AS electric_share

        FROM trips

        {where_clause};
    """

    return conn.execute(
        query,
        params,
    ).fetchdf()


@st.cache_data
def load_daily_metrics(
    start_date,
    end_date,
    rider_type,
    bike_type,
):
    conn = get_connection()

    where_clause, params = (
        build_trip_filter(
            start_date,
            end_date,
            rider_type,
            bike_type,
        )
    )

    query = f"""
        SELECT
            date,
            COUNT(*) AS rides

        FROM trips

        {where_clause}

        GROUP BY date

        ORDER BY date;
    """

    return conn.execute(
        query,
        params,
    ).fetchdf()


@st.cache_data
def load_member_breakdown(
    start_date,
    end_date,
    rider_type,
    bike_type,
):
    conn = get_connection()

    where_clause, params = (
        build_trip_filter(
            start_date,
            end_date,
            rider_type,
            bike_type,
        )
    )

    query = f"""
        SELECT
            member_casual,
            COUNT(*) AS rides

        FROM trips

        {where_clause}

        GROUP BY member_casual

        ORDER BY rides DESC;
    """

    return conn.execute(
        query,
        params,
    ).fetchdf()


@st.cache_data
def load_top_stations(
    start_date,
    end_date,
    rider_type,
    bike_type,
):
    conn = get_connection()

    where_clause, params = (
        build_trip_filter(
            start_date,
            end_date,
            rider_type,
            bike_type,
        )
    )

    query = f"""
        SELECT
            start_station_name
                AS station_name,

            COUNT(*) AS departures

        FROM trips

        {where_clause}

            AND start_station_name
                IS NOT NULL

        GROUP BY
            start_station_name

        ORDER BY
            departures DESC

        LIMIT 10;
    """

    return conn.execute(
        query,
        params,
    ).fetchdf()


# ---------------------------------------------------------
# FORMAT HELPERS
# ---------------------------------------------------------


def format_ride_count(
    value: int,
) -> str:
    if value >= 1_000_000:
        return (
            f"{value / 1_000_000:.2f}M"
        )

    if value >= 1_000:
        return (
            f"{value / 1_000:.1f}K"
        )

    return f"{value:,}"


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------


st.title(
    "UrbanFlow 🚲"
)

st.caption(
    "Urban Mobility Analytics & Visualization Platform"
)

st.markdown(
    """
    Exploring Citi Bike mobility patterns across
    New York City — August 2026.
    """
)

st.caption(
    "Dataset: Citi Bike trip history + "
    "Open-Meteo historical weather | "
    "Period: August 2026 | "
    "Processed rides: 5.24M"
)


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------


filters = render_trip_filters(
    min_date=ANALYSIS_START,
    max_date=ANALYSIS_END,
)

st.caption(
    "Active filters: "
    f"{filters['rider_label']} · "
    f"{filters['bike_label']} · "
    f"{filters['start_date']:%b %d, %Y} → "
    f"{filters['end_date']:%b %d, %Y}"
)


# ---------------------------------------------------------
# KPI SUMMARY
# ---------------------------------------------------------


summary = load_summary(
    filters["start_date"],
    filters["end_date"],
    filters["rider_type"],
    filters["bike_type"],
).iloc[0]


total_rides = int(
    summary["total_rides"]
)

median_duration = float(
    summary["median_duration"]
    or 0
)

member_share = float(
    summary["member_share"]
    or 0
)

electric_share = float(
    summary["electric_share"]
    or 0
)


metric_row(
    [
        (
            "Total Rides",
            format_ride_count(
                total_rides
            ),
        ),
        (
            "Median Ride Duration",
            f"{median_duration:.1f} min",
        ),
        (
            "Member Share",
            f"{member_share:.1f}%",
        ),
        (
            "Electric Bike Share",
            f"{electric_share:.1f}%",
        ),
    ]
)


# ---------------------------------------------------------
# KEY FINDINGS
# ---------------------------------------------------------


st.markdown(
    "### Key Findings"
)

finding1, finding2, finding3 = (
    st.columns(3)
)


with finding1:
    st.info(
        """
        **Commuter-oriented demand**

        Weekday ridership shows strong morning and
        evening peaks, especially around 08:00 and
        17:00–18:00.
        """
    )


with finding2:
    st.info(
        """
        **Weekend behavior differs**

        Weekend demand shifts toward midday and
        afternoon rather than showing the same
        commuter peak structure.
        """
    )


with finding3:
    st.info(
        """
        **Rain is associated with lower demand**

        After adjusting for weekday and hour,
        wetter conditions are associated with
        below-expected ride demand.
        """
    )


st.divider()


# ---------------------------------------------------------
# DAILY RIDE VOLUME
# ---------------------------------------------------------


st.subheader(
    "Daily Ride Volume"
)


daily = load_daily_metrics(
    filters["start_date"],
    filters["end_date"],
    filters["rider_type"],
    filters["bike_type"],
)


daily_fig = px.line(
    daily,
    x="date",
    y="rides",
    markers=True,
    labels={
        "date": "Date",
        "rides": "Rides",
    },
)


style_figure(
    daily_fig,
    height=430,
)

daily_fig.update_layout(
    xaxis_title=None,
)


st.plotly_chart(
    daily_fig,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------
# RIDER MIX + TOP STATIONS
# ---------------------------------------------------------


left, right = st.columns(2)


with left:
    member_data = (
        load_member_breakdown(
            filters["start_date"],
            filters["end_date"],
            filters["rider_type"],
            filters["bike_type"],
        )
    )

    member_fig = px.bar(
        member_data,
        x="member_casual",
        y="rides",
        title=(
            "Member vs Casual Rides"
        ),
        labels={
            "member_casual":
                "Rider Type",
            "rides":
                "Rides",
        },
    )

    style_figure(
        member_fig,
        height=420,
    )

    st.plotly_chart(
        member_fig,
        width="stretch",
    )


with right:
    stations = load_top_stations(
        filters["start_date"],
        filters["end_date"],
        filters["rider_type"],
        filters["bike_type"],
    )

    station_fig = px.bar(
        stations.sort_values(
            "departures",
            ascending=True,
        ),
        x="departures",
        y="station_name",
        orientation="h",
        title=(
            "Top 10 Departure Stations"
        ),
        labels={
            "departures":
                "Departures",
            "station_name":
                "Station",
        },
    )

    style_figure(
        station_fig,
        height=420,
    )

    st.plotly_chart(
        station_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# PIPELINE NOTE
# ---------------------------------------------------------


st.divider()

st.caption(
    """
    UrbanFlow transforms raw mobility and weather data
    through a reproducible Python → Polars → Parquet →
    DuckDB analytics pipeline before visualization.
    """
)
