import base64
import html
from functools import lru_cache
from pathlib import Path

import streamlit as st

BRAND_SVG_B64 = "CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB3aWR0aD0iMjUwIiBoZWlnaHQ9IjcyIiB2aWV3Qm94PSIwIDAgMjUwIDcyIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZyIgeDE9IjAiIHgyPSIxIiB5MT0iMCIgeTI9IjEiPgogICAgICA8c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiMwQjZCRkYiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIuNTIiIHN0b3AtY29sb3I9IiMxOUMzQzUiLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjODNFMDZCIi8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogIDwvZGVmcz4KICA8cmVjdCB4PSIyIiB5PSI3IiB3aWR0aD0iNDYiIGhlaWdodD0iNDYiIHJ4PSIxNSIgZmlsbD0idXJsKCNnKSIvPgogIDxwYXRoIGQ9Ik0xOSAxOSBMMzYgMjggTDE5IDM3IFoiIGZpbGw9IiNmZmYiIG9wYWNpdHk9Ii45NCIvPgogIDx0ZXh0IHg9IjU5IiB5PSIzMyIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjI1IiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjMEIxRjNBIj5VcmJhbkZsb3c8L3RleHQ+CiAgPHRleHQgeD0iNjAiIHk9IjUyIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iOC44IiBmb250LXdlaWdodD0iNzAwIiBsZXR0ZXItc3BhY2luZz0iMi44IiBmaWxsPSIjNzE4M0EwIj5NT0JJTElUWSBJTlRFTExJR0VOQ0U8L3RleHQ+Cjwvc3ZnPgo="

HERO_ASSET_BY_TITLE = {
    "UrbanFlow": "nyc_hero.webp",
    "Mobility Flow": "nyc_mobility.webp",
    "Temporal Patterns": "nyc_temporal.webp",
    "Weather Impact": "nyc_weather.webp",
}


GLOBAL_CSS = """
<style>
:root {
    --uf-navy: #0B1F3A;
    --uf-navy-2: #16385F;
    --uf-blue: #0B6BFF;
    --uf-blue-2: #3A8DFF;
    --uf-cyan: #31C8F3;
    --uf-teal: #13C8A3;
    --uf-mint: #E8FFF8;
    --uf-amber: #FF9F1C;
    --uf-violet: #9A5CFF;
    --uf-red: #FF5D6C;
    --uf-bg: #F7FBFF;
    --uf-card: rgba(255, 255, 255, 0.94);
    --uf-border: #DCEBFA;
    --uf-muted: #64748B;
    --uf-soft-blue: #EAF4FF;
    --uf-shadow: 0 18px 50px rgba(54, 93, 139, .10);
    --uf-shadow-soft: 0 10px 28px rgba(54, 93, 139, .08);
}

html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", Arial, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 82% 8%, rgba(49, 200, 243, .08), transparent 24rem),
        radial-gradient(circle at 42% 0%, rgba(19, 200, 163, .05), transparent 24rem),
        linear-gradient(180deg, #FFFFFF 0%, var(--uf-bg) 62%, #F6FAFF 100%);
    color: var(--uf-navy);
}

header[data-testid="stHeader"] {
    background: rgba(255, 255, 255, .82);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(220, 235, 250, .75);
}

.main .block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1510px;
    padding-top: 1.35rem;
    padding-bottom: 4rem;
}

[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 35px 30px, rgba(49, 200, 243, .11), transparent 115px),
        linear-gradient(180deg, #FBFDFF 0%, #F4F9FF 100%);
    border-right: 1px solid #DDE9F6;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: .15rem;
}

[data-testid="stSidebarNav"] {
    padding-top: 94px !important;
    background-image: url("data:image/svg+xml;base64,{BRAND_SVG_B64}");
    background-repeat: no-repeat;
    background-position: 24px 16px;
    background-size: 244px 70px;
}

[data-testid="stSidebarNav"] ul {
    gap: .34rem;
}

[data-testid="stSidebarNav"] li {
    margin: 0 .55rem;
}

[data-testid="stSidebarNav"] a {
    min-height: 48px;
    border-radius: 15px;
    padding: .72rem .85rem !important;
    font-size: .96rem;
    font-weight: 650;
    color: #425A78 !important;
    transition: all .18s ease;
}

[data-testid="stSidebarNav"] a:hover {
    color: var(--uf-blue) !important;
    background: rgba(11, 107, 255, .07) !important;
    transform: translateX(2px);
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    color: #0B2F62 !important;
    background:
        linear-gradient(90deg, rgba(46, 144, 255, .18), rgba(46, 144, 255, .06)) !important;
    box-shadow: inset 3px 0 0 #0B6BFF;
}

[data-testid="stSidebarNav"] li:nth-child(1) a::before,
[data-testid="stSidebarNav"] li:nth-child(2) a::before,
[data-testid="stSidebarNav"] li:nth-child(3) a::before,
[data-testid="stSidebarNav"] li:nth-child(4) a::before {
    display: inline-flex;
    width: 30px;
    margin-right: 8px;
    font-size: 1.12rem;
    color: var(--uf-blue);
}

[data-testid="stSidebarNav"] li:nth-child(1) a::before { content: "⌂"; }
[data-testid="stSidebarNav"] li:nth-child(2) a::before { content: "▥"; }
[data-testid="stSidebarNav"] li:nth-child(3) a::before { content: "◷"; }
[data-testid="stSidebarNav"] li:nth-child(4) a::before { content: "☁"; }

[data-testid="stSidebar"] hr {
    border-color: #D8E6F5;
    margin: 1.35rem .25rem;
}

.uf-hero {
    --uf-page-accent: var(--uf-blue);
    position: relative;
    min-height: 266px;
    overflow: hidden;
    border: 1px solid rgba(161, 210, 255, .52);
    border-radius: 28px;
    background:
        radial-gradient(circle at 50% 28%, rgba(255,255,255,.96), rgba(239,249,255,.72) 42%, rgba(224,247,247,.72) 100%);
    box-shadow: 0 22px 65px rgba(50, 100, 150, .13);
    margin-bottom: 1.2rem;
}

.uf-hero::before {
    content: "";
    position: absolute;
    width: 380px;
    height: 380px;
    border: 54px solid rgba(49, 200, 243, .18);
    border-radius: 50%;
    right: -80px;
    top: -250px;
    z-index: 1;
}

.uf-hero::after {
    content: "";
    position: absolute;
    width: 230px;
    height: 230px;
    border-radius: 50%;
    background: rgba(19, 200, 163, .11);
    right: 125px;
    bottom: -165px;
    z-index: 1;
}

.uf-hero-art {
    position: absolute;
    inset: 0 0 0 51%;
    background-size: cover;
    background-position: center;
    opacity: .98;
    z-index: 0;
}

.uf-hero-art::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, #EEF9FF 0%, rgba(238,249,255,.93) 12%, rgba(238,249,255,.48) 38%, rgba(238,249,255,0) 68%);
}

.uf-hero-content {
    position: relative;
    z-index: 3;
    width: 61%;
    padding: 30px 38px 28px 40px;
}

.uf-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 9px;
    text-transform: uppercase;
    letter-spacing: .20em;
    font-size: .72rem;
    font-weight: 800;
    color: var(--uf-blue);
}

.uf-eyebrow::before {
    content: "";
    width: 22px;
    height: 2px;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--uf-blue), var(--uf-teal));
}

.uf-title {
    display: flex;
    align-items: center;
    gap: 13px;
    color: var(--uf-navy);
    font-size: clamp(2.8rem, 4vw, 4.45rem);
    line-height: .98;
    font-weight: 850;
    letter-spacing: -.055em;
    margin: 5px 0 16px;
}

.uf-title .uf-title-accent {
    background: linear-gradient(118deg, #0B6BFF 0%, #186FF4 45%, #38BDF8 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.uf-title-icon {
    display: inline-flex;
    width: 58px;
    height: 58px;
    align-items: center;
    justify-content: center;
    border-radius: 18px;
    font-size: 2.1rem;
    background: rgba(255,255,255,.72);
    border: 1px solid rgba(150, 202, 255, .62);
    box-shadow: 0 10px 24px rgba(47, 128, 237, .13);
}

.uf-subtitle {
    max-width: 850px;
    color: #425A78;
    font-size: 1.04rem;
    line-height: 1.65;
    font-weight: 480;
}

.uf-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 18px;
}

.uf-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 13px;
    border-radius: 999px;
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(191, 216, 242, .88);
    color: #213A59;
    font-size: .80rem;
    font-weight: 700;
    box-shadow: 0 6px 17px rgba(66, 90, 120, .06);
}


.uf-viewbar {
    display: inline-flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 7px;
    min-height: 36px;
    margin: .15rem 0 .3rem;
    padding: 7px 12px;
    border-radius: 12px;
    color: #6C809C;
    background: rgba(255,255,255,.62);
    border: 1px solid rgba(218, 232, 246, .82);
    font-size: .77rem;
    font-weight: 620;
}

.uf-viewbar strong {
    color: #435D7D;
    font-size: .69rem;
    text-transform: uppercase;
    letter-spacing: .12em;
}

.uf-viewbar .uf-view-dot {
    color: #A9B8CA;
}

.uf-section {
    position: relative;
    padding: 9px 0 8px 20px;
    margin: 2.35rem 0 1.05rem;
}

.uf-section::before {
    content: "";
    position: absolute;
    left: 0;
    top: 7px;
    bottom: 7px;
    width: 4px;
    border-radius: 999px;
    background: linear-gradient(180deg, var(--uf-blue), var(--uf-teal));
    box-shadow: 0 0 0 5px rgba(11, 107, 255, .05);
}

.uf-section-index {
    color: var(--uf-blue);
    text-transform: uppercase;
    letter-spacing: .17em;
    font-size: .69rem;
    font-weight: 850;
    margin-bottom: 4px;
}

.uf-section-title {
    color: var(--uf-navy);
    font-weight: 820;
    font-size: 1.55rem;
    letter-spacing: -.025em;
}

.uf-section-caption {
    color: #657995;
    font-size: .90rem;
    margin-top: 4px;
    line-height: 1.5;
}


.uf-filter-heading {
    display: flex;
    align-items: center;
    gap: 11px;
    margin: 1.55rem .05rem .85rem;
    padding: 12px 13px;
    border-radius: 16px;
    border: 1px solid rgba(213, 230, 246, .90);
    background:
        radial-gradient(circle at 100% 0%, rgba(49, 200, 243, .10), transparent 72px),
        linear-gradient(135deg, rgba(255,255,255,.96), rgba(242,249,255,.86));
    box-shadow: 0 8px 22px rgba(66, 96, 132, .055);
}

.uf-filter-heading-icon {
    display: flex;
    flex: 0 0 auto;
    width: 35px;
    height: 35px;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    color: #FFFFFF;
    background: linear-gradient(135deg, var(--uf-blue), var(--uf-teal));
    box-shadow: 0 8px 18px rgba(11, 107, 255, .18);
    font-size: .98rem;
    font-weight: 800;
}

.uf-filter-heading-copy {
    min-width: 0;
}

.uf-filter-title {
    margin: 0;
    color: #17395F;
    font-size: 1.00rem;
    font-weight: 830;
    letter-spacing: -.02em;
    line-height: 1.15;
}

.uf-filter-sub {
    margin: 3px 0 0;
    color: #8A9AB1;
    font-size: .68rem;
    line-height: 1.25;
}

.uf-filter-summary {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: .35rem 0 .25rem;
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid #DCEAF7;
    background: linear-gradient(135deg, rgba(247,252,255,.96), rgba(236,250,247,.80));
    box-shadow: 0 6px 16px rgba(60, 92, 128, .045);
}

.uf-filter-summary-icon {
    display: inline-flex;
    width: 29px;
    height: 29px;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    color: #FFFFFF;
    background: linear-gradient(135deg, var(--uf-teal), #48D8B9);
    font-size: .76rem;
    font-weight: 900;
}

.uf-filter-summary-label {
    color: #8496AE;
    font-size: .61rem;
    font-weight: 780;
    text-transform: uppercase;
    letter-spacing: .09em;
}

.uf-filter-summary-value {
    color: #244567;
    font-size: .76rem;
    font-weight: 760;
    margin-top: 1px;
}

.uf-sidebar-heading {
    margin: 1.65rem .2rem .55rem;
    color: #5D7190;
    font-size: .67rem;
    text-transform: uppercase;
    letter-spacing: .18em;
    font-weight: 850;
}

.uf-status,
.uf-health {
    position: relative;
    overflow: hidden;
    border-radius: 18px;
    border: 1px solid #D8E7F6;
    background: rgba(255,255,255,.92);
    box-shadow: 0 10px 26px rgba(67, 99, 136, .07);
    padding: 16px 17px;
}

.uf-status::before {
    content: "";
    position: absolute;
    width: 105px;
    height: 105px;
    border-radius: 50%;
    background: rgba(49, 200, 243, .08);
    right: -48px;
    top: -55px;
}

.uf-status-label {
    position: relative;
    color: #7587A1;
    font-size: .67rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .12em;
}

.uf-status-value {
    position: relative;
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--uf-navy);
    font-weight: 800;
    font-size: 1.02rem;
    margin-top: 8px;
}

.uf-status-refresh {
    position: relative;
    color: #7487A3;
    font-size: .75rem;
    margin-top: 8px;
}

.uf-health-head {
    display: flex;
    align-items: center;
    gap: 7px;
    color: var(--uf-navy);
    font-size: .91rem;
    font-weight: 820;
    margin-bottom: 11px;
}

.uf-health-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 9px;
    color: #70819B;
    font-size: .75rem;
    padding: 8px 0;
    border-top: 1px solid #EEF4FA;
}

.uf-health-row strong {
    color: #183A64;
    font-size: .74rem;
}

.uf-insight {
    --uf-accent: var(--uf-blue);
    position: relative;
    display: flex;
    gap: 13px;
    min-height: 112px;
    border-radius: 20px;
    border: 1px solid #DDEAF7;
    background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(248,252,255,.93));
    box-shadow: var(--uf-shadow-soft);
    padding: 17px 17px 17px 19px;
    overflow: hidden;
}

.uf-insight::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--uf-accent);
}

.uf-insight::after {
    content: "";
    position: absolute;
    width: 92px;
    height: 92px;
    border-radius: 50%;
    right: -35px;
    top: -40px;
    background: rgba(11, 107, 255, .045);
}

.uf-insight-icon {
    flex: 0 0 auto;
    display: flex;
    width: 39px;
    height: 39px;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    background: #F2F7FD;
    border: 1px solid #E5EEF8;
    font-size: 1.08rem;
}

.uf-insight-content {
    position: relative;
    z-index: 1;
}

.uf-insight-title {
    color: var(--uf-navy);
    font-size: .91rem;
    font-weight: 820;
    margin: 2px 0 7px;
}

.uf-insight-body {
    color: #61738D;
    font-size: .80rem;
    line-height: 1.55;
}

.uf-note {
    border: 1px solid #D8E9F8;
    border-radius: 18px;
    background:
        linear-gradient(135deg, rgba(255,255,255,.95), rgba(236,248,255,.72));
    box-shadow: 0 10px 25px rgba(67, 99, 136, .06);
    padding: 17px 19px;
}

.uf-note-title {
    color: #13385F;
    font-size: .88rem;
    font-weight: 820;
    margin-bottom: 7px;
}

.uf-note-body {
    color: #5D718E;
    line-height: 1.55;
    font-size: .80rem;
}

.uf-footer {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    color: #8A9AB1;
    border-top: 1px solid #DDE8F4;
    margin-top: 3.2rem;
    padding: 18px 1px 5px;
    font-size: .70rem;
}

.uf-footer strong {
    color: #385574;
}

.uf-kpi {
    --uf-kpi-accent: var(--uf-blue);
    --uf-kpi-tint: #EEF7FF;
    position: relative;
    overflow: hidden;
    min-height: 146px;
    border: 1px solid #DDEAF6;
    border-radius: 21px;
    background:
        radial-gradient(circle at 95% 4%, rgba(11, 107, 255, .08) 0 52px, transparent 53px),
        linear-gradient(135deg, rgba(255,255,255,.98), var(--uf-kpi-tint));
    box-shadow: 0 15px 36px rgba(59, 92, 128, .08);
    padding: 18px 19px 16px;
    transition: transform .16s ease, box-shadow .16s ease;
}

.uf-kpi:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 42px rgba(59, 92, 128, .12);
}

.uf-kpi-head {
    display: flex;
    align-items: center;
    gap: 11px;
    min-height: 38px;
}

.uf-kpi-icon {
    display: flex;
    width: 38px;
    height: 38px;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: #FFFFFF;
    background: var(--uf-kpi-accent);
    box-shadow: 0 8px 20px rgba(11, 107, 255, .16);
    font-size: 1.03rem;
}

.uf-kpi-label {
    color: #233D61;
    font-weight: 720;
    font-size: .83rem;
}

.uf-kpi-value {
    color: #0B2443;
    font-size: 2.02rem;
    line-height: 1.08;
    font-weight: 850;
    letter-spacing: -.035em;
    margin-top: 9px;
}

.uf-kpi-sub {
    color: #7B8EA8;
    font-size: .69rem;
    margin-top: 7px;
}

div[data-testid="stPlotlyChart"] {
    border: 1px solid #DCE9F6;
    border-radius: 22px;
    background: rgba(255,255,255,.96);
    box-shadow: 0 14px 36px rgba(68, 98, 131, .07);
    padding: 4px 6px 2px;
    overflow: hidden;
}

div[data-testid="stPlotlyChart"]:hover {
    box-shadow: 0 18px 42px rgba(68, 98, 131, .10);
}

[data-testid="stDeckGlJsonChart"],
[data-testid="stPydeckChart"] {
    border: 1px solid #DCE9F6;
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 14px 36px rgba(68, 98, 131, .08);
}

[data-testid="stCaptionContainer"] {
    color: #7587A1;
    font-size: .79rem;
}

[data-testid="stDownloadButton"] button,
[data-testid="stBaseButton-primary"] {
    border: 0 !important;
    border-radius: 13px !important;
    background: linear-gradient(135deg, #0B6BFF, #2485FF) !important;
    color: white !important;
    font-weight: 760 !important;
    box-shadow: 0 9px 22px rgba(11, 107, 255, .22) !important;
}

[data-testid="stDownloadButton"] button:hover,
[data-testid="stBaseButton-primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 26px rgba(11, 107, 255, .28) !important;
}

[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    border-color: #D5E5F4 !important;
    border-radius: 12px !important;
    background: rgba(255,255,255,.94) !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"],
[data-testid="stSidebar"] [data-testid="stDateInput"] {
    margin-bottom: .45rem;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div {
    min-height: 45px !important;
    border: 1px solid #D7E7F5 !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #FFFFFF, #F8FCFF) !important;
    box-shadow: 0 7px 18px rgba(60, 92, 128, .055) !important;
    transition: border-color .16s ease, box-shadow .16s ease, transform .16s ease;
}

[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
    border-color: #A9D1F8 !important;
    box-shadow: 0 9px 20px rgba(42, 118, 198, .08) !important;
}

[data-testid="stSidebar"] [data-testid="stSelectbox"]:focus-within [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-testid="stDateInput"]:focus-within [data-baseweb="input"] {
    border-color: #78B8F7 !important;
    box-shadow: 0 0 0 3px rgba(11, 107, 255, .08), 0 9px 20px rgba(42, 118, 198, .08) !important;
}

[data-testid="stSidebar"] [data-baseweb="select"] svg {
    color: var(--uf-blue) !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] {
    min-height: 45px !important;
    border: 1px solid #D7E7F5 !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #FFFFFF, #F8FCFF) !important;
    box-shadow: 0 7px 18px rgba(60, 92, 128, .055) !important;
    overflow: hidden;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    min-height: 43px !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #244567 !important;
    font-weight: 650 !important;
    font-size: .78rem !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] [data-testid="stDateInput"] button {
    color: var(--uf-blue) !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #17395F;
    font-weight: 780;
}

[data-testid="stSidebar"] label {
    color: #385775 !important;
    font-size: .76rem !important;
    font-weight: 720 !important;
    letter-spacing: .005em;
}

[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    margin-bottom: .30rem;
}

[data-testid="stSidebar"] [data-testid="stSlider"] {
    margin-bottom: .38rem;
    padding: .08rem .12rem .18rem;
}

[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"] {
    background: var(--uf-blue) !important;
    border: 3px solid #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(11, 107, 255, .25) !important;
}

[data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"]:focus {
    box-shadow: 0 0 0 4px rgba(11, 107, 255, .12), 0 2px 8px rgba(11, 107, 255, .25) !important;
}

.uf-flow-filter-summary {
    margin: .55rem 0 .35rem;
    padding: 10px 12px;
    border: 1px solid #DCEAF8;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(239,248,255,.92));
    box-shadow: 0 7px 18px rgba(60, 92, 128, .045);
}

.uf-flow-filter-summary-title {
    margin-bottom: 4px;
    color: #8193AA;
    font-size: .61rem;
    font-weight: 800;
    letter-spacing: .10em;
    text-transform: uppercase;
}

.uf-flow-filter-summary-value {
    color: #244567;
    font-size: .72rem;
    font-weight: 690;
    line-height: 1.45;
}

[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

@media (max-width: 1180px) {
    .uf-hero-art {
        inset: 0 0 0 57%;
        opacity: .80;
    }

    .uf-hero-content {
        width: 68%;
    }

    .uf-title {
        font-size: 3.2rem;
    }
}

@media (max-width: 900px) {
    .uf-hero {
        min-height: 280px;
    }

    .uf-hero-art {
        inset: 0;
        opacity: .20;
    }

    .uf-hero-art::before {
        background: linear-gradient(90deg, rgba(239,249,255,.98), rgba(239,249,255,.78));
    }

    .uf-hero-content {
        width: 100%;
        padding: 28px 25px;
    }

    .uf-title {
        font-size: 2.7rem;
    }

    .uf-footer {
        flex-direction: column;
    }
}
</style>
""".replace("{BRAND_SVG_B64}", BRAND_SVG_B64)


def inject_global_css() -> None:
    st.html(GLOBAL_CSS)


@lru_cache(maxsize=8)
def _asset_data_uri(filename: str) -> str | None:
    asset_path = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / filename
    )

    if not asset_path.exists():
        return None

    mime = "image/webp"
    if asset_path.suffix.lower() == ".png":
        mime = "image/png"
    elif asset_path.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"

    encoded = base64.b64encode(
        asset_path.read_bytes()
    ).decode("ascii")

    return f"data:{mime};base64,{encoded}"


def _split_title(title: str) -> tuple[str, str]:
    if title == "UrbanFlow":
        return "Urban", "Flow"

    if " " in title:
        leading, accent = title.rsplit(" ", 1)
        return f"{leading} ", accent

    return "", title


def page_header(
    *,
    title: str,
    icon: str,
    subtitle: str,
    period: str,
    last_refresh: str,
) -> None:
    leading, accent = _split_title(title)

    safe_leading = html.escape(leading)
    safe_accent = html.escape(accent)
    safe_subtitle = html.escape(subtitle)
    safe_period = html.escape(period)
    safe_refresh = html.escape(last_refresh)
    safe_icon = html.escape(icon)

    hero_uri = _asset_data_uri(
        HERO_ASSET_BY_TITLE.get(
            title,
            "nyc_hero.webp",
        )
    )

    hero_art = ""
    if hero_uri is not None:
        safe_uri = html.escape(
            hero_uri,
            quote=True,
        )
        hero_art = (
            '<div class="uf-hero-art" '
            f'style="background-image:url(\'{safe_uri}\');">'
            '</div>'
        )

    content = (
        '<div class="uf-hero">'
        f'{hero_art}'
        '<div class="uf-hero-content">'
        '<div class="uf-eyebrow">'
        'UrbanFlow · Mobility Intelligence'
        '</div>'
        '<div class="uf-title">'
        '<span>'
        f'{safe_leading}'
        '<span class="uf-title-accent">'
        f'{safe_accent}'
        '</span>'
        '</span>'
        '<span class="uf-title-icon">'
        f'{safe_icon}'
        '</span>'
        '</div>'
        '<div class="uf-subtitle">'
        f'{safe_subtitle}'
        '</div>'
        '<div class="uf-meta">'
        '<span class="uf-pill">'
        f'📅 {safe_period}'
        '</span>'
        '<span class="uf-pill">'
        f'⟳ Updated {safe_refresh}'
        '</span>'
        '<span class="uf-pill">'
        '🚲 Citi Bike + Open-Meteo'
        '</span>'
        '</div>'
        '</div>'
        '</div>'
    )

    st.html(content)



def view_context(text: str) -> None:
    safe_text = html.escape(text)
    parts = [
        part.strip()
        for part in safe_text.split(" · ")
    ]

    content = (
        '<div class="uf-viewbar">'
        '<strong>✦ Current view</strong>'
    )

    for part in parts:
        content += (
            '<span class="uf-view-dot">·</span>'
            '<span>'
            f'{part}'
            '</span>'
        )

    content += '</div>'
    st.html(content)


def section_header(
    title: str,
    caption: str | None = None,
    *,
    index: str | None = None,
) -> None:
    safe_title = html.escape(title)

    content = '<div class="uf-section">'

    if index is not None:
        safe_index = html.escape(index)
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
        safe_caption = html.escape(caption)
        content += (
            '<div class="uf-section-caption">'
            f'{safe_caption}'
            '</div>'
        )

    content += '</div>'
    st.html(content)


def sidebar_filter_heading(
    title: str,
    subtitle: str,
    *,
    icon: str = "⚙",
) -> None:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_icon = html.escape(icon)

    with st.sidebar:
        st.html(
            '<div class="uf-filter-heading">'
            '<div class="uf-filter-heading-icon">'
            f'{safe_icon}'
            '</div>'
            '<div class="uf-filter-heading-copy">'
            '<div class="uf-filter-title">'
            f'{safe_title}'
            '</div>'
            '<div class="uf-filter-sub">'
            f'{safe_subtitle}'
            '</div>'
            '</div>'
            '</div>'
        )


def sidebar_filter_summary(text: str) -> None:
    safe_text = html.escape(text)

    with st.sidebar:
        st.html(
            '<div class="uf-flow-filter-summary">'
            '<div class="uf-flow-filter-summary-title">Active flow view</div>'
            '<div class="uf-flow-filter-summary-value">'
            f'{safe_text}'
            '</div>'
            '</div>'
        )


def sidebar_data_status(
    *,
    period: str,
    last_refresh: str,
) -> None:
    safe_period = html.escape(period)
    safe_refresh = html.escape(last_refresh)

    content = (
        '<div class="uf-sidebar-heading">'
        'Data Status'
        '</div>'
        '<div class="uf-status">'
        '<div class="uf-status-label">'
        'Active dataset'
        '</div>'
        '<div class="uf-status-value">'
        '🟢 '
        f'{safe_period}'
        '</div>'
        '<div class="uf-status-refresh">'
        '⟳ Last refresh · '
        f'{safe_refresh}'
        '</div>'
        '</div>'
    )

    with st.sidebar:
        st.html(content)


def insight_card(
    *,
    title: str,
    body: str,
    icon: str = "💡",
    accent: str = "#0B6BFF",
) -> None:
    safe_title = html.escape(title)
    safe_body = html.escape(body)
    safe_icon = html.escape(icon)
    safe_accent = html.escape(accent)

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

    st.html(content)


def note_card(
    *,
    title: str,
    body: str,
) -> None:
    safe_title = html.escape(title)
    safe_body = html.escape(body)

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

    st.html(content)


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

    weather_ok = weather_rows == expected_hours
    join_ok = joined_rows == expected_hours
    database_ok = object_count >= 7
    overall_ok = (
        weather_ok
        and join_ok
        and database_ok
    )

    overall_icon = "🟢" if overall_ok else "🟠"
    overall_label = (
        "Pipeline healthy"
        if overall_ok
        else "Check pipeline"
    )

    weather_icon = "✓" if weather_ok else "!"
    join_icon = "✓" if join_ok else "!"
    database_icon = "✓" if database_ok else "!"

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
        st.html(content)


def page_footer(
    *,
    period: str,
) -> None:
    safe_period = html.escape(period)

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

    st.html(content)
