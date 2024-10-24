import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64

# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# Asegúrate de que el módulo 'plots' existe y funciona correctamente
from pages import plots

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
        dcc.Store(id='upload-status', data='idle'),  # Nuevo Store para el estado de carga
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
                ]),
            ],
            id="loading-modal",
            is_open=False,
            backdrop='static',  # Evita que se cierre al hacer clic fuera del modal
            keyboard=False  # Evita que se cierre al presionar Esc
        ),
        # Intervalo para actualizar la barra de progreso
        dcc.Interval(id="interval-progress", interval=500, n_intervals=0, disabled=True),
    ]
)

# Callback para almacenar los datos del archivo cargado y actualizar el estado de carga
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'data')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def store_uploaded_data(contents, filename):
    if contents is not None:
        # Procesando el archivo
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            # Procesar el archivo Excel
            df = pd.read_excel(io.BytesIO(decoded), sheet_name=0, skiprows=6, engine='openpyxl')

            # Seleccionar las columnas deseadas
            df = df.iloc[:, 3:14]  # Desde la columna D hasta la N

            # Asegurarse de que la primera columna sea tratada como datetime
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')

            # Convertir el DataFrame a un diccionario para almacenarlo
            data = df.to_dict('records')
            # Actualizar estado a 'done'
            upload_status = 'done'
            return data, upload_status
        except Exception as e:
            print("Error al leer el archivo:", e)
            # Actualizar estado a 'error'
            upload_status = 'error'
            return None, upload_status
    else:
        # Si no hay contenido, no actualizamos nada
        return dash.no_update, dash.no_update

# Callback para el enrutamiento de páginas
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/plots':
        return plots.layout  # Asegúrate de que 'plots.layout' está definido y funciona
    else:
        # Layout de la página principal (como en tu código original)
        return html.Div(
            className="content-container",
            children=[
                html.Div(
                    className="left-column",
                    children=[
                        # ... Tu contenido de la columna izquierda ...
                        # (Asegúrate de incluir todo el contenido aquí)
                    ],
                    style={'width': '30%', 'padding': '20px'}
                ),
                html.Div(
                    className="right-column",
                    children=[
                        # ... Tu contenido de la columna derecha ...
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

# Callback para manejar el modal y la barra de progreso
@app.callback(
    [Output('loading-modal', 'is_open'),
     Output('progress-bar', 'value'),
     Output('progress-bar', 'label'),
     Output('interval-progress', 'disabled'),
     Output('interval-progress', 'n_intervals')],
    [Input('upload-data', 'filename'),
     Input('upload-status', 'data'),
     Input('interval-progress', 'n_intervals')],
    [State('loading-modal', 'is_open'),
     State('interval-progress', 'disabled')],
    prevent_initial_call=True
)
def handle_upload_and_progress(filename, upload_status, n_intervals, is_open, interval_disabled):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'upload-data' and filename is not None:
        # Abrir modal, habilitar intervalo y reiniciar contador
        return True, 0, "0%", False, 0
    elif triggered_id == 'interval-progress' and is_open:
        if upload_status == 'done':
            # Cerrar modal, deshabilitar intervalo
            return False, 100, "Carga completa", True, n_intervals
        else:
            # Incrementar progreso más lentamente
            progress = min(n_intervals * 5, 95)  # Incrementos de 5% hasta el 95%
            return True, progress, f"{progress}%", False, n_intervals
    elif triggered_id == 'upload-status' and upload_status == 'done' and is_open:
        # Asegurar que el progreso llegue al 100% y cerrar el modal
        return False, 100, "Carga completa", True, n_intervals
    return is_open, dash.no_update, dash.no_update, interval_disabled, n_intervals

if __name__ == "__main__":
    app.run_server(debug=True)
