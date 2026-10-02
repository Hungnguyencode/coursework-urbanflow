import html

import streamlit as st

GLOBAL_CSS = """
<style>
:root {
    --uf-navy: #081D33;
    --uf-navy-2: #102A43;
    --uf-blue: #0F6CBD;
    --uf-blue-bright: #2F80ED;
    --uf-blue-soft: #EAF4FF;
    --uf-teal: #14B8A6;
    --uf-amber: #F59E0B;
    --uf-red: #EF4444;
    --uf-violet: #8B5CF6;

    --uf-slate-900: #0F172A;
    --uf-slate-700: #334155;
    --uf-slate-600: #475569;
    --uf-slate-500: #64748B;
    --uf-slate-400: #94A3B8;

    --uf-border: #DFE8F2;
    --uf-border-soft: #EDF2F7;

    --uf-bg: #F5F8FC;
    --uf-card: #FFFFFF;

    --uf-radius-lg: 24px;
    --uf-radius-md: 18px;
    --uf-radius-sm: 13px;

    --uf-shadow:
        0 12px 35px rgba(15, 23, 42, 0.055);
}


/* ---------------------------------------------------------
   APP
   --------------------------------------------------------- */

.stApp {
    background:
        radial-gradient(
            circle at 94% 4%,
            rgba(15, 108, 189, 0.085),
            transparent 27rem
        ),
        linear-gradient(
            180deg,
            #FAFCFF 0%,
            var(--uf-bg) 28%,
            #F7F9FC 100%
        );
}


.block-container {
    max-width: 1460px;
    padding-top: 2.2rem;
    padding-bottom: 5rem;
}


/* ---------------------------------------------------------
   SIDEBAR
   --------------------------------------------------------- */

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #F6F9FD 0%,
            #EFF4FA 100%
        );

    border-right:
        1px solid var(--uf-border);
}


[data-testid="stSidebar"] > div {
    padding-top: 1rem;
}


[data-testid="stSidebarNav"] {
    padding-top: 0.25rem;
    padding-bottom: 0.8rem;
}


[data-testid="stSidebarNav"] a {
    border-radius: 10px;
    margin: 0.12rem 0.35rem;
    padding-top: 0.43rem;
    padding-bottom: 0.43rem;
    transition:
        background 0.16s ease,
        transform 0.16s ease;
}


[data-testid="stSidebarNav"] a:hover {
    background: rgba(15, 108, 189, 0.07);
    transform: translateX(2px);
}


[data-testid="stSidebarNav"] a[aria-current="page"] {
    background:
        linear-gradient(
            90deg,
            rgba(15, 108, 189, 0.13),
            rgba(15, 108, 189, 0.055)
        );
}


[data-testid="stSidebarNav"] a[aria-current="page"] p {
    color: var(--uf-navy);
    font-weight: 700;
}


/* ---------------------------------------------------------
   TYPOGRAPHY
   --------------------------------------------------------- */

h1,
h2,
h3 {
    color: var(--uf-navy);
    letter-spacing: -0.025em;
}


p {
    line-height: 1.6;
}


/* ---------------------------------------------------------
   NATIVE METRICS
   --------------------------------------------------------- */

[data-testid="stMetric"] {
    position: relative;

    min-height: 126px;

    background:
        linear-gradient(
            145deg,
            rgba(255, 255, 255, 1),
            rgba(249, 252, 255, 0.96)
        );

    border:
        1px solid var(--uf-border);

    border-radius:
        var(--uf-radius-md);

    padding:
        1.08rem 1.2rem 1.15rem;

    box-shadow:
        0 8px 24px rgba(15, 23, 42, 0.045);

    overflow: hidden;

    transition:
        transform 0.18s ease,
        box-shadow 0.18s ease,
        border-color 0.18s ease;
}


[data-testid="stMetric"]::before {
    content: "";

    position: absolute;

    left: 0;
    right: 0;
    top: 0;

    height: 3px;

    background:
        linear-gradient(
            90deg,
            var(--uf-blue),
            var(--uf-teal)
        );

    opacity: 0.86;
}


[data-testid="stMetric"]:hover {
    transform: translateY(-2px);

    border-color: #CDDCEB;

    box-shadow:
        0 13px 30px rgba(15, 23, 42, 0.075);
}


[data-testid="stMetricLabel"] {
    color: var(--uf-slate-500);

    font-size: 0.78rem;
    font-weight: 650;

    letter-spacing: 0.015em;
}


[data-testid="stMetricValue"] {
    color: var(--uf-navy);

    font-size: 2.05rem;
    font-weight: 780;

    letter-spacing: -0.04em;
}


/* ---------------------------------------------------------
   CHART SURFACES
   --------------------------------------------------------- */

[data-testid="stPlotlyChart"] {
    background:
        rgba(255, 255, 255, 0.94);

    border:
        1px solid var(--uf-border);

    border-radius:
        20px;

    padding:
        0.3rem;

    box-shadow:
        0 8px 26px rgba(15, 23, 42, 0.035);

    overflow: hidden;
}


[data-testid="stPydeckChart"] {
    border:
        1px solid var(--uf-border);

    border-radius:
        21px;

    overflow: hidden;

    box-shadow:
        0 9px 28px rgba(15, 23, 42, 0.045);
}


/* ---------------------------------------------------------
   INPUTS
   --------------------------------------------------------- */

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    border-radius:
        11px;
}


.stButton > button,
.stDownloadButton > button {
    border-radius:
        11px;

    font-weight:
        650;

    border-color:
        #CCD9E6;

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease;
}


.stButton > button:hover,
.stDownloadButton > button:hover {
    transform:
        translateY(-1px);

    box-shadow:
        0 7px 18px rgba(15, 23, 42, 0.07);
}


/* ---------------------------------------------------------
   HERO
   --------------------------------------------------------- */

.uf-hero {
    position:
        relative;

    overflow:
        hidden;

    padding:
        1.65rem 1.9rem 1.55rem;

    margin-bottom:
        1.35rem;

    border-radius:
        25px;

    border:
        1px solid #D9E7F4;

    background:
        linear-gradient(
            118deg,
            rgba(255,255,255,0.98) 0%,
            #EFF7FF 57%,
            #EAFBF8 100%
        );

    box-shadow:
        0 14px 40px rgba(15, 108, 189, 0.075);
}


.uf-hero::before {
    content:
        "";

    position:
        absolute;

    width:
        360px;

    height:
        360px;

    right:
        -205px;

    top:
        -230px;

    border-radius:
        50%;

    border:
        1px solid rgba(15, 108, 189, 0.10);

    background:
        rgba(15, 108, 189, 0.06);
}


.uf-hero::after {
    content:
        "";

    position:
        absolute;

    width:
        160px;

    height:
        160px;

    right:
        44px;

    bottom:
        -125px;

    border-radius:
        50%;

    background:
        rgba(20, 184, 166, 0.075);
}


.uf-eyebrow {
    position:
        relative;

    z-index:
        2;

    display:
        flex;

    align-items:
        center;

    gap:
        0.5rem;

    color:
        var(--uf-blue);

    font-size:
        0.7rem;

    font-weight:
        850;

    letter-spacing:
        0.12em;

    text-transform:
        uppercase;

    margin-bottom:
        0.55rem;
}


.uf-eyebrow::before {
    content:
        "";

    width:
        24px;

    height:
        2px;

    border-radius:
        99px;

    background:
        linear-gradient(
            90deg,
            var(--uf-blue),
            var(--uf-teal)
        );
}


.uf-title {
    position:
        relative;

    z-index:
        2;

    color:
        var(--uf-navy);

    font-size:
        clamp(2rem, 3vw, 2.85rem);

    line-height:
        1.03;

    font-weight:
        820;

    letter-spacing:
        -0.055em;

    margin:
        0;

    max-width:
        850px;
}


.uf-subtitle {
    position:
        relative;

    z-index:
        2;

    color:
        var(--uf-slate-600);

    font-size:
        0.93rem;

    line-height:
        1.65;

    margin-top:
        0.7rem;

    margin-bottom:
        1rem;

    max-width:
        870px;
}


.uf-meta {
    position:
        relative;

    z-index:
        2;

    display:
        flex;

    flex-wrap:
        wrap;

    gap:
        0.48rem;
}


.uf-pill {
    display:
        inline-flex;

    align-items:
        center;

    gap:
        0.35rem;

    background:
        rgba(255, 255, 255, 0.82);

    color:
        var(--uf-slate-700);

    border:
        1px solid #D8E5F2;

    border-radius:
        999px;

    padding:
        0.38rem 0.72rem;

    font-size:
        0.73rem;

    font-weight:
        680;

    box-shadow:
        0 2px 8px rgba(15,23,42,0.025);
}


/* ---------------------------------------------------------
   SECTION HEADERS
   --------------------------------------------------------- */

.uf-section {
    position:
        relative;

    margin-top:
        2.55rem;

    margin-bottom:
        1rem;

    padding-left:
        0.95rem;
}


.uf-section::before {
    content:
        "";

    position:
        absolute;

    left:
        0;

    top:
        0.14rem;

    bottom:
        0.08rem;

    width:
        3px;

    border-radius:
        99px;

    background:
        linear-gradient(
            180deg,
            var(--uf-blue),
            var(--uf-teal)
        );
}


.uf-section-index {
    color:
        var(--uf-blue);

    font-size:
        0.67rem;

    font-weight:
        850;

    letter-spacing:
        0.13em;

    text-transform:
        uppercase;

    margin-bottom:
        0.16rem;
}


.uf-section-title {
    color:
        var(--uf-navy);

    font-size:
        1.45rem;

    line-height:
        1.15;

    font-weight:
        780;

    letter-spacing:
        -0.035em;

    margin:
        0;
}


.uf-section-caption {
    color:
        var(--uf-slate-500);

    font-size:
        0.83rem;

    line-height:
        1.55;

    margin-top:
        0.28rem;

    max-width:
        780px;
}


/* ---------------------------------------------------------
   SIDEBAR STATUS
   --------------------------------------------------------- */

.uf-sidebar-heading {
    color:
        var(--uf-slate-500);

    font-size:
        0.65rem;

    font-weight:
        850;

    letter-spacing:
        0.12em;

    text-transform:
        uppercase;

    margin-top:
        1rem;

    margin-bottom:
        0.48rem;
}


.uf-status,
.uf-health {
    padding:
        0.9rem 0.95rem;

    border-radius:
        14px;

    border:
        1px solid #D8E4F0;

    background:
        rgba(255,255,255,0.84);

    box-shadow:
        0 5px 17px rgba(15,23,42,0.035);
}


.uf-status {
    margin-bottom:
        0.85rem;
}


.uf-status-label {
    color:
        var(--uf-slate-500);

    font-size:
        0.64rem;

    font-weight:
        850;

    letter-spacing:
        0.10em;

    text-transform:
        uppercase;
}


.uf-status-value {
    color:
        var(--uf-navy);

    font-size:
        0.9rem;

    font-weight:
        760;

    margin-top:
        0.32rem;
}


.uf-status-refresh {
    color:
        var(--uf-slate-500);

    font-size:
        0.7rem;

    margin-top:
        0.34rem;
}


/* ---------------------------------------------------------
   HEALTH
   --------------------------------------------------------- */

.uf-health {
    margin-bottom:
        1rem;
}


.uf-health-head {
    display:
        flex;

    align-items:
        center;

    gap:
        0.4rem;

    color:
        var(--uf-navy);

    font-size:
        0.8rem;

    font-weight:
        760;

    margin-bottom:
        0.62rem;
}


.uf-health-row {
    display:
        flex;

    justify-content:
        space-between;

    gap:
        0.6rem;

    color:
        var(--uf-slate-500);

    font-size:
        0.69rem;

    padding:
        0.3rem 0;

    border-bottom:
        1px solid var(--uf-border-soft);
}


.uf-health-row:last-child {
    border-bottom:
        none;
}


.uf-health-row strong {
    color:
        var(--uf-slate-700);

    font-weight:
        720;
}


/* ---------------------------------------------------------
   INSIGHTS
   --------------------------------------------------------- */

.uf-insight {
    position:
        relative;

    display:
        flex;

    gap:
        0.85rem;

    min-height:
        126px;

    padding:
        1rem 1.05rem;

    border-radius:
        17px;

    border:
        1px solid var(--uf-border);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.98),
            rgba(249,252,255,0.94)
        );

    box-shadow:
        0 7px 22px rgba(15,23,42,0.04);

    overflow:
        hidden;
}


.uf-insight::before {
    content:
        "";

    position:
        absolute;

    left:
        0;

    top:
        0;

    bottom:
        0;

    width:
        3px;

    background:
        var(--uf-accent);
}


.uf-insight-icon {
    width:
        35px;

    height:
        35px;

    flex:
        0 0 35px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        11px;

    background:
        #F1F5F9;

    font-size:
        1rem;
}


.uf-insight-title {
    color:
        var(--uf-navy);

    font-size:
        0.88rem;

    font-weight:
        770;

    margin-bottom:
        0.32rem;
}


.uf-insight-body {
    color:
        #526174;

    font-size:
        0.8rem;

    line-height:
        1.55;
}


/* ---------------------------------------------------------
   NOTES
   --------------------------------------------------------- */

.uf-note {
    padding:
        1rem 1.08rem;

    border-radius:
        16px;

    border:
        1px solid #DCE7F2;

    background:
        linear-gradient(
            120deg,
            rgba(255,255,255,0.98),
            #F4F9FE
        );

    box-shadow:
        0 5px 18px rgba(15,23,42,0.03);
}


.uf-note-title {
    color:
        var(--uf-navy);

    font-weight:
        760;

    font-size:
        0.87rem;

    margin-bottom:
        0.28rem;
}


.uf-note-body {
    color:
        #526174;

    font-size:
        0.79rem;

    line-height:
        1.58;
}


/* ---------------------------------------------------------
   FOOTER
   --------------------------------------------------------- */

.uf-footer {
    display:
        flex;

    justify-content:
        space-between;

    align-items:
        center;

    flex-wrap:
        wrap;

    gap:
        0.8rem;

    margin-top:
        3.2rem;

    padding-top:
        1rem;

    border-top:
        1px solid var(--uf-border);

    color:
        var(--uf-slate-400);

    font-size:
        0.7rem;
}


.uf-footer strong {
    color:
        var(--uf-slate-600);

    font-weight:
        720;
}


/* ---------------------------------------------------------
   STREAMLIT DETAILS
   --------------------------------------------------------- */

hr {
    border-color:
        var(--uf-border) !important;
}


.modebar,
.modebar-container {
    display:
        none !important;
}


/* ---------------------------------------------------------
   RESPONSIVE
   --------------------------------------------------------- */

@media (max-width: 900px) {
    .block-container {
        padding-top:
            1.4rem;
    }

    .uf-hero {
        padding:
            1.3rem 1.3rem;
    }

    .uf-title {
        font-size:
            2rem;
    }

    .uf-section {
        margin-top:
            2rem;
    }

    [data-testid="stMetric"] {
        min-height:
            112px;
    }
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

    safe_icon = html.escape(
        icon
    )

    content = (
        '<div class="uf-hero">'
        '<div class="uf-eyebrow">'
        'UrbanFlow · Mobility Intelligence'
        '</div>'
        '<div class="uf-title">'
        f'{safe_title} {safe_icon}'
        '</div>'
        '<div class="uf-subtitle">'
        f'{safe_subtitle}'
        '</div>'
        '<div class="uf-meta">'
        '<span class="uf-pill">'
        f'📅 {safe_period}'
        '</span>'
        '<span class="uf-pill">'
        f'↻ Updated {safe_refresh}'
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
    *,
    index: str | None = None,
) -> None:
    safe_title = html.escape(
        title
    )

    content = (
        '<div class="uf-section">'
    )

    if index is not None:
        safe_index = html.escape(
            index
        )

        content += (
            '<div class="uf-section-index">'
            f'{safe_index}'
            '</div>'
        )

    content += (
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

    content += (
        '</div>'
    )

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
        f'Last refresh · {safe_refresh}'
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

    overall_label = (
        "Pipeline healthy"
        if overall_ok
        else "Check pipeline"
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
        f'{overall_icon} {overall_label}'
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


def page_footer(
    *,
    period: str,
) -> None:
    safe_period = html.escape(
        period
    )

    content = (
        '<div class="uf-footer">'
        '<span>'
        '<strong>UrbanFlow</strong> · '
        'Mobility Intelligence'
        '</span>'
        '<span>'
        f'{safe_period} · Citi Bike + Open-Meteo'
        '</span>'
        '</div>'
    )

    st.html(
        content
    )