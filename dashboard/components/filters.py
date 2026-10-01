from datetime import date

import streamlit as st


def render_trip_filters(
    min_date: date,
    max_date: date,
) -> dict:
    st.sidebar.header("Filters")

    rider_label = st.sidebar.selectbox(
        "Rider Type",
        options=[
            "All riders",
            "Member",
            "Casual",
        ],
    )

    bike_label = st.sidebar.selectbox(
        "Bike Type",
        options=[
            "All bikes",
            "Electric bike",
            "Classic bike",
        ],
    )

    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
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
