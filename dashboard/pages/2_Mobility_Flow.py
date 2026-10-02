import duckdb
import plotly.express as px
import pydeck as pdk
import streamlit as st
from components.charts import style_figure
from components.health import render_sidebar_health
from components.refresh import (
    load_refresh_context,
    sync_refresh_cache,
)
from components.ui import (
    inject_global_css,
    note_card,
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
# HERO
# ---------------------------------------------------------

page_header(
    title="Mobility Flow",
    icon="🗺️",
    subtitle=(
        "Follow how rider trips redistribute demand across "
        "New York City's Citi Bike network and identify "
        "stations under persistent inflow or outflow pressure."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)


# ---------------------------------------------------------
# DATA
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

route_limit = st.sidebar.slider(
    "OD routes shown",
    min_value=5,
    max_value=20,
    value=10,
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
# 01 · STATION FLOW
# ---------------------------------------------------------

section_header(
    "Station Flow Map",
    (
        "Explore rider-driven redistribution across active "
        "stations. Circle size represents station activity; "
        "blue indicates net inflow and red indicates net outflow."
    ),
    index="01 · STATION FLOW",
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
                239,
                68,
                68,
                180,
            ]

        if net_flow > 0:
            return [
                15,
                108,
                189,
                180,
            ]

        return [
            148,
            163,
            184,
            155,
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
        * 15
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
        radius_max_pixels=21,
        pickable=True,
        auto_highlight=True,
        opacity=0.68,
        stroked=True,
        get_line_color=[
            255,
            255,
            255,
            145,
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
        zoom=11.6,
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
            "backgroundColor": "#081D33",
            "color": "white",
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
# 02 · FLOW EXTREMES
# ---------------------------------------------------------

section_header(
    "Flow Extremes",
    (
        "Compare stations experiencing the strongest observed "
        "rider-driven net outflow and net inflow."
    ),
    index="02 · FLOW EXTREMES",
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
        title="Highest Net Bike Outflow",
        labels={
            "net_flow": "Net Flow",
            "station_name": "Station",
        },
    )


    style_figure(
        loss_fig,
        height=430,
    )


    loss_fig.update_traces(
        marker_color="#EF4444",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Net flow: %{x:,}"
            "<extra></extra>"
        ),
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
        title="Highest Net Bike Inflow",
        labels={
            "net_flow": "Net Flow",
            "station_name": "Station",
        },
    )


    style_figure(
        gain_fig,
        height=430,
    )


    gain_fig.update_traces(
        marker_color="#0F6CBD",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Net flow: +%{x:,}"
            "<extra></extra>"
        ),
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
# 03 · NETWORK PRESSURE
# ---------------------------------------------------------

section_header(
    "Network Pressure",
    (
        "Bring together station imbalance and high-frequency "
        "origin–destination corridors to highlight where "
        "operational pressure may concentrate."
    ),
    index="03 · NETWORK PRESSURE",
)


pressure_left, pressure_right = st.columns(
    [1, 1.35],
    gap="large",
)


# ---------------------------------------------------------
# IMBALANCE
# ---------------------------------------------------------

with pressure_left:
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
        title="Rebalancing Pressure",
        labels={
            "imbalance_pct":
                "Absolute Imbalance (%)",
            "station_name":
                "Station",
        },
    )


    style_figure(
        imbalance_fig,
        height=510,
    )


    imbalance_fig.update_traces(
        marker_color="#F59E0B",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Imbalance: %{x:.1f}%"
            "<extra></extra>"
        ),
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

with pressure_right:
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
        title="Top Origin–Destination Routes",
        labels={
            "rides": "Trips",
            "route": "Route",
        },
    )


    style_figure(
        route_fig,
        height=510,
    )


    route_fig.update_traces(
        marker_color="#14B8A6",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Trips: %{x:,}"
            "<extra></extra>"
        ),
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
# INTERPRETATION
# ---------------------------------------------------------

note_card(
    title="How to read network pressure",
    body=(
        "Net station flow reflects rider trips only. "
        "Operator rebalancing movements are not included "
        "in the trip-history dataset. These metrics therefore "
        "indicate rebalancing pressure rather than exact "
        "station inventory change."
    ),
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

page_footer(
    period=refresh.period_label,
)