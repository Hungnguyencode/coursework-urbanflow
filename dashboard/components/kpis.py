import streamlit as st


def metric_row(
    metrics: list[tuple[str, str]],
) -> None:
    columns = st.columns(
        len(metrics)
    )

    for column, (
        label,
        value,
    ) in zip(
        columns,
        metrics,
        strict=True,
    ):
        with column:
            st.metric(
                label,
                value,
            )