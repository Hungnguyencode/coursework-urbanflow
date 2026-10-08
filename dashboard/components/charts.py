import plotly.graph_objects as go

COLORWAY = [
    "#0B6BFF",
    "#13C8A3",
    "#FF9F1C",
    "#9A5CFF",
    "#FF5D6C",
    "#38BDF8",
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
            "family": "Inter, Segoe UI, Arial, sans-serif",
            "color": "#425A78",
            "size": 15,
        },
        title={
            "font": {
                "size": 20,
                "color": "#0B1F3A",
                "family": "Inter, Segoe UI, Arial, sans-serif",
            },
            "x": 0.025,
            "y": 0.96,
        },
        margin={
            "l": 34,
            "r": 28,
            "t": 58,
            "b": 30,
        },
        hoverlabel={
            "font_size": 14,
            "bgcolor": "#0B1F3A",
            "font_color": "#FFFFFF",
            "bordercolor": "#0B6BFF",
        },
        legend={
            "title": None,
            "orientation": "h",
            "y": 1.08,
            "x": 0,
            "font": {
                "color": "#5F7390",
                "size": 13,
            },
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
        linecolor="#DFEAF5",
        tickfont={
            "color": "#70839E",
            "size": 14,
        },
        title_font={
            "color": "#607590",
            "size": 14,
        },
        ticks="outside",
        tickcolor="#D7E5F2",
    )

    fig.update_yaxes(
        gridcolor="rgba(144, 168, 196, 0.18)",
        zeroline=False,
        linecolor="#DFEAF5",
        tickfont={
            "color": "#70839E",
            "size": 14,
        },
        title_font={
            "color": "#607590",
            "size": 14,
        },
        ticks="outside",
        tickcolor="#D7E5F2",
    )

    fig.update_coloraxes(
        colorbar_tickfont={
            "color": "#607590",
            "size": 13,
        },
        colorbar_title_font={
            "color": "#425A78",
            "size": 14,
        },
    )

    fig.for_each_annotation(
        lambda annotation: annotation.update(
            font={
                "size": 14,
                "color": "#425A78",
            }
        )
    )

    return fig

