import html

import streamlit as st

KPI_STYLE = {
    "Total Rides": {
        "icon": "👥",
        "accent": "#2F9BFF",
        "tint": "#EAF6FF",
        "sub": "Trips in active selection",
    },
    "Median Ride Duration": {
        "icon": "◷",
        "accent": "#24C99A",
        "tint": "#E9FFF7",
        "sub": "Typical trip duration",
    },
    "Member Share": {
        "icon": "♟",
        "accent": "#FF9F1C",
        "tint": "#FFF7E8",
        "sub": "Rider composition",
    },
    "Electric Bike Share": {
        "icon": "◆",
        "accent": "#9A5CFF",
        "tint": "#F5EEFF",
        "sub": "Bike-type composition",
    },
    "Stations Analyzed": {
        "icon": "⌖",
        "accent": "#2F9BFF",
        "tint": "#EAF6FF",
        "sub": "Stations meeting activity filter",
    },
    "Median Imbalance": {
        "icon": "↔",
        "accent": "#24C99A",
        "tint": "#E9FFF7",
        "sub": "Typical rider-flow imbalance",
    },
    "Largest Net Outflow": {
        "icon": "↗",
        "accent": "#FF5D6C",
        "tint": "#FFF0F3",
        "sub": "Strongest rider-driven outflow",
    },
    "Largest Net Inflow": {
        "icon": "↙",
        "accent": "#2F9BFF",
        "tint": "#EAF6FF",
        "sub": "Strongest rider-driven inflow",
    },
    "Peak Hour": {
        "icon": "◷",
        "accent": "#2F9BFF",
        "tint": "#EAF6FF",
        "sub": "Highest average hourly demand",
    },
    "Busiest Day": {
        "icon": "▦",
        "accent": "#9A5CFF",
        "tint": "#F5EEFF",
        "sub": "Highest average daily demand",
    },
    "Strongest Time Slot": {
        "icon": "⚡",
        "accent": "#FF9F1C",
        "tint": "#FFF7E8",
        "sub": "Strongest recurring weekday-hour",
    },
    "Weekend vs Weekday": {
        "icon": "☀",
        "accent": "#24C99A",
        "tint": "#E9FFF7",
        "sub": "Average daily demand difference",
    },
    "Temp Association": {
        "icon": "🌡",
        "accent": "#2F9BFF",
        "tint": "#EAF6FF",
        "sub": "Adjusted-demand association",
    },
    "Rain Association": {
        "icon": "☂",
        "accent": "#FF9F1C",
        "tint": "#FFF7E8",
        "sub": "Adjusted-demand association",
    },
    "Dry Hours vs Expected": {
        "icon": "☀",
        "accent": "#24C99A",
        "tint": "#E9FFF7",
        "sub": "Demand relative to baseline",
    },
    "Wet vs Dry": {
        "icon": "☔",
        "accent": "#FF5D6C",
        "tint": "#FFF0F3",
        "sub": "Adjusted demand gap",
    },
}

FALLBACK_STYLES = [
    ("◉", "#2F9BFF", "#EAF6FF"),
    ("◷", "#24C99A", "#E9FFF7"),
    ("◆", "#FF9F1C", "#FFF7E8"),
    ("✦", "#9A5CFF", "#F5EEFF"),
]

def metric_row(
    metrics: list[tuple[str, str] | tuple[str, str, str]],
) -> None:
    columns = st.columns(
        len(metrics),
        gap="medium",
    )

    for index, (column, metric) in enumerate(
        zip(columns, metrics, strict=True)
    ):
        label = metric[0]
        value = metric[1]
        custom_sub = metric[2] if len(metric) == 3 else None

        config = KPI_STYLE.get(label)

        if config is None:
            icon, accent, tint = FALLBACK_STYLES[
                index % len(FALLBACK_STYLES)
            ]
            default_sub = "Active selection"
        else:
            icon = config["icon"]
            accent = config["accent"]
            tint = config["tint"]
            default_sub = config["sub"]

        sub = custom_sub or default_sub

        safe_label = html.escape(label)
        safe_value = html.escape(value)
        safe_icon = html.escape(icon)
        safe_sub = html.escape(sub)

        with column:
            st.html(
                '<div class="uf-kpi" '
                f'style="--uf-kpi-accent:{accent};'
                f'--uf-kpi-tint:{tint};">'
                '<div class="uf-kpi-head">'
                '<div class="uf-kpi-icon">'
                f'{safe_icon}'
                '</div>'
                '<div class="uf-kpi-label">'
                f'{safe_label}'
                '</div>'
                '</div>'
                '<div class="uf-kpi-value">'
                f'{safe_value}'
                '</div>'
                '<div class="uf-kpi-sub">'
                f'{safe_sub}'
                '</div>'
                '</div>'
            )
