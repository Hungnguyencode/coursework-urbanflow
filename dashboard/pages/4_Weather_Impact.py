import duckdb
import plotly.express as px
import streamlit as st
from components.charts import style_figure
from components.health import (
    render_sidebar_health,
)
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)
from components.ui import (
    inject_global_css,
    insight_card,
    note_card,
    page_header,
    section_header,
    sidebar_data_status,
)

from urbanflow.config import DATABASE_PATH

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Weather Impact | UrbanFlow",
    page_icon="🌦️",
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
def load_weather_hourly():
    conn = get_connection()

    return conn.execute(
        """
        SELECT *
        FROM weather_ride_hourly
        ORDER BY
            date,
            hour;
        """
    ).fetchdf()


@st.cache_data
def load_weather_summary():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            ROUND(
                CORR(
                    temperature_c,
                    demand_vs_expected_pct
                ),
                3
            ) AS temp_correlation,

            ROUND(
                CORR(
                    precipitation_mm,
                    demand_vs_expected_pct
                ),
                3
            ) AS precipitation_correlation,

            AVG(
                CASE
                    WHEN precipitation_mm = 0
                    THEN demand_vs_expected_pct
                END
            ) AS dry_adjusted,

            AVG(
                CASE
                    WHEN precipitation_mm > 0
                    THEN demand_vs_expected_pct
                END
            ) AS wet_adjusted

        FROM weather_ride_hourly;
        """
    ).fetchdf()


@st.cache_data
def load_precipitation_summary():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            precipitation_category,

            COUNT(*)
                AS hours,

            AVG(
                demand_vs_expected_pct
            ) AS avg_vs_expected_pct,

            MEDIAN(
                demand_vs_expected_pct
            ) AS median_vs_expected_pct

        FROM weather_ride_hourly

        GROUP BY
            precipitation_category;
        """
    ).fetchdf()


@st.cache_data
def load_temperature_bins():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            CASE
                WHEN temperature_c < 20
                THEN '< 20°C'

                WHEN temperature_c < 25
                THEN '20–25°C'

                WHEN temperature_c < 30
                THEN '25–30°C'

                ELSE '30°C+'
            END AS temperature_band,

            AVG(
                demand_vs_expected_pct
            ) AS avg_vs_expected_pct,

            COUNT(*)
                AS observed_hours

        FROM weather_ride_hourly

        GROUP BY
            temperature_band;
        """
    ).fetchdf()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

page_header(
    title="Weather Impact",
    icon="🌦️",
    subtitle=(
        "Explore how temperature and precipitation are "
        "associated with Citi Bike demand after adjusting "
        "for normal weekday and hourly travel patterns."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

data = load_weather_hourly()

summary = (
    load_weather_summary()
    .iloc[0]
)

precip = (
    load_precipitation_summary()
)

temperature = (
    load_temperature_bins()
)


# ---------------------------------------------------------
# KPI SUMMARY
# ---------------------------------------------------------

temp_corr = float(
    summary["temp_correlation"]
)

rain_corr = float(
    summary["precipitation_correlation"]
)

dry_avg = float(
    summary["dry_adjusted"]
)

wet_avg = float(
    summary["wet_adjusted"]
)

wet_difference = (
    wet_avg
    - dry_avg
)

kpi1, kpi2, kpi3, kpi4 = st.columns(
    4,
    gap="medium",
)

with kpi1:
    st.metric(
        "Temp Association",
        f"{temp_corr:+.2f}",
    )

with kpi2:
    st.metric(
        "Rain Association",
        f"{rain_corr:+.2f}",
    )

with kpi3:
    st.metric(
        "Dry Hours vs Expected",
        f"{dry_avg:+.1f}%",
    )

with kpi4:
    st.metric(
        "Wet vs Dry",
        f"{wet_difference:+.1f} pp",
    )


st.caption(
    "Associations are descriptive and should not "
    "be interpreted as causal effects."
)


# ---------------------------------------------------------
# TEMPERATURE SCATTER
# ---------------------------------------------------------

section_header(
    "Temperature & Adjusted Demand",
    (
        "Each point represents one hour. "
        "Demand is measured relative to the normal "
        "weekday–hour baseline."
    ),
)

temp_fig = px.scatter(
    data,
    x="temperature_c",
    y="demand_vs_expected_pct",
    color="precipitation_mm",
    opacity=0.72,
    hover_data={
        "date": True,
        "hour": True,
        "rides": ":,",
        "expected_rides": ":,.0f",
        "temperature_c": ":.1f",
        "precipitation_mm": ":.1f",
    },
    color_continuous_scale=[
        [0.00, "#DDF3FF"],
        [0.25, "#9DD9F3"],
        [0.50, "#4EA8DE"],
        [0.75, "#2166AC"],
        [1.00, "#08306B"],
    ],
    labels={
        "temperature_c":
            "Temperature (°C)",
        "demand_vs_expected_pct":
            "Demand vs Expected (%)",
        "precipitation_mm":
            "Precipitation (mm)",
    },
    title=(
        "Weather-adjusted Ride Demand "
        "vs Temperature"
    ),
)

style_figure(
    temp_fig,
    height=500,
)

temp_fig.add_hline(
    y=0,
    line_dash="dash",
    line_color="#64748B",
    line_width=1.5,
)

temp_fig.update_traces(
    marker={
        "size": 8,
        "line": {
            "width": 0,
        },
    },
)

temp_fig.update_layout(
    coloraxis_colorbar={
        "title": "Rain (mm)",
        "thickness": 14,
    },
)

st.plotly_chart(
    temp_fig,
    width="stretch",
)


# ---------------------------------------------------------
# PRECIPITATION + TEMP BANDS
# ---------------------------------------------------------

section_header(
    "Weather Condition Comparison",
    (
        "Compare average adjusted demand across "
        "precipitation severity and temperature ranges."
    ),
)

left, right = st.columns(
    2,
    gap="large",
)


# ---------------------------------------------------------
# PRECIPITATION CATEGORIES
# ---------------------------------------------------------

with left:
    precipitation_order = [
        "No precipitation",
        "Light precipitation",
        "Moderate / heavy precipitation",
    ]

    precip_colors = {
        "No precipitation":
            "#14B8A6",
        "Light precipitation":
            "#F59E0B",
        "Moderate / heavy precipitation":
            "#EF4444",
    }

    precip_fig = px.bar(
        precip,
        x="precipitation_category",
        y="avg_vs_expected_pct",
        color="precipitation_category",
        hover_data={
            "hours": True,
            "avg_vs_expected_pct":
                ":.1f",
        },
        category_orders={
            "precipitation_category":
                precipitation_order,
        },
        color_discrete_map=(
            precip_colors
        ),
        title=(
            "Demand vs Expected "
            "by Precipitation"
        ),
        labels={
            "precipitation_category":
                "Weather",
            "avg_vs_expected_pct":
                "Demand vs Expected (%)",
            "hours":
                "Observed Hours",
        },
    )

    style_figure(
        precip_fig,
        height=430,
    )

    precip_fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#64748B",
        line_width=1.25,
    )

    precip_fig.update_traces(
        marker_line_width=0,
    )

    precip_fig.update_layout(
        showlegend=False,
    )

    precip_fig.update_xaxes(
        tickangle=-12,
    )

    st.plotly_chart(
        precip_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# TEMPERATURE BANDS
# ---------------------------------------------------------

with right:
    temperature_order = [
        "< 20°C",
        "20–25°C",
        "25–30°C",
        "30°C+",
    ]

    temperature_colors = {
        "< 20°C":
            "#9DD9F3",
        "20–25°C":
            "#4EA8DE",
        "25–30°C":
            "#0F6CBD",
        "30°C+":
            "#083C6B",
    }

    temp_band_fig = px.bar(
        temperature,
        x="temperature_band",
        y="avg_vs_expected_pct",
        color="temperature_band",
        hover_data={
            "observed_hours": True,
            "avg_vs_expected_pct":
                ":.1f",
        },
        category_orders={
            "temperature_band":
                temperature_order,
        },
        color_discrete_map=(
            temperature_colors
        ),
        title=(
            "Demand vs Expected "
            "by Temperature Band"
        ),
        labels={
            "temperature_band":
                "Temperature",
            "avg_vs_expected_pct":
                "Demand vs Expected (%)",
            "observed_hours":
                "Observed Hours",
        },
    )

    style_figure(
        temp_band_fig,
        height=430,
    )

    temp_band_fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#64748B",
        line_width=1.25,
    )

    temp_band_fig.update_traces(
        marker_line_width=0,
    )

    temp_band_fig.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        temp_band_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# WET HOURS
# ---------------------------------------------------------

section_header(
    "Rain Events & Demand",
    (
        "Focus specifically on wet hours to examine how "
        "larger precipitation events coincide with "
        "above- or below-expected ridership."
    ),
)

rain_events = data[
    data["precipitation_mm"] > 0
].copy()

if rain_events.empty:
    st.info(
        "No precipitation events are present "
        "in the active dataset."
    )

else:
    rain_fig = px.scatter(
        rain_events,
        x="precipitation_mm",
        y="demand_vs_expected_pct",
        size="precipitation_mm",
        color="temperature_c",
        opacity=0.72,
        hover_data={
            "date": True,
            "hour": True,
            "temperature_c":
                ":.1f",
            "rides":
                ":,",
            "expected_rides":
                ":,.0f",
        },
        color_continuous_scale=[
            [0.00, "#9DD9F3"],
            [0.50, "#4EA8DE"],
            [1.00, "#0F6CBD"],
        ],
        labels={
            "precipitation_mm":
                "Precipitation (mm)",
            "demand_vs_expected_pct":
                "Demand vs Expected (%)",
            "temperature_c":
                "Temperature (°C)",
        },
        title=(
            "Adjusted Ride Demand "
            "During Wet Hours"
        ),
    )

    style_figure(
        rain_fig,
        height=470,
    )

    rain_fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#64748B",
        line_width=1.5,
    )

    rain_fig.update_layout(
        coloraxis_colorbar={
            "title": "Temp °C",
            "thickness": 14,
        },
    )

    st.plotly_chart(
        rain_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# INTERPRETATION CARDS
# ---------------------------------------------------------

section_header(
    "Weather Interpretation",
    (
        "Key signals from the weather-adjusted "
        "mobility analysis."
    ),
)

wet_label = (
    "lower"
    if wet_difference < 0
    else "higher"
)

rain_label = (
    "negative"
    if rain_corr < 0
    else "positive"
)

temp_label = (
    "positive"
    if temp_corr > 0
    else "negative"
)

insight1, insight2, insight3 = st.columns(
    3,
    gap="medium",
)

with insight1:
    insight_card(
        title="Wet-hour penalty",
        icon="🌧️",
        accent="#EF4444",
        body=(
            f"Wet hours average {abs(wet_difference):.1f} "
            f"percentage points {wet_label} demand than "
            "dry hours after adjusting for normal "
            "weekday and hourly patterns."
        ),
    )

with insight2:
    insight_card(
        title="Rain association",
        icon="☔",
        accent="#F59E0B",
        body=(
            f"Precipitation has a {rain_label} "
            "association with adjusted demand "
            f"(r = {rain_corr:+.2f})."
        ),
    )

with insight3:
    insight_card(
        title="Temperature association",
        icon="🌡️",
        accent="#0F6CBD",
        body=(
            f"Temperature shows a {temp_label} "
            "relationship with adjusted demand "
            f"(r = {temp_corr:+.2f})."
        ),
    )


# ---------------------------------------------------------
# DATA CAVEAT
# ---------------------------------------------------------

note_card(
    title="Weather coverage note",
    body=(
        "Weather observations represent a single "
        "New York City reference location. They "
        "approximate city-level conditions rather "
        "than station-specific microclimates."
    ),
)