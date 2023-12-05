import dash
import dash_bootstrap_components as dbc
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import shapely.geometry
from dash import dcc, html
from dash.dependencies import Input, Output

df = pd.read_pickle("../data/quakes_last_24.pkl")
geo_df = gpd.read_file("../data/GeoJSON/PB2002_boundaries.json")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "Earthquakes over the Last 24 Hours",
                        className="text-center mb-4",
                    ),
                    width=12,
                    style={"padding": "5px"},
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Container(
                        [
                            html.H2("World View", className="text-center mb-3"),
                            dcc.Graph(
                                id="map",
                                style={"height": "500"},
                                clickData={"points": []},
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Magnitude Range"),
                                            dcc.RangeSlider(
                                                id="mag-slider",
                                                min=2.5,
                                                max=9.0,
                                                step=0.1,
                                                value=[2.5, 9.0],
                                                marks={
                                                    i: {
                                                        "label": str(i),
                                                        "style": {
                                                            "font-size": "12px",
                                                        },
                                                    }
                                                    for i in range(3, 10)
                                                },
                                                included=True,
                                            ),
                                        ],
                                        className="mt-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.RadioItems(
                                                id="tsunami-filter",
                                                options=[
                                                    {"label": "All", "value": "all"},
                                                    {
                                                        "label": "Tsunami Warning Issued",
                                                        "value": "yes",
                                                    },
                                                    {
                                                        "label": "No Tsunami Warning",
                                                        "value": "no",
                                                    },
                                                ],
                                                value="all",
                                                inline=True,
                                            ),
                                        ],
                                        className="mt-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Checklist(
                                                id="boundary-toggle",
                                                options=[
                                                    {"label": "Show Major Fault Lines", "value": "show"},
                                                ],
                                                value=["show"],
                                                inline=True,
                                            ),
                                        ],
                                        className="mt-3",
                                    ),
                                ], style={"background-color": "#ededed"}
                            ),
                        ]
                    ),
                    width=8,
                ),
                dbc.Col(
                    dbc.Container(
                        [
                            html.H2(
                                "Today's Earthquakes Sorted By",
                                className="text-center mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.RadioItems(
                                                id="sort-by",
                                                options=[
                                                    {
                                                        "label": "Magnitude",
                                                        "value": "mag",
                                                    },
                                                    {
                                                        "label": "Time",
                                                        "value": "datetime",
                                                    },
                                                    {
                                                        "label": "Depth",
                                                        "value": "depth",
                                                    },
                                                ],
                                                value="datetime",
                                                inline=True,
                                            ),
                                        ],
                                        width=6,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.RadioItems(
                                                id="sort-order",
                                                options=[
                                                    {
                                                        "label": "Ascending",
                                                        "value": "asc",
                                                    },
                                                    {
                                                        "label": "Descending",
                                                        "value": "desc",
                                                    },
                                                ],
                                                value="desc",
                                                inline=True,
                                            ),
                                        ],
                                        width=6,
                                    ),
                                ]
                            ),
                            dbc.ListGroup(
                                id="quake-details",
                                style={
                                    "overflow": "auto",
                                    "max-height": "500px",
                                    "padding": "20px",
                                    "padding-top": "10px",
                                    "background-color": "white",
                                },
                            ),
                        ]
                    ),
                    width=4,
                ),
            ],
            className="mt-2",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="depth-histogram", style={"padding": "20px"}),
                    width=6,
                ),
                dbc.Col(
                    dcc.Graph(id="magnitude-histogram", style={"padding": "20px"}),
                    width=6,
                ),
            ],
            className="mt-2",
        ),
    ],
    fluid=True,
    style={"backgroundColor": "#F6F6F6"},
)


@app.callback(
    Output("map", "figure"),
    [
        Input("mag-slider", "value"),
        Input("tsunami-filter", "value"),
        Input("boundary-toggle", "value"),
    ],
)
def update_map(mag_range, tsunami, boundary):
    filtered_df = df[(df["mag"] >= mag_range[0]) & (df["mag"] <= mag_range[1])]
    if tsunami != "all":
        filtered_df = filtered_df[
            filtered_df["tsunami warning"] == (1 if tsunami == "yes" else 0)
        ]

    fig = px.scatter_geo(
        filtered_df,
        lat="latitude",
        lon="longitude",
        size="mag",
        color="tsunami warning",
        opacity=0.3,
        color_discrete_map={True: "blue", False: "orange"},
        hover_name="place",
        projection="natural earth",
    )

    if "show" in boundary:
        lats = []
        lons = []
        names = []

        for feature, name in zip(geo_df.geometry, geo_df.LAYER):
            if isinstance(feature, shapely.geometry.linestring.LineString):
                linestrings = [feature]
            elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
                linestrings = feature.geoms
            else:
                continue
            for linestring in linestrings:
                x, y = linestring.xy
                lats = np.append(lats, y)
                lons = np.append(lons, x)
                names = np.append(names, [name]*len(y))
                lats = np.append(lats, None)
                lons = np.append(lons, None)
                names = np.append(names, None)

        fig.add_trace(go.Scattergeo(lat=lats, lon=lons, mode='lines', line=dict(width=1, color='black'), name='Major Faultlines'))

    fig.update_layout(
        showlegend=False,
        margin={"r": 0, "t": 10, "l": 0, "b": 10},
        geo=dict(
            center=dict(lat=0, lon=-150),
            projection_rotation=dict(lon=-150),
        ),
    )
    return fig


@app.callback(
    Output("quake-details", "children"),
    [
        Input("sort-by", "value"),
        Input("sort-order", "value"),
        Input("tsunami-filter", "value"),
        Input("mag-slider", "value"),
    ],
)
def update_quake_details(sort_by, sort_order, tsunami, mag_range):
    sorted_df = df.sort_values(sort_by, ascending=(sort_order == "asc"))
    sorted_df = sorted_df[
        (sorted_df["mag"] >= mag_range[0]) & (sorted_df["mag"] <= mag_range[1])
    ]

    if tsunami != "all":
        sorted_df = sorted_df[
            sorted_df["tsunami warning"] == (1 if tsunami == "yes" else 0)
        ]

    quake_details = []

    for _, row in sorted_df.iterrows():
        text_color = "blue" if row["tsunami warning"] else "black"
        description = f"M: {row['mag']} @ {row['place']}, {row['datetime']}, Depth: {row['depth']} km"
        quake_details.append(html.Li(description, style={"color": text_color}))

    return quake_details


@app.callback(
    [Output("depth-histogram", "figure"),
     Output("magnitude-histogram", "figure")],
    [Input("mag-slider", "value"), Input("tsunami-filter", "value")]
)
def update_histograms(mag_range, tsunami):
    filtered_df = df.copy()

    if tsunami != "all":
        filtered_df = filtered_df[
            filtered_df["tsunami warning"] == (1 if tsunami == "yes" else 0)
        ]

    depth_histogram = px.histogram(
        filtered_df,
        x="depth",
        nbins=20,
        title="Earthquakes by Depth(km)",
        labels={"depth": "Depth"},
        color_discrete_sequence=["green"],
        opacity=0.7,
    )
    depth_histogram.update_layout(
        xaxis_title="Depth (km)",
        yaxis_title="Count",
        bargap=0.05,
        margin=dict(l=0, r=0, t=30, b=0),
        title_x=0.5,
    )

    magnitude_histogram = px.histogram(
        filtered_df,
        x="mag",
        nbins=20,
        title="Earthquakes by Magnitude",
        labels={"mag": "Magnitude"},
        color_discrete_sequence=["blue"],
        opacity=0.7,
    )
    magnitude_histogram.update_layout(
        xaxis_title="Magnitude",
        yaxis_title="Count",
        bargap=0.05,
        margin=dict(l=0, r=0, t=30, b=0),
        title_x=0.5,
    )

    return depth_histogram, magnitude_histogram


if __name__ == "__main__":
    app.run_server(port=8010, debug=True)

