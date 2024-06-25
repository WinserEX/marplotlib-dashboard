from dash import Dash, html, dcc, Input, Output  # pip install dash
import plotly.express as px
import dash_ag_grid as dag                       # pip install dash-ag-grid
import dash_bootstrap_components as dbc          # pip install dash-bootstrap-components
import pandas as pd                              # pip install pandas

import matplotlib                                # pip install matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import base64
from io import BytesIO

# URL to the CSV file
iddoc2 = "1vsSJiu2uPe1enWTg03HqmPh3oHBlg2HIlPFFCxUiRyY"
gid2 = "87653910"
link2 = f"https://docs.google.com/spreadsheets/d/{iddoc2}/export?format=csv&{gid2}"

# Load the CSV file into a DataFrame
df = pd.read_csv(link2)

# Ensure NETO and TOTAL are numeric
df['NETO'] = pd.to_numeric(df['NETO'], errors='coerce').fillna(0).astype(int)
df['TOTAL'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0).astype(int)

# Group by DESC_PROD and aggregate the selected metric
def group_and_aggregate(df, column):
    grouped_df = df.groupby('DESC_PROD').sum().reset_index()
    return grouped_df

# Formatter function to convert numbers to human-readable format
def human_format(num, pos):
    if num >= 1e6:
        return f'{num*1e-6:.1f}M'
    elif num >= 1e3:
        return f'{num*1e-3:.1f}k'
    else:
        return f'{num:.1f}'

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = dbc.Container([
    html.H1("Interactive Matplotlib with Dash", className='mb-2', style={'textAlign':'center'}),

    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='category',
                value='TOTAL',
                clearable=False,
                options=[{'label': col, 'value': col} for col in df.columns[1:]]
            )
        ], width=4)
    ]),

    dbc.Row([
        dbc.Col([
            html.Img(id='bar-graph-matplotlib')
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-graph-plotly', figure={})
        ], width=12, md=6),
        dbc.Col([
            dag.AgGrid(
                id='grid',
                rowData=df.to_dict("records"),
                columnDefs=[{"field": i} for i in df.columns],
                columnSize="sizeToFit",
            )
        ], width=12, md=6),
    ], className='mt-10'),

])

# Create interactivity between dropdown component and graph
@app.callback(
    Output(component_id='bar-graph-matplotlib', component_property='src'),
    Output('bar-graph-plotly', 'figure'),
    Output('grid', 'defaultColDef'),
    Input('category', 'value'),
)
def plot_data(selected_yaxis):
    # Group and aggregate the data
    grouped_df = group_and_aggregate(df, selected_yaxis)
    
    # Debug: Print the aggregated data
    print(grouped_df[['DESC_PROD', selected_yaxis]].head())

    # Build the matplotlib figure
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(grouped_df['DESC_PROD'], grouped_df[selected_yaxis])
    ax.set_ylabel(selected_yaxis)
    ax.set_xticklabels(grouped_df['DESC_PROD'], rotation=30)
    ax.set_ylim(0, grouped_df[selected_yaxis].max() * 1.1)  # Ensure the Y-axis shows the full range of data

    # Apply the human-readable format to the Y-axis
    formatter = FuncFormatter(human_format)
    ax.yaxis.set_major_formatter(formatter)

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    fig_data = base64.b64encode(buf.getbuffer()).decode("ascii")
    fig_bar_matplotlib = f'data:image/png;base64,{fig_data}'

    # Build the Plotly figure
    fig_bar_plotly = px.bar(grouped_df, x='DESC_PROD', y=selected_yaxis)
    fig_bar_plotly.update_xaxes(tickangle=330)
    fig_bar_plotly.update_yaxes(range=[0, grouped_df[selected_yaxis].max() * 1.1])  # Ensure the Y-axis shows the full range of data

    my_cellStyle = {
        "styleConditions": [
            {
                "condition": f"params.colDef.field == '{selected_yaxis}'",
                "style": {"backgroundColor": "#d3d3d3"},
            },
            {   "condition": f"params.colDef.field != '{selected_yaxis}'",
                "style": {"color": "black"}
            },
        ]
    }

    return fig_bar_matplotlib, fig_bar_plotly, {'cellStyle': my_cellStyle}


if __name__ == '__main__':
    app.run_server(debug=False, port=8002)
