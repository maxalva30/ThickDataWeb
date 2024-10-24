from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
from dash import Dash
import time

# Crear la aplicación Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

from pages import plots  # Importar la subpágina de análisis

# Layout de la aplicación
app.layout = html.Div(
    className="main-container",
    children=[
        # Contenedor del encabezado
        html.Div(
            className="header-container",
            children=[
                html.Img(src='/assets/MetsoLogo.png', className="logo"),
                html.H1("Thickener Operational Data Analysis", className="main-title")
            ]
        ),
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', style={'flex': '1'}),
        dcc.Store(id='stored-data', storage_type='session'),  # Aquí almacenaremos los datos leídos del archivo Excel
        html.Div(className='footer', children=[
            html.P("Copyright © 2024 Metso")
        ]),
        # Modal para la barra de progreso
        dbc.Modal(
            [
                dbc.ModalHeader("Cargando archivo..."),
                dbc.ModalBody([
                    html.Div("Por favor espere mientras se carga el archivo."),
                    dbc.Progress(id="progress-bar", striped=True, animated=True, style={"marginTop": "10px"}),
                    dcc.Interval(id="interval-progress", interval=500, n_intervals=0)
                ]),
            ],
            id="loading-modal",
            is_open=False,
        ),
    ]
)

# Callback para almacenar los datos del archivo cargado
@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def store_uploaded_data(contents, filename):
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            # Leer el archivo Excel completo y luego seleccionar las columnas deseadas
            df = pd.read_excel(io.BytesIO(decoded), sheet_name=0, skiprows=6, engine='openpyxl')

            # Seleccionar las columnas que corresponden al rango de D a N
            df = df.iloc[:, 3:14]  # Esto selecciona las columnas desde la cuarta (D) hasta la décimo cuarta (N)

            # Asegurarse de que la primera columna sea tratada como datetime
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Convertir el DataFrame a un diccionario para almacenarlo
            return df.to_dict('records')
        except Exception as e:
            print("Error al leer el archivo:", e)
    return None

# Callback para el enrutamiento de páginas
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/plots':
        return plots.layout
    else:
        # Layout de la página principal
        return html.Div(
            className="content-container",
            children=[
                html.Div(
                    className="left-column",
                    children=[
                        html.H3("Project Information", className="section-title"),
                        html.Div(
                            className="form-container",
                            children=[
                                html.Table(
                                    children=[
                                        html.Tr([
                                            html.Td(html.Label("Project Name"), className="label-cell"),
                                            html.Td(dcc.Input(type="text", id="project-name", className="input-cell")),
                                        ]),
                                        html.Tr([
                                            html.Td(html.Label("Operation Name"), className="label-cell"),
                                            html.Td(dcc.Input(type="text", id="operation-name", className="input-cell")),
                                        ]),
                                        html.Tr([
                                            html.Td(html.Label("Type of Thickener"), className="label-cell"),
                                            html.Td(dcc.Dropdown(
                                                id="thickener-type",
                                                options=[
                                                    {'label': 'High Rate Thickener', 'value': 'High Rate Thickener'},
                                                    {'label': 'High Compression Thickener', 'value': 'High Compression Thickener'},
                                                    {'label': 'Paste Thickener', 'value': 'Paste Thickener'},
                                                    {'label': 'Clarifier Thickener', 'value': 'Clarifier Thickener'},
                                                    {'label': 'HRT-S', 'value': 'HRT-S'},
                                                    {'label': 'Deep Cone Settler', 'value': 'Deep Cone Settler'},
                                                    {'label': 'Non-Metso Thickener', 'value': 'Non-Metso Thickener'}
                                                ],
                                                className="dropdown-cell"
                                            )),
                                        ]),
                                        html.Tr([
                                            html.Td(html.Label("User Name"), className="label-cell"),
                                            html.Td(dcc.Input(type="text", id="user-name", className="input-cell")),
                                        ])
                                    ],
                                    className="input-table"
                                )
                            ]
                        ),
                        html.H3("Technical Information", className="section-title"),
                        html.Div(
                            className="form-container",
                            children=[
                                html.Table(
                                    children=[
                                        html.Tr([
                                            html.Td(html.Label("Specific Gravity (-)"), className="label-cell"),
                                            html.Td(dcc.Input(type="number", id="specific-gravity", className="input-cell")),
                                        ]),
                                        html.Tr([
                                            html.Td(html.Label("Flocculant Strength (%)"), className="label-cell"),
                                            html.Td(dcc.Input(type="number", id="flocculant-strength", className="input-cell")),
                                        ])
                                    ],
                                    className="input-table"
                                )
                            ]
                        ),
                        html.H3("Raw Data Entry", className="section-title"),
                        html.Div(
                            className="upload-container",
                            children=[
                                dcc.Upload(
                                    id='upload-data',
                                    children=html.Div([html.Span('Drop or Select a File', id='upload-text')]),
                                    style={
                                        'width': '300px',
                                        'height': '60px',
                                        'lineHeight': '60px',
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '5px',
                                        'textAlign': 'center',
                                        'backgroundColor': '#f9f9f9',
                                    },
                                    multiple=False
                                ),
                                html.Div(id='output-file-upload')
                            ]
                        ),
                        html.H3("Comments", className="section-title"),
                        html.Div(
                            className="comments-container",
                            children=[
                                dcc.Textarea(
                                    id="comments",
                                    className="comments-box",
                                    placeholder="Enter any additional comments here...",
                                    style={'width': '80%', 'height': 150}
                                )
                            ]
                        )
                    ],
                    style={'width': '30%', 'padding': '20px'}
                ),
                html.Div(
                    className="right-column",
                    children=[
                        html.H3("Data Analysis", className="section-title"),
                        html.Div(
                            className="analysis-container",
                            children=[
                                html.A(
                                    href="/plots",
                                    children=[
                                        html.Div(
                                            children=[
                                                html.Img(src='/assets/timeimg.png', className="analysis-img"),
                                                html.P("Time Series", className="analysis-text")
                                            ],
                                            className="analysis-box"
                                        )
                                    ]
                                )
                            ],
                            style={'display': 'flex', 'justify-content': 'center'}
                        )
                    ],
                    style={'width': '70%', 'padding': '20px'}
                )
            ],
            style={'display': 'flex', 'flexDirection': 'row'}
        )

# Callback para mostrar el nombre del archivo cargado
@app.callback(
    Output('upload-text', 'children'),
    Input('upload-data', 'filename')
)
def update_output_filename(filename):
    if filename:
        return html.Span([html.Img(src='/assets/excel-icon.png', style={'width': '20px', 'marginRight': '10px'}), f"{filename}"])
    return "Drop or Select a File"

# Callback para manejar la barra de progreso y el modal
@app.callback(
    [Output('loading-modal', 'is_open'),
     Output('progress-bar', 'value'),
     Output('progress-bar', 'label')],
    [Input('upload-data', 'contents'),
     Input('interval-progress', 'n_intervals')],
    [State('loading-modal', 'is_open')],
    prevent_initial_call=True
)
def handle_upload_and_progress(contents, n_intervals, is_open):
    if contents is not None and not is_open:
        # Abrir modal cuando se sube un archivo
        return True, 0, "0%"
    
    if is_open:
        if n_intervals < 10:  # Se actualiza la barra hasta el 100%
            progress = (n_intervals + 1) * 10
            return True, progress, f"{progress}%"
        else:
            # Cuando alcanza 100%
            return False, 100, "Carga completa"  # Cerrar modal y finalizar el progreso
    
    return is_open, 0, ""

if __name__ == "__main__":
    app.run_server(debug=True)
