import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)

DATABASE_PATH = "data/analytics/urbanflow.duckdb"


st.set_page_config(
    page_title="Temporal Patterns | UrbanFlow",
    page_icon="⏱️",
    layout="wide",
)


refresh = load_refresh_context()

sync_refresh_cache(
    refresh
)


@st.cache_resource
def get_connection():
    return duckdb.connect(
        DATABASE_PATH,
        read_only=True,
    )


@st.cache_data
def load_hourly_heatmap():
    conn = get_connection()

    return conn.execute(
        """
        WITH daily_hourly AS (
            SELECT
                date,
                weekday,
                hour,
                COUNT(*) AS rides
            FROM trips
            GROUP BY
                date,
                weekday,
                hour
        )

        SELECT
            weekday,

            CASE weekday
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
                WHEN 7 THEN 'Sunday'
            END AS weekday_name,

            hour,

            AVG(rides)
                AS avg_rides

        FROM daily_hourly

        GROUP BY
            weekday,
            hour

        ORDER BY
            weekday,
            hour;
        """
    ).fetchdf()


@st.cache_data
def load_hourly_total():
    conn = get_connection()

    return conn.execute(
        """
        WITH daily_hourly AS (
            SELECT
                date,
                hour,
                COUNT(*) AS rides

            FROM trips

            GROUP BY
                date,
                hour
        )

        SELECT
            hour,
            AVG(rides)
                AS avg_rides

        FROM daily_hourly

        GROUP BY hour

        ORDER BY hour;
        """
    ).fetchdf()


@st.cache_data
def load_weekday_total():
    conn = get_connection()

    return conn.execute(
        """
        WITH daily AS (
            SELECT
                date,
                weekday,
                COUNT(*) AS rides

            FROM trips

            GROUP BY
                date,
                weekday
        )

        SELECT
            weekday,

            CASE weekday
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
                WHEN 7 THEN 'Sunday'
            END AS weekday_name,

            AVG(rides)
                AS avg_daily_rides

        FROM daily

        GROUP BY weekday

        ORDER BY weekday;
        """
    ).fetchdf()


st.title("Temporal Patterns ⏱️")

st.caption(
    "When does Citi Bike demand occur?"
)

st.markdown(
    "Explore how ride demand changes across "
    "hours of the day and days of the week "
    f"during {refresh.period_label}."
)

st.caption(
    f"Last refresh: {refresh.last_refresh_label}"
)


# ---------------------------------------------------------
# HEATMAP
# ---------------------------------------------------------

heatmap = load_hourly_heatmap()

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

hours = list(range(24))

matrix = (
    heatmap
    .pivot(
        index="weekday_name",
        columns="hour",
        values="avg_rides",
    )
    .reindex(weekday_order)
)

matrix = matrix.reindex(
    columns=hours
)


heatmap_fig = go.Figure(
    data=go.Heatmap(
        z=matrix.values,
        x=hours,
        y=weekday_order,
        colorscale="Blues",
        colorbar={
            "title": "Avg rides",
        },
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Hour: %{x}:00<br>"
            "Avg rides: %{z:,.0f}"
            "<extra></extra>"
        ),
    )
)

heatmap_fig.update_layout(
    title="Average Ride Demand by Weekday and Hour",
    xaxis_title="Hour of Day",
    yaxis_title="Day of Week",
    height=500,
)

heatmap_fig.update_xaxes(
    tickmode="array",
    tickvals=list(range(24)),
)

st.plotly_chart(
    heatmap_fig,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------
# HOURLY + WEEKDAY
# ---------------------------------------------------------

left, right = st.columns(2)


with left:
    hourly = load_hourly_total()

    hourly_fig = px.line(
        hourly,
        x="hour",
        y="avg_rides",
        markers=True,
        title="Average Ride Demand by Hour",
        labels={
            "hour": "Hour of Day",
            "avg_rides": "Average Rides per Day",
        },
    )

    hourly_fig.update_xaxes(
        tickmode="linear",
        tick0=0,
        dtick=1,
    )

    st.plotly_chart(
        hourly_fig,
        width="stretch",
    )


with right:
    weekday = load_weekday_total()

    weekday_fig = px.bar(
        weekday,
        x="weekday_name",
        y="avg_daily_rides",
        title="Average Daily Ride Volume by Day of Week",
        labels={
            "weekday_name": "Day",
            "avg_daily_rides": "Average Rides per Day",
        },
        category_orders={
            "weekday_name": weekday_order,
        },
    )

    st.plotly_chart(
        weekday_fig,
        width="stretch",
    )