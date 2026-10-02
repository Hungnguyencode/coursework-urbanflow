import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.charts import style_figure
from components.health import render_sidebar_health
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)
from components.ui import (
    inject_global_css,
    insight_card,
    page_footer,
    page_header,
    section_header,
    sidebar_data_status,
)

from urbanflow.config import DATABASE_PATH

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Temporal Patterns | UrbanFlow",
    page_icon="⏱️",
    layout="wide",
)

inject_global_css()


# ---------------------------------------------------------
# REFRESH CONTEXT
# ---------------------------------------------------------

refresh = load_refresh_context()

sync_refresh_cache(
    refresh
)

sidebar_data_status(
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)

render_sidebar_health(
    expected_hours=(
        refresh.period.expected_hours
    ),
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
# DATA LOADERS
# ---------------------------------------------------------

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

        GROUP BY
            hour

        ORDER BY
            hour;
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

        GROUP BY
            weekday

        ORDER BY
            weekday;
        """
    ).fetchdf()


# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------

page_header(
    title="Temporal Patterns",
    icon="⏱️",
    subtitle=(
        "Read the rhythm of New York City mobility — "
        "when demand rises, when it falls and how rider "
        "behavior shifts between weekdays and weekends."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

heatmap = load_hourly_heatmap()

hourly = load_hourly_total()

weekday = load_weekday_total()


weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


# ---------------------------------------------------------
# KPI SUMMARY
# ---------------------------------------------------------

peak_hour_row = hourly.loc[
    hourly["avg_rides"].idxmax()
]

peak_day_row = weekday.loc[
    weekday["avg_daily_rides"].idxmax()
]

peak_slot_row = heatmap.loc[
    heatmap["avg_rides"].idxmax()
]


weekday_mean = weekday[
    weekday["weekday"] <= 5
]["avg_daily_rides"].mean()


weekend_mean = weekday[
    weekday["weekday"] >= 6
]["avg_daily_rides"].mean()


weekend_gap = (
    (
        weekend_mean
        / weekday_mean
    )
    - 1
) * 100


peak_day_short = (
    peak_slot_row[
        "weekday_name"
    ][:3]
)


kpi1, kpi2, kpi3, kpi4 = st.columns(
    4,
    gap="medium",
)


with kpi1:
    st.metric(
        "Peak Hour",
        (
            f"{int(peak_hour_row['hour']):02d}:00"
        ),
    )


with kpi2:
    st.metric(
        "Busiest Day",
        peak_day_row[
            "weekday_name"
        ],
    )


with kpi3:
    st.metric(
        "Strongest Time Slot",
        (
            f"{peak_day_short} · "
            f"{int(peak_slot_row['hour']):02d}:00"
        ),
    )


with kpi4:
    st.metric(
        "Weekend vs Weekday",
        f"{weekend_gap:+.1f}%",
    )


# ---------------------------------------------------------
# 01 · DEMAND RHYTHM
# ---------------------------------------------------------

section_header(
    "Demand Rhythm",
    (
        "See how average Citi Bike activity changes across "
        "the full weekday–hour cycle. Darker cells indicate "
        "stronger recurring demand."
    ),
    index="01 · DEMAND RHYTHM",
)


hours = list(
    range(24)
)


matrix = (
    heatmap
    .pivot(
        index="weekday_name",
        columns="hour",
        values="avg_rides",
    )
    .reindex(
        weekday_order
    )
)


matrix = matrix.reindex(
    columns=hours
)


heatmap_fig = go.Figure(
    data=go.Heatmap(
        z=matrix.values,
        x=hours,
        y=weekday_order,
        colorscale=[
            [
                0.00,
                "#F7FBFF",
            ],
            [
                0.20,
                "#E1EFFA",
            ],
            [
                0.40,
                "#A9D3EC",
            ],
            [
                0.60,
                "#5AA6D1",
            ],
            [
                0.80,
                "#0F6CBD",
            ],
            [
                1.00,
                "#083C6B",
            ],
        ],
        colorbar={
            "title": "Avg rides",
            "thickness": 14,
            "len": 0.72,
        },
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Hour: %{x}:00<br>"
            "Average rides: %{z:,.0f}"
            "<extra></extra>"
        ),
    )
)


style_figure(
    heatmap_fig,
    height=520,
)


heatmap_fig.update_layout(
    title=(
        "Average Ride Demand by Weekday and Hour"
    ),
    xaxis_title="Hour of Day",
    yaxis_title=None,
)


heatmap_fig.update_xaxes(
    tickmode="array",
    tickvals=hours,
    ticktext=[
        str(hour)
        for hour in hours
    ],
)


heatmap_fig.update_yaxes(
    autorange="reversed",
)


st.plotly_chart(
    heatmap_fig,
    width="stretch",
)


# ---------------------------------------------------------
# 02 · DAILY PROFILE
# ---------------------------------------------------------

section_header(
    "Daily Profile",
    (
        "Compare the typical 24-hour demand curve with "
        "average ride volume across each day of the week."
    ),
    index="02 · DAILY PROFILE",
)


profile_left, profile_right = st.columns(
    [
        1.55,
        1,
    ],
    gap="large",
)


# ---------------------------------------------------------
# HOURLY CURVE
# ---------------------------------------------------------

with profile_left:
    hourly_fig = px.line(
        hourly,
        x="hour",
        y="avg_rides",
        markers=True,
        title="Average Ride Demand by Hour",
        labels={
            "hour":
                "Hour of Day",
            "avg_rides":
                "Average Rides per Day",
        },
    )


    style_figure(
        hourly_fig,
        height=455,
    )


    hourly_fig.update_traces(
        line={
            "width": 3,
            "color": "#0F6CBD",
        },
        marker={
            "size": 7,
            "color": "#0F6CBD",
            "line": {
                "width": 1,
                "color": "#FFFFFF",
            },
        },
        hovertemplate=(
            "<b>%{x}:00</b><br>"
            "Average rides: %{y:,.0f}"
            "<extra></extra>"
        ),
    )


    hourly_fig.add_vrect(
        x0=7,
        x1=9,
        fillcolor="#14B8A6",
        opacity=0.08,
        line_width=0,
        annotation_text="AM commute",
        annotation_position="top left",
    )


    hourly_fig.add_vrect(
        x0=16,
        x1=19,
        fillcolor="#F59E0B",
        opacity=0.08,
        line_width=0,
        annotation_text="PM commute",
        annotation_position="top left",
    )


    hourly_fig.update_xaxes(
        tickmode="linear",
        tick0=0,
        dtick=2,
    )


    hourly_fig.update_layout(
        showlegend=False,
    )


    st.plotly_chart(
        hourly_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# WEEKDAY PROFILE
# ---------------------------------------------------------

with profile_right:
    weekday_colors = [
        (
            "#14B8A6"
            if day
            in {
                "Saturday",
                "Sunday",
            }
            else "#0F6CBD"
        )
        for day
        in weekday[
            "weekday_name"
        ]
    ]


    weekday_fig = px.bar(
        weekday,
        x="weekday_name",
        y="avg_daily_rides",
        title=(
            "Average Daily Ride Volume "
            "by Day of Week"
        ),
        labels={
            "weekday_name":
                "Day",
            "avg_daily_rides":
                "Average Rides per Day",
        },
        category_orders={
            "weekday_name":
                weekday_order,
        },
    )


    style_figure(
        weekday_fig,
        height=455,
    )


    weekday_fig.update_traces(
        marker_color=weekday_colors,
        marker_line_width=0,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Average rides: %{y:,.0f}"
            "<extra></extra>"
        ),
    )


    weekday_fig.update_layout(
        showlegend=False,
    )


    weekday_fig.update_xaxes(
        tickangle=-25,
        title=None,
    )


    st.plotly_chart(
        weekday_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# 03 · RHYTHM INSIGHTS
# ---------------------------------------------------------

section_header(
    "Rhythm Insights",
    (
        "Key signals from the normalized temporal profile "
        "and what they suggest about typical Citi Bike usage."
    ),
    index="03 · RHYTHM INSIGHTS",
)


insight1, insight2, insight3 = st.columns(
    3,
    gap="medium",
)


with insight1:
    insight_card(
        title="Peak hourly demand",
        icon="🕔",
        accent="#0F6CBD",
        body=(
            "The strongest average hourly demand occurs "
            f"around {int(peak_hour_row['hour']):02d}:00, "
            "revealing a pronounced late-day travel peak."
        ),
    )


with insight2:
    insight_card(
        title="Busiest average day",
        icon="📅",
        accent="#8B5CF6",
        body=(
            f"{peak_day_row['weekday_name']} records the "
            "highest average daily ride volume in the "
            "active dataset."
        ),
    )


with insight3:
    insight_card(
        title="Weekend shift",
        icon="🌤️",
        accent="#14B8A6",
        body=(
            "Weekend daily demand is "
            f"{abs(weekend_gap):.1f}% "
            f"{'higher' if weekend_gap >= 0 else 'lower'} "
            "than the weekday average, while its hourly "
            "profile shifts later into the day."
        ),
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

page_footer(
    period=refresh.period_label,
)