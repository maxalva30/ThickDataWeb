from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64
from pages import plots   # sub-página
# ───────────────────────────────
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server
# ───────────────────────────────
# Layout
app.layout = html.Div(
    className="main-container",
    style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100vh'},
    children=[
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

        # stores
        dcc.Store(id='stored-data', storage_type='session'),
        dcc.Store(id='project-name-store', storage_type='session'),

        # footer
        html.Div(className='footer', style={'textAlign': 'center', 'padding': '10px'},
                 children=[html.P("Copyright © 2024 Metso")]),

        # modal + progress
        dbc.Modal(
            id="loading-modal",
            is_open=False,
            children=[
                dbc.ModalHeader("Cargando archivo..."),
                dbc.ModalBody([
                    html.Div("Por favor espere mientras se carga el archivo."),
                    dbc.Progress(id="progress-bar", striped=True, animated=True,
                                 style={"marginTop": "10px"}),
                    dcc.Interval(id="interval-progress",
                                 interval=200,      # 0.2 s
                                 n_intervals=0,
                                 disabled=True,
                                 max_intervals=20)  # seguridad
                ])
            ]
        ),
    ]
)
# ---------------------  home layout helper  ---------------------
def build_home():
    return html.Div(
        style={'display': 'flex', 'flexDirection': 'row'},
        children=[
            # left column
            html.Div(style={'width': '30%', 'padding': '20px'}, children=[
                html.H3("Project Information", className="section-title"),
                html.Table(className="input-table", children=[
                    html.Tr([html.Td("Project Name"), html.Td(dcc.Input(id="project-name"))]),
                    html.Tr([html.Td("Operation Name"), html.Td(dcc.Input(id="operation-name"))]),
                    html.Tr([html.Td("Type of Thickener"), html.Td(
                        dcc.Dropdown(id="thickener-type",
                                     options=[{'label': t, 'value': t} for t in [
                                         'High Rate Thickener', 'High Compression Thickener',
                                         'Paste Thickener', 'Clarifier Thickener',
                                         'HRT-S', 'Deep Cone Settler', 'Non-Metso Thickener']]))]),
                    html.Tr([html.Td("User Name"), html.Td(dcc.Input(id="user-name"))])
                ]),
                html.H3("Technical Information", className="section-title"),
                html.Table(className="input-table", children=[
                    html.Tr([html.Td("Solid Specific Gravity"), html.Td(dcc.Input(id="specific-gravity", type="number"))]),
                    html.Tr([html.Td("Flocculant Strength (%)"), html.Td(dcc.Input(id="flocculant-strength", type="number"))])
                ]),
                html.H3("Raw Data Entry", className="section-title"),
                html.Div(style={'position': 'relative'}, children=[
                    dcc.Upload(id='upload-data',
                               children=html.Div(html.Span('Drop or Select a File', id='upload-text')),
                               style={'width': '300px', 'height': '60px', 'lineHeight': '60px',
                                      'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                                      'textAlign': 'center', 'backgroundColor': '#f9f9f9'},
                               multiple=False),
                    html.Button('×', id='remove-upload', n_clicks=0,
                                style={'position': 'absolute', 'top': '5px', 'right': '5px',
                                       'background': 'transparent', 'border': 'none',
                                       'color': 'red', 'fontSize': '18px', 'cursor': 'pointer'}),
                    html.Div(id='output-file-upload')
                ]),
                html.H3("Comments", className="section-title"),
                dcc.Textarea(id="comments", style={'width': '80%', 'height': 150})
            ]),
            # right column
            html.Div(style={'width': '70%', 'padding': '20px'}, children=[
                html.H3("Data Analysis", className="section-title"),
                html.Div(style={'display': 'flex', 'justify-content': 'center'}, children=[
                    html.A(href="/plots", children=html.Div(className="analysis-box", children=[
                        html.Img(src='/assets/timeimg.png', className="analysis-img"),
                        html.P("Time Series")
                    ]))
                ])
            ])
        ]
    )
# ---------------------  routing  ---------------------
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def router(pathname):
    return plots.layout if pathname == '/plots' else build_home()
# ---------------------  upload / reset  --------------
@app.callback(
    [Output('stored-data', 'data'),
     Output('upload-text', 'children')],
    [Input('upload-data', 'contents'),
     Input('remove-upload', 'n_clicks')],
    State('upload-data', 'filename')
)
def handle_file(contents, remove_clicks, filename):
    if remove_clicks:
        return None, "Drop or Select a File"
    if contents:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_excel(io.BytesIO(decoded), sheet_name=0,
                               skiprows=6, engine='openpyxl')
            df = df.iloc[:, 3:14]
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            icon = html.Img(src='/assets/excel-icon.png',
                            style={'width': '20px', 'marginRight': '10px'})
            return df.to_dict('records'), html.Span([icon, filename])
        except Exception as e:
            print("Error al leer el archivo:", e)
    return None, "Drop or Select a File"
# ---------------------  modal / progress control  ----
@app.callback(
    [Output('loading-modal', 'is_open'),
     Output('progress-bar', 'value'),
     Output('progress-bar', 'label'),
     Output('interval-progress', 'disabled')],
    [Input('upload-data', 'contents'),
     Input('interval-progress', 'n_intervals'),
     Input('stored-data', 'data')],        # <- nuevo input
    State('loading-modal', 'is_open'),
    prevent_initial_call=True
)
def progress_modal(contents, n_intervals, stored_data, is_open):
    # inicio de carga
    if contents and not is_open:
        return True, 0, "0 %", False
    # archivo ya cargado -> cerrar enseguida
    if stored_data and is_open:
        return False, 100, "Carga completa", True
    # mientras está abierto, avanzar barra
    if is_open:
        progress = min((n_intervals + 1) * 25, 100)
        return True, progress, f"{progress} %", False
    return is_open, 0, "", True
# ---------------------  store project name ----------
@app.callback(Output('project-name-store', 'data'),
              Input('project-name', 'value'))
def store_project(name):
    return name or ""
# ---------------------  run local -------------------
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
