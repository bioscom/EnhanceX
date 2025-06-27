print("App is being loaded")

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from django_plotly_dash import DjangoDash
 
import plotly.graph_objects as go


# Sample Data
data = {
    "Lgate": ["L1", "L2", "L1", "L3", "L2", "L1", "L4", "L5", "L3", "L1"],
    "InitiativeId": [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    "ProjectName": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
}
df = pd.DataFrame(data)

# Count Initiatives per Lgate
counts_df = df.groupby("Lgate")["InitiativeId"].count().reset_index(name="Count")

# Create Dash App inside Django
app = DjangoDash("LgateDrilldown", external_scripts=["https://cdn.plot.ly/plotly-latest.min.js"]) # Load Plotly from a CDN) # Unique name



# # Sample Data (Replace with Your Database Query)
# df = pd.DataFrame({
#     "Workstream": ["L1", "L2", "L3", "L4", "L5"],
#     "Plan": [10000000, 15000000, 20000000, 25000000, 30000000],
#     "Forecast": [11000000, 14000000, 19000000, 24000000, 31000000],
#     "Actual": [12000000, 13000000, 18000000, 23000000, 32000000]
# })

# # Convert values to Millions
# def format_million(value):
#     return f"{value / 1e6:.1f}M"

# # Layout and Graph
# app.layout = html.Div(
#     children=[
#     dcc.Graph(
#         id="bar-chart",
#         figure={
#             "data": [
#                 go.Bar(x=df["Workstream"], y=df["Plan"], name="Plan", text=[format_million(v) for v in df["Plan"]], textposition="outside", marker_color="blue"),
#                 go.Bar(x=df["Workstream"], y=df["Forecast"], name="Forecast", text=[format_million(v) for v in df["Forecast"]], textposition="outside",  marker_color="orange"),
#                 go.Bar(x=df["Workstream"], y=df["Actual"], name="Actual", text=[format_million(v) for v in df["Actual"]], textposition="outside", marker_color="green"),
#             ],
#             "layout": go.Layout(title="Workstream Performance", xaxis_title="Workstream", yaxis_title="Values (in Millions)", barmode="group", height=600,
#                 legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
#                 ),
#             },
#             style={"width": "100%", "height": "100vh"}, # Stretch graph
#         )
#     ],
#     style={"width": "100vw", "height": "100vh", "overflow": "hidden"}, # Full screen
# )


app.layout = html.Div([
    dcc.Graph(id="bar-chart"),
    html.Div(id="table-container")
])

# Update Bar Chart
@app.callback(
    Output("bar-chart", "figure"),
    Input("bar-chart", "relayoutData") # Detect layout changes
)
def update_chart(_):
    fig = px.bar(counts_df, x="Lgate", y="Count", text="Count", title="Initiative Count per Lgate")
    fig.update_traces(textposition="outside") # Show values on bars
    return fig

# Drill-Down: Show Table on Click
@app.callback(
    Output("table-container", "children"),
    Input("bar-chart", "clickData")
)
def display_table(click_data):
    if not click_data:
        return "Click a bar to see details."

    clicked_workstream = click_data["points"][0]["x"]
    filtered_df = df[df["Lgate"] == clicked_workstream]

    return html.Table([
        html.Tr([html.Th(col) for col in filtered_df.columns])
    ] + [
        html.Tr([html.Td(filtered_df.iloc[i][col]) for col in filtered_df.columns]) for i in range(len(filtered_df))
    ])
