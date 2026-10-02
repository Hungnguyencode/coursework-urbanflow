import plotly.graph_objects as go

COLORWAY = [
    "#0F6CBD",
    "#14B8A6",
    "#F59E0B",
    "#8B5CF6",
    "#EF4444",
]


def style_figure(
    fig: go.Figure,
    *,
    height: int | None = None,
) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLORWAY,
        font={
            "family": "Arial, sans-serif",
            "color": "#334155",
            "size": 13,
        },
        title={
            "font": {
                "size": 18,
                "color": "#0B1F33",
            },
            "x": 0.01,
        },
        margin={
            "l": 30,
            "r": 25,
            "t": 65,
            "b": 35,
        },
        hoverlabel={
            "font_size": 13,
            "bgcolor": "#0B1F33",
            "font_color": "#FFFFFF",
        },
        legend={
            "title": None,
            "orientation": "h",
            "y": 1.08,
            "x": 0,
        },
        hovermode="closest",
    )

    if height is not None:
        fig.update_layout(
            height=height,
        )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#E2E8F0",
        tickfont={
            "color": "#64748B",
        },
        title_font={
            "color": "#64748B",
        },
    )

    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.20)",
        zeroline=False,
        linecolor="#E2E8F0",
        tickfont={
            "color": "#64748B",
        },
        title_font={
            "color": "#64748B",
        },
    )

    return fig