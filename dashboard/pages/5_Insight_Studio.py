
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.charts import style_figure
from components.health import render_sidebar_health
from components.kpis import metric_row
from components.refresh import load_refresh_context, sync_refresh_cache
from components.ui import (
    inject_global_css,
    insight_card,
    note_card,
    page_footer,
    page_header,
    section_header,
    sidebar_data_status,
)
from urbanflow.config import PROJECT_ROOT


# =========================================================
# CONFIGURATION
# =========================================================

HISTORY_PATH = (
    PROJECT_ROOT / "dashboard" / "data" / "monthly_history.json"
)

st.set_page_config(
    page_title="Insight Studio | UrbanFlow",
    page_icon="💡",
    layout="wide",
)

inject_global_css()

refresh = load_refresh_context()
sync_refresh_cache(refresh)

sidebar_data_status(
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)

render_sidebar_health(
    expected_hours=refresh.period.expected_hours,
)


# =========================================================
# HERO
# =========================================================

page_header(
    title="Insight Studio",
    icon="💡",
    subtitle=(
        "Understand what changes across months, "
        "why those changes matter, and where the "
        "data deserves a closer look."
    ),
    period=refresh.period_label,
    last_refresh=refresh.last_refresh_label,
)


# =========================================================
# HELPERS
# =========================================================

def month_label(key):
    return pd.to_datetime(key + "-01").strftime("%B %Y")


def show_chart(fig, height=390):
    style_figure(fig, height=height)
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
    )


def change_pct(new, old):
    if old == 0:
        return float("nan")
    return (new / old - 1) * 100


def rider_group_changes(a, b):
    """
    Calculate average daily rides by rider group.

    The monthly history stores member_share as a percentage
    of all trips. The remaining trips are treated as casual,
    consistent with the current two-group Citi Bike dataset.
    """

    member_a = (
        a["avg_per_day"] * a["member_share"] / 100
    )

    member_b = (
        b["avg_per_day"] * b["member_share"] / 100
    )

    casual_a = a["avg_per_day"] - member_a
    casual_b = b["avg_per_day"] - member_b

    return {
        "member_a": member_a,
        "member_b": member_b,
        "casual_a": casual_a,
        "casual_b": casual_b,
        "member_change": change_pct(member_b, member_a),
        "casual_change": change_pct(casual_b, casual_a),
    }


# =========================================================
# INSIGHT STUDIO
# =========================================================

@st.fragment(run_every="60s")
def insight_studio():

    # -----------------------------------------------------
    # LOAD MONTHLY HISTORY
    # -----------------------------------------------------

    if not HISTORY_PATH.exists():
        st.warning(
            "Monthly history is not available. Run "
            "`uv run python scripts/build_monthly_history.py --all`."
        )
        return

    try:
        history = json.loads(
            HISTORY_PATH.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        st.error(f"Cannot read monthly history: {exc}")
        return

    months = history.get("months", {})
    keys = sorted(months)

    if not keys:
        st.warning("No validated months are available.")
        return

    rows = []

    for key in keys:
        item = months[key]

        rows.append({
            "period": key,
            "month": month_label(key),
            "total_rides": item["total_rides"],
            "avg_per_day": item["avg_per_day"],
            "member_share": item["member_share"],
            "electric_share": item["electric_share"],
            "wet_hour_share": item["wet_hour_share"],
        })

    monthly = pd.DataFrame(rows)

    latest = monthly.iloc[-1]
    previous = (
        monthly.iloc[-2]
        if len(monthly) >= 2
        else None
    )

    if previous is not None:
        latest_change = change_pct(
            latest["avg_per_day"],
            previous["avg_per_day"],
        )
        change_label = f"{latest_change:+.2f}%"
    else:
        change_label = "N/A"

    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    metric_row([
        (
            "Months Available",
            str(len(keys)),
            "Validated monthly datasets",
        ),
        (
            "Latest Period",
            month_label(keys[-1]),
            "Latest historical observation",
        ),
        (
            "Average / Day",
            f"{latest['avg_per_day']:,.0f}",
            "Latest month",
        ),
        (
            "Monthly Change",
            change_label,
            "Daily average vs previous available month",
        ),
    ])

    st.caption(
        "Research reference: August 2026. "
        "Monthly history is stored separately and updates "
        "without replacing the research database."
    )

    tab1, tab2 = st.tabs([
        "📈 Monthly Intelligence",
        "🔎 Research Deep Dive",
    ])

    # =====================================================
    # TAB 1 — MONTHLY INTELLIGENCE
    # =====================================================

    with tab1:

        section_header(
            "How is mobility changing across months?",
            (
                "Compare demand after accounting for "
                "different month lengths and examine "
                "rider composition."
            ),
            index="01 · MONTHLY DEMAND",
        )

        c1, c2 = st.columns([1.4, 1], gap="large")

        # -------------------------------------------------
        # MONTHLY DEMAND CHART
        # -------------------------------------------------

        with c1:

            fig = px.line(
                monthly,
                x="month",
                y="avg_per_day",
                markers=True,
                title="Average Daily Rides by Month",
                labels={
                    "month": "Month",
                    "avg_per_day": "Average rides per day",
                },
            )

            fig.update_traces(
                line=dict(
                    color="#0B6BFF",
                    width=4,
                ),
                marker=dict(size=10),
            )

            fig.update_yaxes(rangemode="tozero")
            show_chart(fig)

        # -------------------------------------------------
        # RIDER AND BIKE COMPOSITION
        # -------------------------------------------------

        with c2:

            composition = monthly.melt(
                id_vars="month",
                value_vars=[
                    "member_share",
                    "electric_share",
                ],
                var_name="metric",
                value_name="percentage",
            )

            composition["metric"] = (
                composition["metric"].map({
                    "member_share": "Member rides",
                    "electric_share": "Electric bike rides",
                })
            )

            fig = px.line(
                composition,
                x="month",
                y="percentage",
                color="metric",
                markers=True,
                title="Rider and Bike Composition",
                labels={
                    "month": "Month",
                    "percentage": "Share of trips (%)",
                    "metric": "",
                },
                color_discrete_map={
                    "Member rides": "#0B6BFF",
                    "Electric bike rides": "#13C8A3",
                },
            )

            fig.update_yaxes(range=[0, 100])
            show_chart(fig)

        # =================================================
        # COMPARATIVE INSIGHTS
        # =================================================

        section_header(
            "What changed between two months?",
            (
                "Select any two observed periods "
                "to compare the evidence."
            ),
            index="02 · COMPARATIVE INSIGHTS",
        )

        if len(keys) < 2:

            note_card(
                title="Waiting for another month",
                body=(
                    "Only one validated month is available. "
                    "Comparative insights will appear when "
                    "a second month has been processed."
                ),
            )

        else:

            col1, col2 = st.columns(2)

            with col1:
                baseline_key = st.selectbox(
                    "Reference month",
                    keys,
                    index=len(keys) - 2,
                    format_func=month_label,
                )

            with col2:
                comparison_key = st.selectbox(
                    "Comparison month",
                    keys,
                    index=len(keys) - 1,
                    format_func=month_label,
                )

            if baseline_key == comparison_key:

                st.info("Choose two different months.")

            else:

                a = months[baseline_key]
                b = months[comparison_key]

                # -----------------------------------------
                # CORE METRIC CHANGES
                # -----------------------------------------

                demand_delta = change_pct(
                    b["avg_per_day"],
                    a["avg_per_day"],
                )

                member_delta = (
                    b["member_share"]
                    - a["member_share"]
                )

                electric_delta = (
                    b["electric_share"]
                    - a["electric_share"]
                )

                rain_delta = (
                    b["wet_hour_share"]
                    - a["wet_hour_share"]
                )

                # -----------------------------------------
                # RIDER GROUP ANALYSIS
                # -----------------------------------------

                groups = rider_group_changes(a, b)

                member_change = groups["member_change"]
                casual_change = groups["casual_change"]

                # Determine which group changed more.
                member_abs_change = abs(
                    groups["member_b"] - groups["member_a"]
                )

                casual_abs_change = abs(
                    groups["casual_b"] - groups["casual_a"]
                )

                if member_abs_change > casual_abs_change:
                    dominant_group = "member"
                elif casual_abs_change > member_abs_change:
                    dominant_group = "casual"
                else:
                    dominant_group = "both groups equally"

                # -----------------------------------------
                # INSIGHT CARDS
                # -----------------------------------------

                left, right = st.columns(
                    2,
                    gap="large",
                )

                with left:

                    insight_card(
                        title="Demand: what changed?",
                        icon="📈",
                        accent="#0B6BFF",
                        body=(
                            f"{month_label(comparison_key)} averaged "
                            f"{b['avg_per_day']:,.0f} rides/day "
                            f"versus {a['avg_per_day']:,.0f} "
                            f"in {month_label(baseline_key)} "
                            f"({demand_delta:+.2f}%). "
                            "Daily averages account for "
                            "different month lengths."
                        ),
                    )

                    insight_card(
                        title="Who is driving the demand change?",
                        icon="👥",
                        accent="#13C8A3",
                        body=(
                            f"Member rides/day: "
                            f"{member_change:+.1f}%. "
                            f"Casual rides/day: "
                            f"{casual_change:+.1f}%. "
                            f"The larger absolute change "
                            f"is in the {dominant_group} group. "
                            f"Electric-bike share: "
                            f"{electric_delta:+.2f} pp."
                        ),
                    )

                with right:

                    insight_card(
                        title="Weather context",
                        icon="🌦️",
                        accent="#FF9F1C",
                        body=(
                            f"The share of hours with rain "
                            f"changed by {rain_delta:+.2f} "
                            "percentage points between "
                            "these months. This is context, "
                            "not proof that rainfall caused "
                            "the ridership change."
                        ),
                    )

                    note_card(
                        title="Interpretation boundary",
                        body=(
                            "Changes may reflect weekday mix, "
                            "holidays, seasonality and other "
                            "unobserved factors. The rider-group "
                            "breakdown assumes member and casual "
                            "are the only trip categories. "
                            "Two months do not establish "
                            "a long-term trend."
                        ),
                    )

                # =========================================
                # DAILY PROFILE COMPARISON
                # =========================================

                section_header(
                    "When during the month did demand differ?",
                    (
                        "Overlay daily profiles of the "
                        "selected months to investigate "
                        "differences in demand."
                    ),
                    index="03 · DAILY PROFILE COMPARISON",
                )

                fig = go.Figure()

                for key, color in [
                    (baseline_key, "#0B6BFF"),
                    (comparison_key, "#13C8A3"),
                ]:

                    records = months[key]["daily"]

                    fig.add_trace(
                        go.Scatter(
                            x=[
                                int(item["date"][-2:])
                                for item in records
                            ],
                            y=[
                                item["rides"]
                                for item in records
                            ],
                            mode="lines+markers",
                            name=month_label(key),
                            line=dict(
                                width=3,
                                color=color,
                            ),
                        )
                    )

                fig.update_layout(
                    title="Daily Ride Profiles — Month Overlay",
                    xaxis_title="Day of month",
                    yaxis_title="Rides",
                )

                fig.update_xaxes(
                    dtick=2,
                    range=[1, 31],
                )

                show_chart(fig, 420)

                note_card(
                    title="How to read these two lines",
                    body=(
                        "The same day number is not necessarily "
                        "the same weekday in both months. "
                        "The overlay reveals variations "
                        "within each month but does not "
                        "identify their causes."
                    ),
                )

    # =====================================================
    # TAB 2 — RESEARCH DEEP DIVE
    # =====================================================

    with tab2:

        section_header(
            "Explore unusual days",
            (
                "Investigate historical anomalies using "
                "a same-weekday reference that excludes "
                "the chosen day."
            ),
            index="04 · ANOMALY EXPLORER",
        )

        # -------------------------------------------------
        # CHOOSE RESEARCH SNAPSHOT
        # -------------------------------------------------

        default_month = (
            keys.index("2026-08")
            if "2026-08" in keys
            else 0
        )

        research_key = st.selectbox(
            "Research snapshot",
            keys,
            index=default_month,
            format_func=month_label,
        )

        record = months[research_key]

        daily = pd.DataFrame(record["daily"])

        daily["date"] = pd.to_datetime(
            daily["date"]
        )

        daily["weekday"] = (
            daily["date"].dt.dayofweek
        )

        # -------------------------------------------------
        # LEAVE-ONE-OUT REFERENCE
        # -------------------------------------------------

        weekday_group = daily.groupby(
            "weekday"
        )["rides"]

        peer_count = (
            weekday_group.transform("count") - 1
        )

        daily["reference"] = (
            weekday_group.transform("sum")
            - daily["rides"]
        ) / peer_count.replace(0, float("nan"))

        daily["gap_pct"] = (
            daily["rides"] / daily["reference"] - 1
        ) * 100

        valid = daily["gap_pct"].dropna()

        default_day = (
            int(valid.idxmin())
            if not valid.empty
            else 0
        )

        selected_index = st.selectbox(
            "Choose a day to investigate",
            daily.index.tolist(),
            index=default_day,
            format_func=lambda i: (
                daily.loc[i, "date"].strftime(
                    "%b %d, %Y"
                )
            ),
        )

        selected = daily.loc[selected_index]

        selected_date = (
            selected["date"].strftime("%Y-%m-%d")
        )

        selected_weekday = selected["weekday"]

        # -------------------------------------------------
        # HOURLY ANALYSIS
        # -------------------------------------------------

        hourly = pd.DataFrame(
            record["hourly"]
        )

        hourly["weekday"] = (
            pd.to_datetime(
                hourly["date"]
            ).dt.dayofweek
        )

        same_weekday = hourly[
            hourly["weekday"] == selected_weekday
        ]

        peer_hours = (
            same_weekday[
                same_weekday["date"] != selected_date
            ]
            .groupby("hour")["rides"]
            .mean()
        )

        selected_hours = hourly[
            hourly["date"] == selected_date
        ].sort_values("hour")

        # -------------------------------------------------
        # ANOMALY INSIGHT
        # -------------------------------------------------

        day_gap = selected["gap_pct"]

        if pd.notna(day_gap):
            gap_text = (
                f"{day_gap:+.1f}% versus "
                "other same weekdays"
            )
        else:
            gap_text = (
                "insufficient comparison days"
            )

        insight_card(
            title=f"Investigation: {selected_date}",
            icon="🔎",
            accent="#FF9F1C",
            body=(
                f"{int(selected['rides']):,} trips, "
                f"{gap_text}. "
                f"Recorded rainfall: "
                f"{selected['rainfall_mm']:.1f} mm."
            ),
        )

        # -------------------------------------------------
        # ANOMALY CHARTS
        # -------------------------------------------------

        c1, c2 = st.columns(
            [1.5, 1],
            gap="large",
        )

        with c1:

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=selected_hours["hour"],
                    y=selected_hours["rides"],
                    name="Observed rides",
                    mode="lines+markers",
                    line=dict(
                        color="#0B6BFF",
                        width=3,
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=peer_hours.index,
                    y=peer_hours.values,
                    name="Other same weekdays",
                    mode="lines",
                    line=dict(
                        color="#13C8A3",
                        dash="dash",
                        width=3,
                    ),
                )
            )

            fig.update_layout(
                title="Observed vs Same-Weekday Reference",
                xaxis_title="Hour",
                yaxis_title="Rides",
            )

            show_chart(fig, 400)

        with c2:

            fig = px.bar(
                selected_hours,
                x="hour",
                y="precipitation_mm",
                title="Hourly Rainfall",
                labels={
                    "hour": "Hour",
                    "precipitation_mm": "Rainfall (mm)",
                },
            )

            fig.update_traces(
                marker_color="#0B6BFF"
            )

            show_chart(fig, 400)

        # -------------------------------------------------
        # INTERPRETATION
        # -------------------------------------------------

        note_card(
            title="What this investigation means",
            body=(
                "The reference excludes the day being "
                "investigated. This helps identify unusual "
                "daily patterns, but cannot establish why "
                "they occurred. Rainfall is one contextual "
                "variable, not a complete explanation "
                "of mobility demand."
            ),
        )

    # =====================================================
    # FOOTER
    # =====================================================

    page_footer(
        period=refresh.period_label
    )


insight_studio()
