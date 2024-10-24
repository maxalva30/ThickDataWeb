from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
from dash import Dash

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
        dcc.Store(id='upload-status', data={'status': 'idle'}),  # Nuevo Store para el estado de carga
        html.Div(className='footer', children=[
            html.P("Copyright © 2024 Metso")
        ]),
        # Modal para la carga del archivo
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
    ]
)

# Callback para almacenar los datos del archivo cargado y actualizar el estado de carga
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-status', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')],
    prevent_initial_call=True
)
def store_uploaded_data(contents, filename):
    if contents is not None:
        # Actualizar estado a 'procesando'
        upload_status = {'status': 'processing'}
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
            data = df.to_dict('records')
            # Actualizar estado a 'completado'
            upload_status = {'status': 'done'}
            return data, upload_status
        except Exception as e:
            print("Error al leer el archivo:", e)
            # Actualizar estado a 'error'
            upload_status = {'status': 'error'}
            return None, upload_status
    return None, {'status': 'idle'}

# Callback para el enrutamiento de páginas (sin cambios)
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/plots':
        return plots.layout
    else:
        # Layout de la página principal (mantener el mismo código que antes)
        # ...
        pass  # Reemplaza 'pass' con el layout de tu página principal

# Callback para mostrar el nombre del archivo cargado (sin cambios)
@app.callback(
    Output('upload-text', 'children'),
    Input('upload-data', 'filename')
)
def update_output_filename(filename):
    if filename:
        return html.Span([html.Img(src='/assets/excel-icon.png', style={'width': '20px', 'marginRight': '10px'}), f"{filename}"])
    return "Drop or Select a File"

# Callback para manejar el modal de carga
@app.callback(
    Output('loading-modal', 'is_open'),
    [Input('upload-data', 'filename'),
     Input('upload-status', 'data')],
    [State('loading-modal', 'is_open')],
    prevent_initial_call=True
)
def handle_upload_modal(filename, upload_status, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'upload-data' and filename and not is_open:
        # Abrir modal cuando se selecciona un archivo
        return True
    elif triggered_id == 'upload-status' and upload_status.get('status') == 'done' and is_open:
        # Cerrar modal cuando el procesamiento ha terminado
        return False
    return is_open

if __name__ == "__main__":
    app.run_server(debug=True)
