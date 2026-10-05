from datetime import date

import streamlit as st


def render_trip_filters(
    min_date: date,
    max_date: date,
) -> dict:
    with st.sidebar:
        st.html(
            '<div class="uf-filter-heading">'
            '<div class="uf-filter-heading-icon">⚙</div>'
            '<div class="uf-filter-heading-copy">'
            '<div class="uf-filter-title">Filters</div>'
            '<div class="uf-filter-sub">Refine the active selection</div>'
            '</div>'
            '</div>'
        )

    rider_label = st.sidebar.selectbox(
        "👥  Rider Type",
        options=[
            "All riders",
            "Member",
            "Casual",
        ],
    )

    bike_label = st.sidebar.selectbox(
        "🚲  Bike Type",
        options=[
            "All bikes",
            "Electric bike",
            "Classic bike",
        ],
    )

    selected_dates = st.sidebar.date_input(
        "📅  Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="MM/DD/YYYY",
    )

    if isinstance(selected_dates, (tuple, list)):
        if len(selected_dates) == 2:
            start_date, end_date = selected_dates
        elif len(selected_dates) == 1:
            start_date = selected_dates[0]
            end_date = selected_dates[0]
        else:
            start_date = min_date
            end_date = max_date
    else:
        start_date = selected_dates
        end_date = selected_dates

    start_label = start_date.strftime("%b %d")
    end_label = end_date.strftime("%b %d, %Y")

    with st.sidebar:
        st.html(
            '<div class="uf-filter-summary">'
            '<span class="uf-filter-summary-icon">✓</span>'
            '<div>'
            '<div class="uf-filter-summary-label">Active window</div>'
            '<div class="uf-filter-summary-value">'
            f'{start_label} → {end_label}'
            '</div>'
            '</div>'
            '</div>'
        )

    rider_values = {
        "All riders": None,
        "Member": "member",
        "Casual": "casual",
    }

    bike_values = {
        "All bikes": None,
        "Electric bike": "electric_bike",
        "Classic bike": "classic_bike",
    }

    return {
        "rider_type": rider_values[rider_label],
        "bike_type": bike_values[bike_label],
        "rider_label": rider_label,
        "bike_label": bike_label,
        "start_date": start_date,
        "end_date": end_date,
    }
