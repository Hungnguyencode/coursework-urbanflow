import duckdb
import plotly.express as px
import pydeck as pdk
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
    page_title="Mobility Flow | UrbanFlow",
    page_icon="🗺️",
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

        ORDER BY
            total_activity DESC;
        """
    ).fetchdf()


@st.cache_data
def load_top_routes(
    limit: int,
):
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

        ORDER BY
            rides DESC

        LIMIT ?;
        """,
        [limit],
    ).fetchdf()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

page_header(
    title="Mobility Flow",
    icon="🗺️",
    subtitle=(
        "Explore how rider trips redistribute bike demand "
        "across stations and reveal areas with persistent "
        "inflow or outflow pressure."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

stations = load_station_metrics()


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.header(
    "Flow Filters"
)

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

flow_view = st.sidebar.selectbox(
    "Map view",
    [
        "All stations",
        "Net outflow only",
        "Net inflow only",
        "High imbalance only",
    ],
)

filtered = stations[
    stations["total_activity"]
    >= min_activity
].copy()


# ---------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------

if filtered.empty:
    st.warning(
        "No stations match the current activity filter. "
        "Lower the minimum station activity to continue."
    )

    st.stop()


# ---------------------------------------------------------
# KPI SUMMARY
# ---------------------------------------------------------

station_count = len(
    filtered
)

largest_loss = filtered.loc[
    filtered["net_flow"].idxmin()
]

largest_gain = filtered.loc[
    filtered["net_flow"].idxmax()
]

median_imbalance = (
    filtered["imbalance_ratio"]
    .median()
    * 100
)

kpi1, kpi2, kpi3, kpi4 = st.columns(
    4,
    gap="medium",
)

with kpi1:
    st.metric(
        "Stations Analyzed",
        f"{station_count:,}",
    )

with kpi2:
    st.metric(
        "Median Imbalance",
        f"{median_imbalance:.1f}%",
    )

with kpi3:
    st.metric(
        "Largest Net Outflow",
        f"{int(largest_loss['net_flow']):,}",
    )

    st.caption(
        largest_loss["station_name"]
    )

with kpi4:
    st.metric(
        "Largest Net Inflow",
        f"+{int(largest_gain['net_flow']):,}",
    )

    st.caption(
        largest_gain["station_name"]
    )


# ---------------------------------------------------------
# FLOW MAP
# ---------------------------------------------------------

section_header(
    "Station Flow Map",
    (
        "Circle size represents station activity. "
        "Blue indicates net inflow; red indicates "
        "net outflow."
    ),
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
        map_data["imbalance_ratio"]
        >= 0.05
    ].copy()


if map_data.empty:
    st.info(
        "No stations match the selected map view."
    )

else:

    def flow_color(
        net_flow,
    ):
        if net_flow < 0:
            return [
                220,
                70,
                70,
                175,
            ]

        if net_flow > 0:
            return [
                15,
                108,
                189,
                175,
            ]

        return [
            140,
            140,
            140,
            150,
        ]


    map_data["color"] = (
        map_data["net_flow"]
        .apply(
            flow_color
        )
    )

    map_data["radius"] = (
        4
        + map_data[
            "total_activity"
        ]
        .rank(
            pct=True
        )
        * 14
    )

    map_data["imbalance_pct"] = (
        map_data[
            "imbalance_ratio"
        ]
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
        opacity=0.65,
        stroked=True,
        get_line_color=[
            255,
            255,
            255,
            130,
        ],
        line_width_min_pixels=1,
    )

    view_state = pdk.ViewState(
        latitude=float(
            map_data[
                "latitude"
            ].median()
        ),
        longitude=float(
            map_data[
                "longitude"
            ].median()
        ),
        zoom=11,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{station_name}</b><br/>"
            "Departures: {departures}<br/>"
            "Arrivals: {arrivals}<br/>"
            "Net flow: {net_flow}<br/>"
            "Activity: {total_activity}<br/>"
            "Imbalance: {imbalance_pct}%"
        ),
        "style": {
            "backgroundColor":
                "#0B1F33",
            "color":
                "white",
        },
    }

    deck = pdk.Deck(
        layers=[
            layer,
        ],
        initial_view_state=(
            view_state
        ),
        tooltip=tooltip,
        map_style=None,
    )

    st.pydeck_chart(
        deck,
        width="stretch",
    )


# ---------------------------------------------------------
# FLOW RANKINGS
# ---------------------------------------------------------

section_header(
    "Net Flow Extremes",
    (
        "Stations experiencing the strongest observed "
        "rider-driven outflow and inflow."
    ),
)

left, right = st.columns(
    2,
    gap="large",
)


# ---------------------------------------------------------
# OUTFLOW
# ---------------------------------------------------------

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
            "Highest Net Bike Outflow"
        ),
        labels={
            "net_flow":
                "Net Flow",
            "station_name":
                "Station",
        },
    )

    style_figure(
        loss_fig,
        height=430,
    )

    loss_fig.update_traces(
        marker_color="#EF4444",
        marker_line_width=0,
    )

    loss_fig.update_layout(
        yaxis_title=None,
        showlegend=False,
    )

    st.plotly_chart(
        loss_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# INFLOW
# ---------------------------------------------------------

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
            "Highest Net Bike Inflow"
        ),
        labels={
            "net_flow":
                "Net Flow",
            "station_name":
                "Station",
        },
    )

    style_figure(
        gain_fig,
        height=430,
    )

    gain_fig.update_traces(
        marker_color="#0F6CBD",
        marker_line_width=0,
    )

    gain_fig.update_layout(
        yaxis_title=None,
        showlegend=False,
    )

    st.plotly_chart(
        gain_fig,
        width="stretch",
    )


# ---------------------------------------------------------
# IMBALANCE
# ---------------------------------------------------------

section_header(
    "Rebalancing Pressure",
    (
        "High-activity stations with the strongest "
        "absolute imbalance between arrivals "
        "and departures."
    ),
)

imbalance = (
    filtered
    .assign(
        imbalance_pct=(
            filtered[
                "imbalance_ratio"
            ]
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

style_figure(
    imbalance_fig,
    height=470,
)

imbalance_fig.update_traces(
    marker_color="#F59E0B",
    marker_line_width=0,
)

imbalance_fig.update_layout(
    yaxis_title=None,
    showlegend=False,
)

st.plotly_chart(
    imbalance_fig,
    width="stretch",
)


# ---------------------------------------------------------
# OD ROUTES
# ---------------------------------------------------------

section_header(
    "Most Frequent OD Flows",
    (
        "The most frequently observed station-to-station "
        "trip pairs in the active dataset."
    ),
)

route_limit = st.slider(
    "Number of routes shown",
    min_value=5,
    max_value=20,
    value=10,
)

routes = load_top_routes(
    route_limit
)

routes["route"] = (
    routes[
        "start_station_name"
    ]
    + " → "
    + routes[
        "end_station_name"
    ]
)

route_fig = px.bar(
    routes.sort_values(
        "rides",
        ascending=True,
    ),
    x="rides",
    y="route",
    orientation="h",
    title=(
        "Top Origin–Destination Routes"
    ),
    labels={
        "rides":
            "Trips",
        "route":
            "Route",
    },
)

style_figure(
    route_fig,
    height=500,
)

route_fig.update_traces(
    marker_color="#14B8A6",
    marker_line_width=0,
)

route_fig.update_layout(
    yaxis_title=None,
    showlegend=False,
)

st.plotly_chart(
    route_fig,
    width="stretch",
)


# ---------------------------------------------------------
# CAVEAT
# ---------------------------------------------------------

note_card(
    title="Interpretation note",
    body=(
        "Net station flow reflects rider trips only. "
        "Operator rebalancing movements are not included "
        "in the trip-history dataset. These metrics "
        "therefore indicate rebalancing pressure rather "
        "than exact station inventory change."
    ),
)