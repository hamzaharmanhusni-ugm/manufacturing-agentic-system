"""Plotly in the Dispatch Manifest grammar: navy ink, ruled axes, cyan/blue series. Registered once as the default template."""
import plotly.graph_objects as go
import plotly.io as pio

PALETTE = {
    "Completed": "#0b1b33", "Running": "#0891b2", "Waiting for response": "#b45309", "Requires human approval": "#5b21b6",
    "Failed": "#b91c1c", "Idle": "#9aa8bb", "PCC": "#0891b2", "OPC": "#0b1b33", "threshold": "#b91c1c", "baseline": "#c9d2de",
    "series": ["#0b1b33", "#0891b2", "#1d4ed8", "#b45309", "#5b21b6", "#5c6b82", "#15803d", "#be185d", "#0e7490"],
    "text": "#0b1b33", "muted": "#5c6b82", "grid": "#e3e8ef", "axis": "#0b1b33",
}
FONT = "Archivo, sans-serif"


def register():
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=FONT, size=12, color=PALETTE["text"]),
        title=dict(font=dict(size=13, color=PALETTE["text"], weight=700), x=0, xanchor="left", y=0.98, yanchor="top"),
        colorway=PALETTE["series"], paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, font=dict(size=11, color=PALETTE["muted"]),
                    title_text="", bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#0b1b33", font=dict(family=FONT, size=12, color="#ffffff"), bordercolor="#0b1b33"),
        xaxis=dict(showgrid=False, linecolor=PALETTE["axis"], linewidth=1, ticks="outside", tickcolor=PALETTE["axis"], ticklen=4,
                   tickfont=dict(size=11, color=PALETTE["muted"]), title_font=dict(size=11, color=PALETTE["muted"]), zeroline=False),
        yaxis=dict(gridcolor=PALETTE["grid"], linecolor="rgba(0,0,0,0)", tickfont=dict(size=11, color=PALETTE["muted"]),
                   title_font=dict(size=11, color=PALETTE["muted"]), zeroline=False),
        bargap=0.3, bargroupgap=0.05, height=320,
    )
    t.data.bar = [go.Bar(marker=dict(line=dict(width=0)))]
    pio.templates["manifest"] = t
    pio.templates.default = "plotly_white+manifest"


def apply(fig, height=None):
    if height:
        fig.update_layout(height=height)
    return fig
