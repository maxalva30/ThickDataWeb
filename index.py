from dash import dcc, html, Input, Output, State
import dash
import plotly.graph_objs as go
import pandas as pd
import plotly.io as pio  # Necesario para guardar el gráfico como HTML
from datetime import datetime  # Para nombrar el archivo con la fecha actual

# --------------
# NOTA IMPORTANTE
# --------------
# Usamos router manual en index.py, por lo que NO necesitamos la API de
# dash pages.  Quitamos dash.register_page para evitar el error
#   "dash.exceptions.PageError: dash.register_page() must be called after
#    app instantiation" cuando Render levanta gunicorn.

# ==========================
# Layout de la página /plots
# ==========================
layout = html.Div(
    className="main-container",
    children=[
        # ------------------------------
        # Barra de controles y opciones
        # ------------------------------
        html.Div(
            className="options-container",
            style={
                'display': 'flex',
                'justify-content': 'space-between',
                'align-items': 'center',
                'flex-wrap': 'wrap',
                'margin': '20px'
            },
            children=[
                # Variables primarias (eje y1)
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='primary-variable',
                            placeholder='Choose primary variables',
                            multi=True,
                            style={'width': '250px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),
                # Variables secundarias (eje y2)
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='secondary-variable',
                            placeholder='Choose secondary variables',
                            multi=True,
                            style={'width': '250px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),
                # Periodo de muestreo / resampleo
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='time-period',
                            options=[
                                {'label': '5 Minutes', 'value': '5T'},
                                {'label': '10 Minutes', 'value': '10T'},
                                {'label': '30 Minutes', 'value': '30T'},
                                {'label': '1 Hour', 'value': '1H'}
                            ],
                            placeholder='Choose time period',
                            style={'width': '200px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),

                # ---------------------------
                # Customer input – Línea #1
                # ---------------------------
                html.Div(
                    children=[
                        html.Label('Line 1', style={'margin-right': '6px'}),
                        dcc.Input(
                            id='line1-value',
                            type='number',
                            placeholder='Y value',
                            style={'width': '120px', 'margin-right': '6px'}
                        ),
                        dcc.Dropdown(
                            id='axis1-choice',
                            options=[
                                {'label': 'Primary', 'value': 'y1'},
                                {'label': 'Secondary', 'value': 'y2'}
                            ],
                            placeholder='Axis',
                            style={'width': '110px'}
                        )
                    ],
                    style={'display': 'flex', 'align-items': 'center', 'margin-right': '20px'}
                ),

                # ---------------------------
                # Customer input – Línea #2
                # ---------------------------
                html.Div(
                    children=[
                        html.Label('Line 2', style={'margin-right': '6px'}),
                        dcc.Input(
                            id='line2-value',
                            type='number',
                            placeholder='Y value',
                            style={'width': '120px', 'margin-right': '6px'}
                        ),
                        dcc.Dropdown(
                            id='axis2-choice',
                            options=[
                                {'label': 'Primary', 'value': 'y1'},
                                {'label': 'Secondary', 'value': 'y2'}
                            ],
                            placeholder='Axis',
                            style={'width': '110px'}
                        )
                    ],
                    style={'display': 'flex', 'align-items': 'center', 'margin-right': '20px'}
                ),

                # Botón para generar el gráfico
                html.Button('Plot graph', id='plot-button', className='btn btn-primary', style={'margin-right': '20px'})
            ]
        ),

        # ----------------
        # Contenedor gráfico
        # ----------------
        html.Div(
            className="graph-container",
            style={'width': '100%', 'display': 'flex', 'justify-content': 'center', 'position': 'relative'},
            children=[
                dcc.Graph(id='time-series-graph', className='time-series-graph', config={'displayModeBar': True}),
                dcc.Download(id="download-graph"),
                html.Button('Save', id='save-button', className='btn btn-secondary',
                            style={'position': 'absolute', 'bottom': '80px', 'right': '20px'})
            ]
        )
    ]
)

# ===============================================
# Callback principal: genera gráfico + dropdowns
# ===============================================
@dash.callback(
    [Output('primary-variable', 'options'),
     Output('secondary-variable', 'options'),
     Output('time-series-graph', 'figure')],
    Input('plot-button', 'n_clicks'),
    State('primary-variable', 'value'),
    State('secondary-variable', 'value'),
    State('time-period', 'value'),
    State('line1-value', 'value'),
    State('axis1-choice', 'value'),
    State('line2-value', 'value'),
    State('axis2-choice', 'value'),
    State('stored-data', 'data')
)
def update_graph(n_clicks, primary_vars, secondary_vars, time_period,
                 line1_val, axis1, line2_val, axis2, stored_data):
    if stored_data is None:
        return [], [], go.Figure()

    df = pd.DataFrame(stored_data)
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
    dropdown_options = [{'label': col, 'value': col} for col in df.columns[1:]]

    # Resampleo
    df_resampled = (df.set_index(df.columns[0])
                      .resample(time_period).mean().reset_index()) if time_period else df

    if n_clicks and primary_vars:
        fig = go.Figure()
        for var in primary_vars:
            fig.add_trace(go.Scatter(x=df_resampled.iloc[:, 0], y=df_resampled[var],
                                     mode='lines', name=var, yaxis='y1'))
        if secondary_vars:
            for var in secondary_vars:
                fig.add_trace(go.Scatter(x=df_resampled.iloc[:, 0], y=df_resampled[var],
                                         mode='lines', name=var, yaxis='y2'))
            fig.update_layout(yaxis2=dict(title='Secondary Y axis', overlaying='y', side='right'))

        def add_hline(value, axis, color):
            fig.add_shape(type='line', x0=df_resampled.iloc[0, 0], x1=df_resampled.iloc[-1, 0],
                          y0=value, y1=value, xref='x', yref=axis,
                          line=dict(color=color, dash='dash'))
            fig.add_annotation(x=df_resampled.iloc[0, 0], y=value, xref='x', yref=axis,
                               text=f"Line @ {value}", showarrow=False, font=dict(color=color))
        if line1_val is not None and axis1 in ['y1', 'y2']:
            add_hline(line1_val, axis1, 'red')
        if line2_val is not None and axis2 in ['y1', 'y2']:
            add_hline(line2_val, axis2, 'blue')

        fig.update_layout(title="Time Series Analysis",
                          xaxis_title="Date", yaxis_title='Primary Y axis', height=700)
        return dropdown_options, dropdown_options, fig
    return dropdown_options, dropdown_options, go.Figure()

# =================================
# Callback: descarga gráfico (HTML)
# =================================
@dash.callback(
    Output("download-graph", "data"),
    Input("save-button", "n_clicks"),
    State("time-series-graph", "figure"),
    State("project-name-store", "data"),
    prevent
