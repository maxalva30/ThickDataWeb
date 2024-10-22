from dash import dcc, html, Input, Output, State
import dash
import plotly.graph_objs as go
import pandas as pd
#from app import app

dash.register_page(__name__, path='/plots')

# Layout de la página de análisis con el diseño ajustado
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
     State('stored-data', 'data')]
)
def update_graph(n_clicks, primary_vars, secondary_vars, stored_data):
    # Convertir los datos almacenados de vuelta a un DataFrame
    if stored_data is None:
        return [], [], go.Figure()

    df = pd.DataFrame(stored_data)
    # Configurar las opciones del dropdown en base a las columnas del DataFrame
    dropdown_options = [{'label': col, 'value': col} for col in df.columns[1:]]  # Excluir la columna de fechas

    # Generar la gráfica si hay un clic en el botón y variables seleccionadas
    if n_clicks and primary_vars:
        fig = go.Figure()

        # Añadir cada serie del eje Y primario
        for var in primary_vars:
            fig.add_trace(
                go.Scatter(
                    x=df.iloc[:, 0], 
                    y=df[var], 
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
                        x=df.iloc[:, 0], 
                        y=df[var], 
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
            title="Time Series Analysis",
            xaxis_title="Date",
            yaxis_title='Primario',
            height=700  # Ajustar la altura del gráfico
        )
        return dropdown_options, dropdown_options, fig

    return dropdown_options, dropdown_options, go.Figure()
