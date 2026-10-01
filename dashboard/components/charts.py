import plotly.graph_objects as go


def style_figure(
    fig: go.Figure,
    *,
    height: int | None = None,
) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        margin={
            "l": 20,
            "r": 20,
            "t": 60,
            "b": 20,
        },
        hoverlabel={
            "font_size": 13,
        },
        legend={
            "title": None,
        },
    )

    if height is not None:
        fig.update_layout(
            height=height,
        )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
    )

    fig.update_yaxes(
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    )

    return fig