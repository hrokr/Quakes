import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

df = pd.read_pickle('../data/quakes_last_24.pkl')

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='map'),
    dcc.Slider(
        id='mag-slider',
        min=2.5,
        max=9,
        step=0.1,
        value=2.5,
    ),
    dcc.RadioItems(
        id='tsunami-filter',
        options=[{'label': 'All', 'value': 'all'},
                 {'label': 'Tsunami Warning Issued', 'value': 'yes'},
                 {'label': 'No Tsunami Warning', 'value': 'no'}],
        value='all',
    )
])


@app.callback(
    Output('map', 'figure'),
    [Input('mag-slider', 'value'),
     Input('tsunami-filter', 'value')])
def update_map(mag, tsunami):
    filtered_df = df[df['mag'] >= mag]
    
    if tsunami != 'all':
        filtered_df = filtered_df[filtered_df['tsunami'] == (1 if tsunami == 'yes' else 0)]
    
    fig = px.scatter_geo(filtered_df,
                         lat='latitude',
                         lon='longitude',
                         color='tsunami',
                         color_continuous_scale=['orange', 'blue'],
                         hover_name='place',
                         projection='natural earth')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
