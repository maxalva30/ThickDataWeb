from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64
from dash import Dash

# ──────────────────────────────────────────────
# Crear la aplicación Dash
# ──────────────────────────────────────────────
app = Dash(__name__,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

from pages import plots  # Sub-página de análisis

# ──────────────────────────────────────────────
# Layout principal
# ──────────────────────────────────────────────
app.layout = html.Div(
    className="main-container",
    style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100vh'},
    children=[
        # Encabezado
        html.Div(
            className="header-container",
            style={'display': 'flex', 'justify-content': 'center',
                   'alignItems': 'center', 'padding': '20px'},
            children=[
                html.Img(src='/assets/MetsoLogo.png', className="logo"),
                html.H1("Thickener Operational Data Analysis", className="main-title")
            ]
        ),

        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content', style={'flex': '1'}),

        # Almacenes en sesión
        dcc.Store(id='stored-data', storage_type='session'),
        dcc.Store(id='project-name-store', storage_type='session'),

        # Pie de página
        html.Div(className='footer',
                 children=[html.P("Copyright © 2024 Metso")],
                 style={'textAlign': 'center', 'padding': '10px'}),

        # Modal de carga + barra de progreso
        dbc.Modal(
            [
                dbc.ModalHeader("Cargando archivo..."),
                dbc.ModalBody([
                    html.Div("Por favor espere mientras se carga el archivo."),
                    dbc.Progress(id="progress-bar", striped=True,
                                 animated=True, style={"marginTop": "10px"}),
                    # Intervalo: deshabilitado por defecto
                    dcc.Interval(id="interval-progress",
                                 interval=500,             # 0.5 s
                                 n_intervals=0,
                                 disabled=True,
                                 max_intervals=200)        # safety-stop
                ]),
            ],
            id="loading-modal",
            is_open=False,
        ),
    ]
)

# ──────────────────────────────────────────────
# Navegación entre páginas
# ──────────────────────────────────────────────
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    return plots.layout if pathname == '/plots' else build_home()


def build_home():
    """Devuelve el layout de la página principal."""
    return html.Div(
        className="content-container",
        children=[
            # -------- Columna izquierda --------
            html.Div(
                className="left-column",
                style={'width': '30%', 'padding': '20px'},
                children=[
                    html.H3("Project Information", className="section-title"),
                    build_info_table(),
                    html.H3("Technical Information", className="section-title"),
                    build_tech_table(),
                    html.H3("Raw Data Entry", className="section-title"),
                    build_upload_box(),
                    html.H3("Comments", className="section-title"),
                    dcc.Textarea(id="comments", className="comments-box",
                                 placeholder="Enter any additional comments here...",
                                 style={'width': '80%', 'height': 150})
                ]
            ),
            # -------- Columna derecha --------
            html.Div(
                className="right-column",
                style={'width': '70%', 'padding': '20px'},
                children=[
                    html.H3("Data Analysis", className="section-title"),
                    html.Div(
                        className="analysis-container",
                        style={'display': 'flex', 'justify-content': 'center'},
                        children=[
                            html.A(
                                href="/plots",
                                children=[
                                    html.Div(
                                        className="analysis-box",
                                        children=[
                                            html.Img(src='/assets/timeimg.png',
                                                     className="analysis-img"),
                                            html.P("Time Series", className="analysis-text")
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ],
        style={'display': 'flex', 'flexDirection': 'row'}
    )


# --- Helpers para construir tablas y upload ----------------------------------
def build_info_table():
    return html.Table(className="input-table", children=[
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
                    {'label': t, 'value': t} for t in [
                        'High Rate Thickener', 'High Compression Thickener',
                        'Paste Thickener', 'Clarifier Thickener',
                        'HRT-S', 'Deep Cone Settler', 'Non-Metso Thickener'
                    ]
                ],
                className="dropdown-cell"
            )),
        ]),
        html.Tr([
            html.Td(html.Label("User Name"), className="label-cell"),
            html.Td(dcc.Input(type="text", id="user-name", className="input-cell")),
        ])
    ])


def build_tech_table():
    return html.Table(className="input-table", children=[
        html.Tr([
            html.Td(html.Label("Solid Specific Gravity (-)"), className="label-cell"),
            html.Td(dcc.Input(type="number", id="specific-gravity", className="input-cell")),
        ]),
        html.Tr([
            html.Td(html.Label("Flocculant Strength (%)"), className="label-cell"),
            html.Td(dcc.Input(type="number", id="flocculant-strength", className="input-cell")),
        ])
    ])


def build_upload_box():
    return html.Div(className="upload-container", style={'position': 'relative'}, children=[
        dcc.Upload(
            id='upload-data',
            children=html.Div([html.Span('Drop or Select a File', id='upload-text')]),
            style={
                'width': '300px', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed',
                'borderRadius': '5px', 'textAlign': 'center',
                'backgroundColor': '#f9f9f9',
            },
            multiple=False
        ),
        # Botón “X” para resetear carga
        html.Button('×', id='remove-upload', n_clicks=0,
                    style={'position': 'absolute', 'top': '5px', 'right': '5px',
                           'backgroundColor': 'transparent', 'color': 'red',
                           'border': 'none', 'fontSize': '18px', 'cursor': 'pointer'}),
        html.Div(id='output-file-upload')
    ])


# ──────────────────────────────────────────────
# Callbacks
# ──────────────────────────────────────────────
# 1) Carga y reseteo de archivo
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-text', 'children')],
    [Input('upload-data', 'contents'),
     Input('remove-upload', 'n_clicks')],
    State('upload-data', 'filename')
)
def handle_uploaded_file(contents, remove_clicks, filename):
    if remove_clicks:               # <-- n_clicks > 0
        return None, "Drop or Select a File"

    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_excel(io.BytesIO(decoded),
                               sheet_name=0, skiprows=6, engine='openpyxl')
            df = df.iloc[:, 3:14]                     # columnas D–N
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            icon = html.Img(src='/assets/excel-icon.png',
                            style={'width': '20px', 'marginRight': '10px'})
            return df.to_dict('records'), html.Span([icon, filename])
        except Exception as e:
            print("Error al leer el archivo:", e)

    return None, "Drop or Select a File"


# 2) Progreso y control del Interval
@app.callback(
    [Output('loading-modal', 'is_open'),
     Output('progress-bar', 'value'),
     Output('progress-bar', 'label'),
     Output('interval-progress', 'disabled')],
    [Input('upload-data', 'contents'),
     Input('interval-progress', 'n_intervals')],
    State('loading-modal', 'is_open'),
    prevent_initial_call=True
)
def handle_upload_and_progress(contents, n_intervals, is_open):
    # Cuando se sube un archivo → abre modal y habilita Interval
    if contents and not is_open:
        return True, 0, "0 %", False

    # Mientras el modal está abierto, avanza la barra
    if is_open:
        progress = (n_intervals + 1) * 10
        if progress >= 100:
            # Carga finalizada → cierra modal y deshabilita Interval
            return False, 100, "Carga completa", True
        return True, progress, f"{progress} %", False

    # Situación neutra
    return is_open, 0, "", True


# 3) Almacenar “Project Name”
@app.callback(Output('project-name-store', 'data'),
              Input('project-name', 'value'))
def store_project_name(project_name):
    return project_name or ""


# ──────────────────────────────────────────────
# Run local (en Render usarás gunicorn)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
