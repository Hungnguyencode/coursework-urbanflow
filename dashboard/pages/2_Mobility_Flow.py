import duckdb
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.charts import style_figure
from components.health import render_sidebar_health
from components.kpis import metric_row
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
    sidebar_filter_heading,
    sidebar_filter_summary,
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



sync_refresh_cache(refresh)



sidebar_data_status(

    period=refresh.period_label,

    last_refresh=refresh.last_refresh_label,

)



render_sidebar_health(

    expected_hours=refresh.period.expected_hours,

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



sidebar_filter_heading(

    "Flow Filters",

    "Tune station activity, rankings and map scope",

    icon="⌁",

)



min_activity = st.sidebar.slider(

    "◉ Minimum station activity",

    min_value=100,

    max_value=10_000,

    value=5_000,

    step=100,

)



top_n = st.sidebar.slider(

    "▥ Stations shown in rankings",

    min_value=5,

    max_value=25,

    value=10,

    step=5,

)



route_limit = st.sidebar.slider(

    "↔ OD routes shown",

    min_value=5,

    max_value=20,

    value=10,

)



flow_view = st.sidebar.selectbox(

    "⌖ Map view",

    [

        "All stations",

        "Net outflow only",

        "Net inflow only",

        "High imbalance only",

    ],

)



sidebar_filter_summary(

    f"Activity ≥ {min_activity:,} · Top {top_n} stations · "

    f"{route_limit} OD routes · {flow_view}"

)



filtered = stations[

    stations["total_activity"] >= min_activity

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



station_count = len(filtered)



largest_loss = filtered.loc[

    filtered["net_flow"].idxmin()

]



largest_gain = filtered.loc[

    filtered["net_flow"].idxmax()

]



median_imbalance = (

    filtered["imbalance_ratio"].median() * 100

)



metric_row(

    [

        (

            "Stations Analyzed",

            f"{station_count:,}",

        ),

        (

            "Median Imbalance",

            f"{median_imbalance:.1f}%",

        ),

        (

            "Largest Net Outflow",

            f"{int(largest_loss['net_flow']):,}",

            str(largest_loss["station_name"]),

        ),

        (

            "Largest Net Inflow",

            f"+{int(largest_gain['net_flow']):,}",

            str(largest_gain["station_name"]),

        ),

    ]

)



# ---------------------------------------------------------
# 01 · STATION FLOW
# ---------------------------------------------------------

section_header(
    "Station Flow Map",
    (
        "Explore rider-driven redistribution across the full Citi Bike "
        "station network. Marker size represents station activity; color "
        "shows both the direction and strength of net flow."
    ),
    index="01 · STATION FLOW",
)

# The map intentionally uses the full station network so low-activity
# stations remain visible. Ranking/KPI views still use the sidebar threshold.
map_data = stations.copy()

if flow_view == "Net outflow only":
    map_data = map_data[map_data["net_flow"] < 0].copy()
elif flow_view == "Net inflow only":
    map_data = map_data[map_data["net_flow"] > 0].copy()
elif flow_view == "High imbalance only":
    map_data = map_data[map_data["imbalance_ratio"] >= 0.05].copy()

if map_data.empty:
    st.info("No stations match the selected map view.")
else:
    # Plotly Scattermap uses marker sizes directly in screen pixels. This is
    # deliberate: PyDeck's point-radius clamping made the activity tiers look
    # visually too similar on this dashboard. These four tiers force a clear
    # small / medium / large hierarchy while keeping most stations unobtrusive.
    activity_q65 = float(stations["total_activity"].quantile(0.65))
    activity_q90 = float(stations["total_activity"].quantile(0.90))
    activity_q98 = float(stations["total_activity"].quantile(0.98))

    def activity_marker_size(total_activity):
        if total_activity <= activity_q65:
            return 4
        if total_activity <= activity_q90:
            return 8
        if total_activity <= activity_q98:
            return 15
        return 28

    # Robust color cap: extreme stations remain saturated while the majority
    # of the network still shows useful variation around neutral net flow.
    flow_cap = max(
        float(stations["net_flow"].abs().quantile(0.95)),
        1.0,
    )

    map_data["marker_size"] = map_data["total_activity"].apply(
        activity_marker_size
    )
    map_data["imbalance_pct"] = map_data["imbalance_ratio"] * 100

    map_fig = go.Figure(
        go.Scattermap(
            lat=map_data["latitude"],
            lon=map_data["longitude"],
            mode="markers",
            text=map_data["station_name"],
            customdata=map_data[
                [
                    "departures",
                    "arrivals",
                    "net_flow",
                    "total_activity",
                    "imbalance_pct",
                ]
            ],
            marker={
                "size": map_data["marker_size"],
                "sizemode": "diameter",
                "sizemin": 2,
                "color": map_data["net_flow"],
                "cmin": -flow_cap,
                "cmax": flow_cap,
                "cmid": 0,
                "colorscale": [
                    [0.00, "#FF4F64"],
                    [0.30, "#E78D9B"],
                    [0.50, "#A8B4C5"],
                    [0.70, "#87B2E8"],
                    [1.00, "#1970F5"],
                ],
                "opacity": 0.78,
                "showscale": False,
            },
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Departures: %{customdata[0]:,.0f}<br>"
                "Arrivals: %{customdata[1]:,.0f}<br>"
                "Net flow: %{customdata[2]:+,.0f}<br>"
                "Activity: %{customdata[3]:,.0f}<br>"
                "Imbalance: %{customdata[4]:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    # Important change from the PyDeck versions: OpenStreetMap's standard
    # colored basemap is rendered by Plotly/MapLibre itself. Parks are green,
    # water is blue, and main roads carry their normal map colors.
    map_fig.update_layout(
        map={
            "style": "open-street-map",
            "center": {
                "lat": float(map_data["latitude"].median()),
                "lon": float(map_data["longitude"].median()),
            },
            "zoom": 10.15,
        },
        height=520,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        hoverlabel={
            "bgcolor": "#0B1F3A",
            "font_color": "white",
            "font_size": 13,
        },
    )

    q65_label = f"{activity_q65:,.0f}"
    q90_label = f"{activity_q90:,.0f}"
    q98_label = f"{activity_q98:,.0f}"
    flow_label = f"{flow_cap:,.0f}"

    st.html(
        f"""
        <div style="display:flex;flex-wrap:wrap;gap:16px 28px;align-items:center;
                    margin:0 0 12px 2px;color:#607596;font-size:13px;">
          <div style="display:flex;align-items:center;gap:9px;">
            <span style="font-weight:800;color:#0B1F3A;">Station activity</span>
            <span style="font-size:7px;color:#5F7798;">●</span><span>≤ {q65_label}</span>
            <span style="font-size:13px;color:#5F7798;">●</span><span>{q65_label}–{q90_label}</span>
            <span style="font-size:22px;color:#5F7798;line-height:12px;">●</span><span>{q90_label}–{q98_label}</span>
            <span style="font-size:36px;color:#5F7798;line-height:12px;">●</span><span>Top 2%</span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-weight:800;color:#0B1F3A;">Net flow</span>
            <span style="color:#FF4F64;">−{flow_label}</span>
            <span style="display:inline-block;width:112px;height:8px;border-radius:999px;
                         background:linear-gradient(90deg,#FF4F64 0%,#A8B4C5 50%,#1970F5 100%);"></span>
            <span style="color:#1970F5;">+{flow_label}</span>
          </div>
        </div>
        """
    )

    st.plotly_chart(
        map_fig,
        width="stretch",
        config={
            "displayModeBar": False,
            "scrollZoom": True,
        },
    )

    st.caption(
        "Marker diameter is fixed by network-wide activity tier: 65% tiny, "
        "25% small, 8% medium and the top 2% large · Net-flow color intensity "
        "is scaled to the 95th percentile · Basemap © OpenStreetMap contributors"
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

        height=372,

    )



    loss_fig.update_traces(

        marker_color="#FF5D6C",

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

        height=372,

    )



    gain_fig.update_traces(

        marker_color="#0B6BFF",

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

                filtered["imbalance_ratio"] * 100

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

            "imbalance_pct": "Absolute Imbalance (%)",

            "station_name": "Station",

        },

    )



    style_figure(

        imbalance_fig,

        height=440,

    )



    imbalance_fig.update_traces(

        marker_color="#FF9F1C",

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



    style_figure(

        route_fig,

        height=440,

    )



    route_fig.update_traces(

        marker_color="#13C8A3",

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
