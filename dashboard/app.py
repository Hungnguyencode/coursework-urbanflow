import duckdb
import plotly.express as px
import streamlit as st


DATABASE_PATH = "data/analytics/urbanflow.duckdb"


st.set_page_config(
    page_title="UrbanFlow",
    page_icon="🚲",
    layout="wide",
)


@st.cache_resource
def get_connection():
    return duckdb.connect(
        DATABASE_PATH,
        read_only=True,
    )


@st.cache_data
def load_kpis():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            COUNT(*) AS total_rides,

            MEDIAN(duration_minutes)
                AS median_duration,

            SUM(
                CASE
                    WHEN member_casual = 'member'
                    THEN 1
                    ELSE 0
                END
            ) * 100.0 / COUNT(*)
                AS member_share,

            SUM(
                CASE
                    WHEN rideable_type = 'electric_bike'
                    THEN 1
                    ELSE 0
                END
            ) * 100.0 / COUNT(*)
                AS electric_share

        FROM trips;
        """
    ).fetchdf()


@st.cache_data
def load_daily_metrics():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            date,
            rides,
            member_rides,
            casual_rides

        FROM daily_metrics

        ORDER BY date;
        """
    ).fetchdf()


@st.cache_data
def load_member_metrics():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            member_casual,
            COUNT(*) AS rides

        FROM trips

        GROUP BY member_casual

        ORDER BY rides DESC;
        """
    ).fetchdf()


@st.cache_data
def load_top_stations():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            station_name,
            departures

        FROM station_metrics

        WHERE station_name IS NOT NULL

        ORDER BY departures DESC

        LIMIT 10;
        """
    ).fetchdf()


st.title("UrbanFlow 🚲")

st.caption(
    "Urban Mobility Analytics & Visualization Platform"
)

st.markdown(
    """
    Exploring Citi Bike mobility patterns across
    New York City — August 2026.
    """
)

kpis = load_kpis().iloc[0]

total_rides = int(
    kpis["total_rides"]
)

median_duration = float(
    kpis["median_duration"]
)

member_share = float(
    kpis["member_share"]
)

electric_share = float(
    kpis["electric_share"]
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Rides",
        f"{total_rides / 1_000_000:.2f}M",
    )

with col2:
    st.metric(
        "Median Ride Duration",
        f"{median_duration:.1f} min",
    )

with col3:
    st.metric(
        "Member Share",
        f"{member_share:.1f}%",
    )

with col4:
    st.metric(
        "Electric Bike Share",
        f"{electric_share:.1f}%",
    )


st.divider()


daily = load_daily_metrics()

daily_fig = px.line(
    daily,
    x="date",
    y="rides",
    markers=True,
    title="Daily Ride Volume",
)

daily_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Rides",
)

st.plotly_chart(
    daily_fig,
    width="stretch",
)


left, right = st.columns(2)


with left:
    member_data = load_member_metrics()

    member_fig = px.bar(
        member_data,
        x="member_casual",
        y="rides",
        title="Member vs Casual Riders",
        labels={
            "member_casual": "Rider Type",
            "rides": "Rides",
        },
    )

    st.plotly_chart(
        member_fig,
        width="stretch",
    )


with right:
    stations = load_top_stations()

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

    st.plotly_chart(
        station_fig,
        width="stretch",
    )