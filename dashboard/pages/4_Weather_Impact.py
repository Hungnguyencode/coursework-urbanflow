import duckdb
import plotly.express as px
import streamlit as st


DATABASE_PATH = (
    "data/analytics/urbanflow.duckdb"
)


st.set_page_config(
    page_title="Weather Impact | UrbanFlow",
    page_icon="🌦️",
    layout="wide",
)


@st.cache_resource
def get_connection():
    return duckdb.connect(
        DATABASE_PATH,
        read_only=True,
    )


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

            COUNT(*) AS hours,

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

                ELSE
                    '30°C+'
            END AS temperature_band,

            AVG(
                demand_vs_expected_pct
            ) AS avg_vs_expected_pct,

            COUNT(*)
                AS observed_hours

        FROM weather_ride_hourly

        GROUP BY temperature_band;
        """
    ).fetchdf()


st.title(
    "Weather Impact 🌦️"
)

st.caption(
    "How is Citi Bike demand associated with weather?"
)

st.markdown(
    """
    Hourly Citi Bike demand is joined with historical
    weather observations for New York City during
    August 2026.
    """
)


data = load_weather_hourly()

summary = (
    load_weather_summary()
    .iloc[0]
)


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
    wet_avg - dry_avg
)


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:
    st.metric(
        "Adjusted Temp Association",
        f"{temp_corr:+.2f}",
    )

with col2:
    st.metric(
        "Adjusted Rain Association",
        f"{rain_corr:+.2f}",
    )

with col3:
    st.metric(
        "Dry Hours vs Expected",
        f"{dry_avg:+.1f}%",
    )

with col4:
    st.metric(
        "Wet vs Dry",
        f"{wet_difference:+.1f} pp",
    )


st.caption(
    """
    Correlation describes association only and
    should not be interpreted as causal effect.
    """
)


st.divider()


# ---------------------------------------------------------
# TEMPERATURE SCATTER
# ---------------------------------------------------------

st.subheader(
    "Temperature and Hourly Ride Demand"
)


temp_fig = px.scatter(
    data,

    x="temperature_c",
    y="demand_vs_expected_pct",

    color="precipitation_mm",

    opacity=0.65,

    hover_data=[
        "date",
        "hour",
        "rides",
        "expected_rides",
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
        "Weather-adjusted Ride Demand vs Temperature"
    ),
)

temp_fig.add_hline(
    y=0,
    line_dash="dash",
)

st.plotly_chart(
    temp_fig,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------
# PRECIPITATION + TEMP BANDS
# ---------------------------------------------------------

left, right = st.columns(2)


with left:
    precip = (
        load_precipitation_summary()
    )

    precip_fig = px.bar(
        precip,

        x="precipitation_category",
        y="avg_vs_expected_pct",

        hover_data={
            "hours": True,
            "avg_vs_expected_pct": ":.1f",
        },

        title=(
            "Ride Demand vs Expected "
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

        category_orders={
            "precipitation_category": [
                "No precipitation",
                "Light precipitation",
                "Moderate / heavy precipitation",
            ]
        },
    )

    precip_fig.add_hline(
        y=0,
        line_dash="dash",
    )

    st.plotly_chart(
        precip_fig,
        width="stretch",
    )


with right:
    temperature = (
        load_temperature_bins()
    )

    temperature_order = [
        "< 20°C",
        "20–25°C",
        "25–30°C",
        "30°C+",
    ]

    temp_band_fig = px.bar(
        temperature,

        x="temperature_band",
        y="avg_vs_expected_pct",

        hover_data={
            "observed_hours": True,
            "avg_vs_expected_pct": ":.1f",
        },

        category_orders={
            "temperature_band":
                temperature_order,
        },

        title=(
            "Ride Demand vs Expected "
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

    temp_band_fig.add_hline(
        y=0,
        line_dash="dash",
    )

    st.plotly_chart(
        temp_band_fig,
        width="stretch",
    )


st.divider()


# ---------------------------------------------------------
# PRECIPITATION TIME SERIES
# ---------------------------------------------------------

st.subheader(
    "Rain Events and Ride Demand"
)


rain_events = data[
    data["precipitation_mm"] > 0
].copy()


rain_fig = px.scatter(
    rain_events,

    x="precipitation_mm",
    y="demand_vs_expected_pct",

    size="precipitation_mm",

    hover_data=[
        "date",
        "hour",
        "temperature_c",
        "rides",
        "expected_rides",
    ],

    labels={
        "precipitation_mm":
            "Precipitation (mm)",

        "demand_vs_expected_pct":
            "Demand vs Expected (%)",
    },

    title=(
        "Adjusted Ride Demand During Wet Hours"
    ),
)

rain_fig.add_hline(
    y=0,
    line_dash="dash",
)


st.plotly_chart(
    rain_fig,
    width="stretch",
)


st.info(
    """
    Weather data is represented by a single
    New York City reference location, so it
    approximates city-level conditions rather
    than station-specific microclimates.
    """
)