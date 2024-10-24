from dash import dcc, html, Input, Output, State
import dash
import plotly.graph_objs as go
import pandas as pd

# Registrar la página
dash.register_page(__name__, path='/plots')

# Layout de la página de análisis
layout = html.Div(
    className="main-container",
    children=[
        # Contenedor de opciones (Dropdowns y botón)
        html.Div(
            className="options-container",
            style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center', 'margin': '20px'},
            children=[
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='primary-variable',
                            placeholder='Seleccione variable(es) primaria(s)',
                            multi=True,  # Habilitar selección múltiple
                            style={'width': '250px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='secondary-variable',
                            placeholder='Seleccione variable(es) secundaria(s)',
                            multi=True,  # Habilitar selección múltiple
                            style={'width': '250px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),
                # Nuevo Dropdown para seleccionar el período de agrupación
                html.Div(
                    children=[
                        dcc.Dropdown(
                            id='time-period',
                            options=[
                                {'label': '5 Minutos', 'value': '5T'},
                                {'label': '10 Minutos', 'value': '10T'},
                                {'label': '30 Minutos', 'value': '30T'},
                                {'label': '1 Hora', 'value': '1H'}
                            ],
                            placeholder='Seleccione período de agrupación',
                            style={'width': '200px'},
                        )
                    ],
                    style={'flex': '1', 'margin-right': '20px'}
                ),
                html.Button('Graficar', id='plot-button', className='btn btn-primary', style={'margin-right': '20px'})
            ]
        ),
        
        # Contenedor del gráfico
        html.Div(
            className="graph-container",
            style={'width': '100%', 'display': 'flex', 'justify-content': 'center'},
            children=[
                dcc.Graph(
                    id='time-series-graph',
                    className='time-series-graph',
                    config={'displayModeBar': True},
                )
            ]
        )
    ]
)

# Callback para actualizar las opciones del Dropdown y graficar los datos
@dash.callback(
    [Output('primary-variable', 'options'),
     Output('secondary-variable', 'options'),
     Output('time-series-graph', 'figure')],
    [Input('plot-button', 'n_clicks')],
    [State('primary-variable', 'value'),
     State('secondary-variable', 'value'),
     State('time-period', 'value'),  # Nuevo State para capturar el período seleccionado
     State('stored-data', 'data')]
)
def update_graph(n_clicks, primary_vars, secondary_vars, time_period, stored_data):
    # Convertir los datos almacenados de vuelta a un DataFrame
    if stored_data is None:
        return [], [], go.Figure()

    df = pd.DataFrame(stored_data)

    # Asegurarse de que la columna de fecha sea datetime
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
    
    # Configurar las opciones del dropdown en base a las columnas del DataFrame
    dropdown_options = [{'label': col, 'value': col} for col in df.columns[1:]]  # Excluir la columna de fechas

    # Verificar si se seleccionó un período de agrupación
    if time_period:
        # Resamplear los datos para obtener los promedios por el período seleccionado
        df = df.set_index(df.columns[0])  # Asegurar que la columna de fecha es el índice
        df_resampled = df.resample(time_period).mean().reset_index()  # Calcular el promedio por período
    else:
        # Si no se seleccionó un período, mantener los datos originales
        df_resampled = df

    # Generar la gráfica si hay un clic en el botón y variables seleccionadas
    if n_clicks and primary_vars:
        fig = go.Figure()

        # Añadir cada serie del eje Y primario
        for var in primary_vars:
            fig.add_trace(
                go.Scatter(
                    x=df_resampled.iloc[:, 0], 
                    y=df_resampled[var], 
                    mode='lines', 
                    name=var,
                    yaxis='y1'
                )
            )

        # Añadir cada serie del eje Y secundario si hay variables seleccionadas
        if secondary_vars:
            for var in secondary_vars:
                fig.add_trace(
                    go.Scatter(
                        x=df_resampled.iloc[:, 0], 
                        y=df_resampled[var], 
                        mode='lines', 
                        name=var,
                        yaxis='y2'
                    )
                )
            # Configuración del eje Y secundario
            fig.update_layout(
                yaxis2=dict(
                    title='Secundario',
                    overlaying='y',
                    side='right'
                )
            )

        fig.update_layout(
            title="Análisis de Series Temporales",
            xaxis_title="Fecha",
            yaxis_title='Primario',
            height=700  # Ajustar la altura del gráfico
        )
        return dropdown_options, dropdown_options, fig

    return dropdown_options, dropdown_options, go.Figure()
