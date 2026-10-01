import duckdb
import plotly.express as px
import pydeck as pdk
import streamlit as st
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)

DATABASE_PATH = "data/analytics/urbanflow.duckdb"


st.set_page_config(
    page_title="Mobility Flow | UrbanFlow",
    page_icon="🗺️",
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
def load_station_metrics():
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            station_key,
            station_name,
            source_station_id_count,
            latitude,
            longitude,
            departures,
            arrivals,
            net_flow,
            total_activity,
            imbalance_ratio

        FROM station_metrics

        WHERE
            latitude IS NOT NULL
            AND longitude IS NOT NULL

        ORDER BY total_activity DESC;
        """
    ).fetchdf()


@st.cache_data
def load_top_routes(limit: int):
    conn = get_connection()

    return conn.execute(
        """
        SELECT
            start_station_name,
            end_station_name,
            rides

        FROM od_flow

        WHERE
            start_station_name IS NOT NULL
            AND end_station_name IS NOT NULL

        ORDER BY rides DESC

        LIMIT ?;
        """,
        [limit],
    ).fetchdf()


st.title("Mobility Flow 🗺️")

st.caption(
    "How do Citi Bike trips redistribute bikes across stations?"
)

st.caption(
    f"Active data period: {refresh.period_label} | "
    f"Last refresh: {refresh.last_refresh_label}"
)

st.markdown(
    """
    This page analyzes observed trip flows between stations.
    Negative net flow indicates more departures than arrivals;
    positive net flow indicates more arrivals than departures.
    """
)


stations = load_station_metrics()


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------

st.sidebar.header("Flow Filters")

min_activity = st.sidebar.slider(
    "Minimum station activity",
    min_value=100,
    max_value=10_000,
    value=5_000,
    step=100,
)

top_n = st.sidebar.slider(
    "Stations shown in rankings",
    min_value=5,
    max_value=25,
    value=10,
    step=5,
)


filtered = stations[
    stations["total_activity"] >= min_activity
].copy()

flow_view = st.sidebar.selectbox(
    "Map view",
    [
        "All stations",
        "Net outflow only",
        "Net inflow only",
        "High imbalance only",
    ],
)

# ---------------------------------------------------------
# KPIs
# ---------------------------------------------------------

station_count = len(filtered)

largest_loss = filtered.loc[
    filtered["net_flow"].idxmin()
]

largest_gain = filtered.loc[
    filtered["net_flow"].idxmax()
]

median_imbalance = (
    filtered["imbalance_ratio"].median()
    * 100
)


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Stations Analyzed",
        f"{station_count:,}",
    )


with col2:
    st.metric(
        "Median Imbalance",
        f"{median_imbalance:.1f}%",
    )


with col3:
    st.metric(
        "Largest Net Loss",
        f"{int(largest_loss['net_flow']):,}",
    )

    st.caption(
        largest_loss["station_name"]
    )


with col4:
    st.metric(
        "Largest Net Gain",
        f"+{int(largest_gain['net_flow']):,}",
    )

    st.caption(
        largest_gain["station_name"]
    )


st.divider()


# ---------------------------------------------------------
# STATION FLOW MAP
# ---------------------------------------------------------

st.subheader(
    "Observed Station Flow Imbalance"
)

st.caption(
    """
    Circle size represents total station activity.
    Red stations have more departures than arrivals;
    blue stations have more arrivals than departures.
    """
)


map_data = filtered.copy()

if flow_view == "Net outflow only":
    map_data = map_data[
        map_data["net_flow"] < 0
    ].copy()

elif flow_view == "Net inflow only":
    map_data = map_data[
        map_data["net_flow"] > 0
    ].copy()

elif flow_view == "High imbalance only":
    map_data = map_data[
        map_data["imbalance_ratio"] >= 0.05
    ].copy()


def flow_color(net_flow):
    if net_flow < 0:
        return [220, 70, 70, 170]

    if net_flow > 0:
        return [60, 120, 210, 170]

    return [140, 140, 140, 150]


map_data["color"] = (
    map_data["net_flow"]
    .apply(flow_color)
)


# Use percentile rank instead of raw activity.
# This prevents extremely active stations
# from creating giant circles.
map_data["radius"] = (
    4
    + map_data["total_activity"]
    .rank(pct=True)
    * 14
)


map_data["imbalance_pct"] = (
    map_data["imbalance_ratio"]
    * 100
)


layer = pdk.Layer(
    "ScatterplotLayer",

    data=map_data,

    get_position=[
        "longitude",
        "latitude",
    ],

    get_fill_color="color",

    get_radius="radius",

    radius_units="pixels",

    radius_min_pixels=4,

    radius_max_pixels=20,

    pickable=True,

    auto_highlight=True,

    opacity=0.6,

    stroked=True,

    get_line_color=[
        255,
        255,
        255,
        120,
    ],

    line_width_min_pixels=1,
)


view_state = pdk.ViewState(
    latitude=float(
        map_data["latitude"].median()
    ),

    longitude=float(
        map_data["longitude"].median()
    ),

    zoom=11,

    pitch=0,
)


tooltip = {
    "html": """
        <b>{station_name}</b><br/>
        Departures: {departures}<br/>
        Arrivals: {arrivals}<br/>
        Net flow: {net_flow}<br/>
        Activity: {total_activity}<br/>
        Imbalance: {imbalance_pct}%
    """,

    "style": {
        "backgroundColor": "#111827",
        "color": "white",
    },
}


deck = pdk.Deck(
    layers=[layer],

    initial_view_state=view_state,

    tooltip=tooltip,

    map_style=None,
)


st.pydeck_chart(
    deck,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------
# NET LOSS / NET GAIN
# ---------------------------------------------------------

left, right = st.columns(2)


with left:
    losses = (
        filtered
        .nsmallest(
            top_n,
            "net_flow",
        )
        .sort_values(
            "net_flow",
            ascending=True,
        )
    )

    loss_fig = px.bar(
        losses,

        x="net_flow",

        y="station_name",

        orientation="h",

        title=(
            "Stations with Highest Net Bike Outflow"
        ),

        labels={
            "net_flow": (
                "Net Flow (Arrivals − Departures)"
            ),
            "station_name": "Station",
        },
    )

    st.plotly_chart(
        loss_fig,
        width="stretch",
    )


with right:
    gains = (
        filtered
        .nlargest(
            top_n,
            "net_flow",
        )
        .sort_values(
            "net_flow",
            ascending=True,
        )
    )

    gain_fig = px.bar(
        gains,

        x="net_flow",

        y="station_name",

        orientation="h",

        title=(
            "Stations with Highest Net Bike Inflow"
        ),

        labels={
            "net_flow": (
                "Net Flow (Arrivals − Departures)"
            ),
            "station_name": "Station",
        },
    )

    st.plotly_chart(
        gain_fig,
        width="stretch",
    )


st.divider()


# ---------------------------------------------------------
# IMBALANCE RATIO
# ---------------------------------------------------------

st.subheader(
    "High-Activity Stations with Strong Imbalance"
)


imbalance = (
    filtered
    .assign(
        imbalance_pct=(
            filtered["imbalance_ratio"]
            * 100
        )
    )
    .nlargest(
        top_n,
        "imbalance_ratio",
    )
    .sort_values(
        "imbalance_pct",
        ascending=True,
    )
)


imbalance_fig = px.bar(
    imbalance,

    x="imbalance_pct",

    y="station_name",

    orientation="h",

    title=(
        "Station Imbalance Ratio"
    ),

    labels={
        "imbalance_pct":
            "Absolute Imbalance (%)",

        "station_name":
            "Station",
    },
)


st.plotly_chart(
    imbalance_fig,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------
# TOP ROUTES
# ---------------------------------------------------------

st.subheader(
    "Most Frequent Station-to-Station Flows"
)


route_limit = st.slider(
    "Number of routes",
    min_value=5,
    max_value=20,
    value=10,
)


routes = load_top_routes(
    route_limit
)


routes["route"] = (
    routes["start_station_name"]
    + " → "
    + routes["end_station_name"]
)


route_fig = px.bar(
    routes.sort_values(
        "rides",
        ascending=True,
    ),

    x="rides",

    y="route",

    orientation="h",

    title="Top Origin–Destination Routes",

    labels={
        "rides": "Trips",
        "route": "Route",
    },
)


st.plotly_chart(
    route_fig,
    width="stretch",
)


st.info(
    """
    Net station flow reflects rider trips only.
    Operator rebalancing movements are not present
    in the trip history dataset, so these metrics
    indicate rebalancing pressure rather than
    exact station inventory changes.
    """
)