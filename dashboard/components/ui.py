import html

import streamlit as st

GLOBAL_CSS = """
<style>
:root {
    --uf-navy: #0B1F33;
    --uf-blue: #0F6CBD;
    --uf-blue-soft: #EAF3FF;
    --uf-teal: #14B8A6;
    --uf-slate: #64748B;
    --uf-border: #E2E8F0;
    --uf-bg: #F7F9FC;
    --uf-card: #FFFFFF;
}

.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(15, 108, 189, 0.07),
            transparent 28rem
        ),
        var(--uf-bg);
}

.block-container {
    max-width: 1480px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #F3F7FD 0%,
            #EEF3F9 100%
        );
    border-right: 1px solid var(--uf-border);
}

[data-testid="stSidebar"] > div {
    padding-top: 1.25rem;
}

h1,
h2,
h3 {
    color: var(--uf-navy);
    letter-spacing: -0.02em;
}

p {
    line-height: 1.55;
}

[data-testid="stMetric"] {
    background: var(--uf-card);
    border: 1px solid var(--uf-border);
    border-radius: 18px;
    padding: 1.1rem 1.2rem;
    box-shadow:
        0 8px 24px
        rgba(15, 23, 42, 0.055);
    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow:
        0 12px 30px
        rgba(15, 23, 42, 0.09);
}

[data-testid="stMetricLabel"] {
    color: var(--uf-slate);
    font-size: 0.82rem;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: var(--uf-navy);
    font-weight: 700;
}

[data-testid="stPlotlyChart"] {
    background: var(--uf-card);
    border: 1px solid var(--uf-border);
    border-radius: 18px;
    padding: 0.35rem;
    box-shadow:
        0 8px 24px
        rgba(15, 23, 42, 0.045);
}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    border-radius: 12px;
}

.stButton > button {
    border-radius: 12px;
    font-weight: 600;
}

.uf-hero {
    position: relative;
    overflow: hidden;
    padding: 1.7rem 1.85rem;
    margin-bottom: 1.15rem;
    border-radius: 22px;
    border: 1px solid #DCE8F5;
    background:
        linear-gradient(
            120deg,
            #FFFFFF 0%,
            #EDF6FF 55%,
            #E8FAF7 100%
        );
    box-shadow:
        0 10px 30px
        rgba(15, 108, 189, 0.07);
}

.uf-hero::after {
    content: "";
    position: absolute;
    width: 230px;
    height: 230px;
    right: -75px;
    top: -105px;
    border-radius: 50%;
    background:
        rgba(15, 108, 189, 0.08);
}

.uf-eyebrow {
    position: relative;
    z-index: 1;
    color: var(--uf-blue);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 0.45rem;
}

.uf-title {
    position: relative;
    z-index: 1;
    color: var(--uf-navy);
    font-size: 2.45rem;
    line-height: 1.08;
    font-weight: 800;
    letter-spacing: -0.04em;
    margin: 0;
}

.uf-subtitle {
    position: relative;
    z-index: 1;
    color: #475569;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-top: 0.55rem;
    margin-bottom: 1rem;
    max-width: 830px;
}

.uf-meta {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
}

.uf-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(255, 255, 255, 0.84);
    color: #334155;
    border: 1px solid #D9E5F2;
    border-radius: 999px;
    padding: 0.38rem 0.72rem;
    font-size: 0.78rem;
    font-weight: 650;
}

.uf-section {
    margin-top: 1.75rem;
    margin-bottom: 0.8rem;
}

.uf-section-title {
    color: var(--uf-navy);
    font-size: 1.35rem;
    font-weight: 750;
    margin: 0;
}

.uf-section-caption {
    color: var(--uf-slate);
    font-size: 0.86rem;
    margin-top: 0.25rem;
}

.uf-sidebar-heading {
    color: #64748B;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-top: 1rem;
    margin-bottom: 0.5rem;
}

.uf-status {
    padding: 0.9rem 1rem;
    border-radius: 14px;
    border: 1px solid #D8E6F4;
    background: rgba(255, 255, 255, 0.85);
    margin-bottom: 0.9rem;
    box-shadow:
        0 5px 16px
        rgba(15, 23, 42, 0.04);
}

.uf-status-label {
    color: #64748B;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.uf-status-value {
    color: var(--uf-navy);
    font-size: 0.92rem;
    font-weight: 750;
    margin-top: 0.28rem;
}

.uf-status-refresh {
    color: #64748B;
    font-size: 0.74rem;
    margin-top: 0.35rem;
}

hr {
    border-color: var(--uf-border) !important;
}
.uf-insight {
    display: flex;
    gap: 0.9rem;
    min-height: 132px;
    padding: 1rem 1.05rem;
    border-radius: 16px;
    border: 1px solid #E2E8F0;
    border-top: 3px solid var(--uf-accent);
    background: rgba(255,255,255,0.92);
    box-shadow:
        0 6px 20px
        rgba(15,23,42,0.045);
}

.uf-insight-icon {
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: #F1F5F9;
    font-size: 1rem;
}

.uf-insight-title {
    color: #0B1F33;
    font-size: 0.92rem;
    font-weight: 750;
    margin-bottom: 0.35rem;
}

.uf-insight-body {
    color: #526174;
    font-size: 0.84rem;
    line-height: 1.55;
}

.uf-note {
    padding: 1rem 1.1rem;
    border-radius: 16px;
    border: 1px solid #DDE7F1;
    background:
        linear-gradient(
            120deg,
            #FFFFFF,
            #F6FAFE
        );
    box-shadow:
        0 5px 16px
        rgba(15,23,42,0.035);
}

.uf-note-title {
    color: #0B1F33;
    font-weight: 750;
    font-size: 0.9rem;
    margin-bottom: 0.3rem;
}

.uf-note-body {
    color: #526174;
    font-size: 0.83rem;
    line-height: 1.55;
}
.uf-health {
    padding: 0.9rem 1rem;
    border-radius: 14px;
    border: 1px solid #D8E6F4;
    background: rgba(255,255,255,0.82);
    box-shadow:
        0 5px 16px
        rgba(15,23,42,0.04);
    margin-bottom: 1rem;
}

.uf-health-head {
    color: #0B1F33;
    font-size: 0.82rem;
    font-weight: 750;
    margin-bottom: 0.65rem;
}

.uf-health-row {
    display: flex;
    justify-content: space-between;
    gap: 0.6rem;
    color: #64748B;
    font-size: 0.72rem;
    padding: 0.28rem 0;
    border-bottom: 1px solid #EEF2F7;
}

.uf-health-row:last-child {
    border-bottom: none;
}

.uf-health-row strong {
    color: #334155;
    font-weight: 700;
}
.modebar,
.modebar-container {
    display: none !important;
}
</style>
"""


def inject_global_css() -> None:
    st.html(
        GLOBAL_CSS
    )


def page_header(
    *,
    title: str,
    icon: str,
    subtitle: str,
    period: str,
    last_refresh: str,
) -> None:
    safe_title = html.escape(
        title
    )

    safe_subtitle = html.escape(
        subtitle
    )

    safe_period = html.escape(
        period
    )

    safe_refresh = html.escape(
        last_refresh
    )

    content = (
        '<div class="uf-hero">'
        '<div class="uf-eyebrow">'
        'UrbanFlow · Mobility Intelligence'
        '</div>'
        '<div class="uf-title">'
        f'{safe_title} {icon}'
        '</div>'
        '<div class="uf-subtitle">'
        f'{safe_subtitle}'
        '</div>'
        '<div class="uf-meta">'
        '<span class="uf-pill">'
        f'📅 {safe_period}'
        '</span>'
        '<span class="uf-pill">'
        f'🔄 Refreshed {safe_refresh}'
        '</span>'
        '<span class="uf-pill">'
        '🚲 Citi Bike + Open-Meteo'
        '</span>'
        '</div>'
        '</div>'
    )

    st.html(
        content
    )


def section_header(
    title: str,
    caption: str | None = None,
) -> None:
    safe_title = html.escape(
        title
    )

    content = (
        '<div class="uf-section">'
        '<div class="uf-section-title">'
        f'{safe_title}'
        '</div>'
    )

    if caption is not None:
        safe_caption = html.escape(
            caption
        )

        content += (
            '<div class="uf-section-caption">'
            f'{safe_caption}'
            '</div>'
        )

    content += "</div>"

    st.html(
        content
    )


def sidebar_data_status(
    *,
    period: str,
    last_refresh: str,
) -> None:
    safe_period = html.escape(
        period
    )

    safe_refresh = html.escape(
        last_refresh
    )

    content = (
        '<div class="uf-sidebar-heading">'
        'Data Status'
        '</div>'
        '<div class="uf-status">'
        '<div class="uf-status-label">'
        'Active dataset'
        '</div>'
        '<div class="uf-status-value">'
        f'🟢 {safe_period}'
        '</div>'
        '<div class="uf-status-refresh">'
        f'Last refresh: {safe_refresh}'
        '</div>'
        '</div>'
    )

    with st.sidebar:
        st.html(
            content
        )


def insight_card(
    *,
    title: str,
    body: str,
    icon: str = "💡",
    accent: str = "#0F6CBD",
) -> None:
    safe_title = html.escape(
        title
    )

    safe_body = html.escape(
        body
    )

    safe_icon = html.escape(
        icon
    )

    safe_accent = html.escape(
        accent
    )

    content = (
        '<div class="uf-insight" '
        f'style="--uf-accent:{safe_accent};">'
        '<div class="uf-insight-icon">'
        f'{safe_icon}'
        '</div>'
        '<div class="uf-insight-content">'
        '<div class="uf-insight-title">'
        f'{safe_title}'
        '</div>'
        '<div class="uf-insight-body">'
        f'{safe_body}'
        '</div>'
        '</div>'
        '</div>'
    )

    st.html(
        content
    )


def note_card(
    *,
    title: str,
    body: str,
) -> None:
    safe_title = html.escape(
        title
    )

    safe_body = html.escape(
        body
    )

    content = (
        '<div class="uf-note">'
        '<div class="uf-note-title">'
        f'{safe_title}'
        '</div>'
        '<div class="uf-note-body">'
        f'{safe_body}'
        '</div>'
        '</div>'
    )

    st.html(
        content
    )


def sidebar_health_status(
    *,
    total_rides: int,
    weather_rows: int,
    joined_rows: int,
    expected_hours: int,
    object_count: int,
) -> None:
    rides_label = (
        f"{total_rides / 1_000_000:.2f}M"
        if total_rides >= 1_000_000
        else f"{total_rides:,}"
    )

    weather_ok = (
        weather_rows
        == expected_hours
    )

    join_ok = (
        joined_rows
        == expected_hours
    )

    database_ok = (
        object_count >= 7
    )

    overall_ok = (
        weather_ok
        and join_ok
        and database_ok
    )

    overall_icon = (
        "🟢"
        if overall_ok
        else "🟠"
    )

    weather_icon = (
        "✓"
        if weather_ok
        else "!"
    )

    join_icon = (
        "✓"
        if join_ok
        else "!"
    )

    database_icon = (
        "✓"
        if database_ok
        else "!"
    )

    content = (
        '<div class="uf-sidebar-heading">'
        'System Health'
        '</div>'
        '<div class="uf-health">'
        '<div class="uf-health-head">'
        f'{overall_icon} Pipeline healthy'
        '</div>'
        '<div class="uf-health-row">'
        '<span>Processed rides</span>'
        f'<strong>{rides_label}</strong>'
        '</div>'
        '<div class="uf-health-row">'
        '<span>Weather coverage</span>'
        f'<strong>{weather_icon} '
        f'{weather_rows}/{expected_hours}</strong>'
        '</div>'
        '<div class="uf-health-row">'
        '<span>Weather join</span>'
        f'<strong>{join_icon} '
        f'{joined_rows}/{expected_hours}</strong>'
        '</div>'
        '<div class="uf-health-row">'
        '<span>Analytics objects</span>'
        f'<strong>{database_icon} '
        f'{object_count}</strong>'
        '</div>'
        '</div>'
    )

    with st.sidebar:
        st.html(
            content
        )