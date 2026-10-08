import duckdb
import plotly.express as px
import streamlit as st
from components.charts import style_figure
from components.filters import render_trip_filters
from components.health import render_sidebar_health
from components.kpis import metric_row
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)
from components.ui import (
    inject_global_css,
    insight_card,
    note_card,
    page_footer,
    page_header,
    section_header,
    sidebar_data_status,
    view_context,
)

from urbanflow.config import DATABASE_PATH

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="UrbanFlow",
    page_icon="🚲",
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

ANALYSIS_START = refresh.start_date
ANALYSIS_END = refresh.end_date

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
        + " AND ".join(
            conditions
        )
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
            COUNT(*)
                AS total_rides,

            MEDIAN(
                duration_minutes
            ) AS median_duration,

            AVG(
                CASE
                    WHEN member_casual = 'member'
                    THEN 1
                    ELSE 0
                END
            ) * 100
                AS member_share,

            AVG(
                CASE
                    WHEN rideable_type = 'electric_bike'
                    THEN 1
                    ELSE 0
                END
            ) * 100
                AS electric_share

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

        GROUP BY
            date

        ORDER BY
            date;
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

        GROUP BY
            member_casual

        ORDER BY
            rides DESC;
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

            COUNT(*)
                AS departures

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
# HERO
# ---------------------------------------------------------

page_header(
    title="UrbanFlow",
    icon="🚲",
    subtitle=(
        "Explore how New York City moves — when riders travel, "
        "where demand concentrates and how mobility patterns "
        "change across the Citi Bike network."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

filters = render_trip_filters(
    min_date=ANALYSIS_START,
    max_date=ANALYSIS_END,
)

view_context(
    f"{filters['rider_label']} · "
    f"{filters['bike_label']} · "
    f"{filters['start_date']:%b %d} → "
    f"{filters['end_date']:%b %d, %Y}"
)

# ---------------------------------------------------------
# KPI PULSE
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
# 01 · MOBILITY SNAPSHOT
# ---------------------------------------------------------

section_header(
    "Mobility Snapshot",
    (
        "Daily ride demand and rider composition "
        "for the active filter selection."
    ),
    index="01 · MOBILITY SNAPSHOT",
)

daily = load_daily_metrics(
    filters["start_date"],
    filters["end_date"],
    filters["rider_type"],
    filters["bike_type"],
)

member_data = load_member_breakdown(
    filters["start_date"],
    filters["end_date"],
    filters["rider_type"],
    filters["bike_type"],
)

main_left, main_right = st.columns(
    [2.35, 1],
    gap="large",
)

# ---------------------------------------------------------
# DAILY VOLUME
# ---------------------------------------------------------

with main_left:
    daily_fig = px.area(
        daily,
        x="date",
        y="rides",
        markers=True,
        labels={
            "date": "Date",
            "rides": "Rides",
        },
        title="Daily Ride Volume",
    )

    style_figure(
        daily_fig,
        height=372,
    )

    daily_fig.update_traces(
        line={
            "width": 3,
            "color": "#0B6BFF",
        },
        marker={
            "size": 6,
            "color": "#0B6BFF",
        },
        fillcolor=(
            "rgba(15,108,189,0.10)"
        ),
        hovertemplate=(
            "<b>%{x|%b %d}</b><br>"
            "Rides: %{y:,}"
            "<extra></extra>"
        ),
    )

    daily_fig.update_layout(
        xaxis_title=None,
        showlegend=False,
    )

    daily_fig.update_xaxes(
        tickformat="%b %d",
    )

    st.plotly_chart(
        daily_fig,
        width="stretch",
    )

# ---------------------------------------------------------
# RIDER MIX
# ---------------------------------------------------------

with main_right:
    rider_colors = {
        "member": "#0B6BFF",
        "casual": "#13C8A3",
    }

    member_fig = px.pie(
        member_data,
        values="rides",
        names="member_casual",
        hole=0.66,
        color="member_casual",
        color_discrete_map=(
            rider_colors
        ),
        title="Rider Mix",
    )

    member_fig.update_traces(
        textposition="inside",
        textinfo="percent",
        marker={
            "line": {
                "color": "#FFFFFF",
                "width": 3,
            },
        },
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Rides: %{value:,}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        ),
    )

    member_fig.add_annotation(
        text=(
            f"<b>{format_ride_count(total_rides)}</b>"
            "<br><span style='font-size:12px'>rides</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font={
            "size": 20,
            "color": "#0B1F3A",
        },
    )

    member_fig.update_layout(
        template="plotly_white",
        height=372,
        margin={
            "l": 18,
            "r": 18,
            "t": 65,
            "b": 18,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title={
            "font": {
                "size": 18,
                "color": "#0B1F3A",
            },
            "x": 0.03,
        },
    )

    st.plotly_chart(
        member_fig,
        width="stretch",
    )

# ---------------------------------------------------------
# 02 · NETWORK SIGNALS
# ---------------------------------------------------------

section_header(
    "Network Signals",
    (
        "High-demand departure locations and the strongest "
        "behavioral patterns visible in the active dataset."
    ),
    index="02 · NETWORK SIGNALS",
)

stations = load_top_stations(
    filters["start_date"],
    filters["end_date"],
    filters["rider_type"],
    filters["bike_type"],
)

network_left, network_right = st.columns(
    [2.35, 1],
    gap="large",
)

# ---------------------------------------------------------
# TOP STATIONS
# ---------------------------------------------------------

with network_left:
    station_fig = px.bar(
        stations.sort_values(
            "departures",
            ascending=True,
        ),
        x="departures",
        y="station_name",
        orientation="h",
        title="Top 10 Departure Stations",
        labels={
            "departures": "Departures",
            "station_name": "Station",
        },
    )

    style_figure(
        station_fig,
        height=405,
    )

    station_fig.update_traces(
        marker_color="#0B6BFF",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Departures: %{x:,}"
            "<extra></extra>"
        ),
    )

    station_fig.update_layout(
        yaxis_title=None,
        showlegend=False,
    )

    st.plotly_chart(
        station_fig,
        width="stretch",
    )

# ---------------------------------------------------------
# FINDINGS
# ---------------------------------------------------------

with network_right:
    st.caption(
        "KEY FINDINGS"
    )

    insight_card(
        title="Commuter-oriented demand",
        icon="🚇",
        accent="#0B6BFF",
        body=(
            "Weekday ridership shows clear morning and "
            "evening peaks, especially near 08:00 and "
            "17:00–18:00."
        ),
    )

    insight_card(
        title="Weekend behavior shifts",
        icon="🌤️",
        accent="#13C8A3",
        body=(
            "Weekend demand moves toward midday and "
            "afternoon instead of following the weekday "
            "commuter profile."
        ),
    )

    insight_card(
        title="Rain suppresses demand",
        icon="🌧️",
        accent="#FF5D6C",
        body=(
            "After adjusting for weekday and hour, wetter "
            "conditions are associated with below-expected "
            "ride demand."
        ),
    )

# ---------------------------------------------------------
# 03 · EXPORT
# ---------------------------------------------------------

section_header(
    "Export & Reproducibility",
    (
        "Take the filtered daily summary with you or review "
        "how the dashboard is produced."
    ),
    index="03 · EXPORT & REPRODUCIBILITY",
)

csv_data = daily.to_csv(
    index=False
).encode(
    "utf-8"
)

export_left, export_right = st.columns(
    [1, 2.8],
    gap="large",
)

with export_left:
    st.download_button(
        label="⬇️ Download daily metrics",
        data=csv_data,
        file_name=(
            "urbanflow_daily_metrics_"
            f"{refresh.period.file_suffix}.csv"
        ),
        mime="text/csv",
        width="stretch",
    )

with export_right:
    note_card(
        title="Reproducible analytics pipeline",
        body=(
            "UrbanFlow transforms Citi Bike mobility and "
            "Open-Meteo weather data through Python, Polars, "
            "Parquet and DuckDB before rendering the "
            "interactive Streamlit dashboard."
        ),
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

page_footer(
    period=refresh.period_label,
)
