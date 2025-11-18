from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
import dash  # para callback_context
from dash import Dash

# =========================
# Crear la aplicación Dash
# =========================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    use_pages=True,  # por si en plots.py sigues usando dash.register_page
)
server = app.server

# Importar la subpágina de análisis DESPUÉS de crear la app
from pages import plots  # noqa: E402


# =========================
# Layout principal
# =========================
app.layout = html.Div(
    className="main-container",
    style={"display": "flex", "flexDirection": "column", "minHeight": "100vh"},
    children=[
        # Encabezado
        html.Div(
            className="header-container",
            style={
                "display": "flex",
                "justifyContent": "center",
                "alignItems": "center",
                "padding": "20px",
            },
            children=[
                html.Img(src="/assets/MetsoLogo.png", className="logo"),
                html.H1("Thickener Operational Data Analysis", className="main-title"),
            ],
        ),

        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content", style={"flex": "1"}),

        # Stores
        dcc.Store(id="stored-data", storage_type="session"),
        dcc.Store(id="project-name-store", storage_type="session"),

        # Footer
        html.Div(
            className="footer",
            children=[html.P("Copyright © 2024 Metso")],
            style={"textAlign": "center", "padding": "10px"},
        ),
    ],
)


# =========================
# Navegación entre páginas
# =========================
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/plots":
        return plots.layout
    else:
        return html.Div(
            className="content-container",
            style={"display": "flex", "flexDirection": "row"},
            children=[
                # -------- COLUMNA IZQUIERDA --------
                html.Div(
                    className="left-column",
                    style={"width": "30%", "padding": "20px"},
                    children=[
                        html.H3("Project Information", className="section-title"),
                        html.Div(
                            className="form-container",
                            children=[
                                html.Table(
                                    className="input-table",
                                    children=[
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label("Project Name"),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Input(
                                                        type="text",
                                                        id="project-name",
                                                        className="input-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label("Operation Name"),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Input(
                                                        type="text",
                                                        id="operation-name",
                                                        className="input-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label("Type of Thickener"),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Dropdown(
                                                        id="thickener-type",
                                                        options=[
                                                            {
                                                                "label": "High Rate Thickener",
                                                                "value": "High Rate Thickener",
                                                            },
                                                            {
                                                                "label": "High Compression Thickener",
                                                                "value": "High Compression Thickener",
                                                            },
                                                            {
                                                                "label": "Paste Thickener",
                                                                "value": "Paste Thickener",
                                                            },
                                                            {
                                                                "label": "Clarifier Thickener",
                                                                "value": "Clarifier Thickener",
                                                            },
                                                            {
                                                                "label": "HRT-S",
                                                                "value": "HRT-S",
                                                            },
                                                            {
                                                                "label": "Deep Cone Settler",
                                                                "value": "Deep Cone Settler",
                                                            },
                                                            {
                                                                "label": "Non-Metso Thickener",
                                                                "value": "Non-Metso Thickener",
                                                            },
                                                        ],
                                                        className="dropdown-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label("User Name"),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Input(
                                                        type="text",
                                                        id="user-name",
                                                        className="input-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                    ],
                                )
                            ],
                        ),

                        html.H3("Technical Information", className="section-title"),
                        html.Div(
                            className="form-container",
                            children=[
                                html.Table(
                                    className="input-table",
                                    children=[
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label(
                                                        "Solid Specific Gravity (-)"
                                                    ),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Input(
                                                        type="number",
                                                        id="specific-gravity",
                                                        className="input-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td(
                                                    html.Label(
                                                        "Flocculant Strength (%)"
                                                    ),
                                                    className="label-cell",
                                                ),
                                                html.Td(
                                                    dcc.Input(
                                                        type="number",
                                                        id="flocculant-strength",
                                                        className="input-cell",
                                                    )
                                                ),
                                            ]
                                        ),
                                    ],
                                )
                            ],
                        ),

                        html.H3("Raw Data Entry", className="section-title"),
                        html.Div(
                            className="upload-container",
                            style={
                                "position": "relative",
                                "width": "320px",          # un poco más que el upload
                                "display": "inline-block", # para que no se estire a todo el ancho
                            },
                            children=[
                                dcc.Upload(
                                    id="upload-data",
                                    children=html.Div(
                                        [
                                            html.Span(
                                                "Drop or Select a File",
                                                id="upload-text",
                                            )
                                        ]
                                    ),
                                    style={
                                        "width": "300px",
                                        "height": "60px",
                                        "lineHeight": "60px",
                                        "borderWidth": "1px",
                                        "borderStyle": "dashed",
                                        "borderRadius": "5px",
                                        "textAlign": "center",
                                        "backgroundColor": "#f9f9f9",
                                    },
                                    multiple=False,
                                ),
                                # Botón "X" estético pegado al recuadro
                                html.Button(
                                    "×",
                                    id="remove-upload",
                                    n_clicks=0,
                                    style={
                                        "position": "absolute",
                                        "top": "5px",
                                        "right": "5px",
                                        "width": "22px",
                                        "height": "22px",
                                        "borderRadius": "4px",
                                        "backgroundColor": "#f5f5f5",
                                        "color": "#cc0000",
                                        "border": "1px solid #ccc",
                                        "fontSize": "14px",
                                        "lineHeight": "18px",
                                        "cursor": "pointer",
                                        "padding": "0",
                                    },
                                ),
                                html.Div(id="output-file-upload"),
                            ],
                        ),

                        html.H3("Comments", className="section-title"),
                        html.Div(
                            className="comments-container",
                            children=[
                                dcc.Textarea(
                                    id="comments",
                                    className="comments-box",
                                    placeholder="Enter any additional comments here...",
                                    style={"width": "80%", "height": 150},
                                )
                            ],
                        ),
                    ],
                ),

                # -------- COLUMNA DERECHA --------
                html.Div(
                    className="right-column",
                    style={"width": "70%", "padding": "20px"},
                    children=[
                        html.H3("Data Analysis", className="section-title"),
                        html.Div(
                            className="analysis-container",
                            style={"display": "flex", "justifyContent": "center"},
                            children=[
                                html.A(
                                    href="/plots",
                                    children=[
                                        html.Div(
                                            className="analysis-box",
                                            children=[
                                                html.Img(
                                                    src="/assets/timeimg.png",
                                                    className="analysis-img",
                                                ),
                                                html.P(
                                                    "Time Series",
                                                    className="analysis-text",
                                                ),
                                            ],
                                        )
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )


# =========================
# Callback: upload + botón X
# =========================
@app.callback(
    [Output("stored-data", "data"), Output("upload-text", "children")],
    [Input("upload-data", "contents"), Input("remove-upload", "n_clicks")],
    [State("upload-data", "filename")],
)
def handle_uploaded_file(contents, remove_clicks, filename):
    ctx = dash.callback_context

    # Carga inicial de la app
    if not ctx.triggered:
        return None, "Drop or Select a File"

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # Si se hizo clic en la X → limpiar todo
    if trigger == "remove-upload":
        return None, "Drop or Select a File"

    # Si se cargó un archivo nuevo
    if trigger == "upload-data" and contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            df = pd.read_excel(
                io.BytesIO(decoded),
                sheet_name=0,
                skiprows=6,
                engine="openpyxl",
            )
            # Columnas D a N
            df = df.iloc[:, 3:14]
            # Primera columna como datetime
            df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], errors="coerce")

            file_label = html.Span(
                [
                    html.Img(
                        src="/assets/excel-icon.png",
                        style={"width": "20px", "marginRight": "10px"},
                    ),
                    f"{filename}",
                ]
            )
            return df.to_dict("records"), file_label
        except Exception as e:
            print("Error al leer el archivo:", e)
            return None, "Error reading file. Try again."

    # Fallback
    return None, "Drop or Select a File"


# =========================
# Callback: guardar metadata del proyecto
# =========================
@app.callback(
    Output("project-name-store", "data"),
    [
        Input("project-name", "value"),
        Input("operation-name", "value"),
        Input("thickener-type", "value"),
        Input("user-name", "value"),
    ],
)
def store_project_meta(project_name, operation_name, thickener_type, user_name):
    parts = []

    if project_name:
        parts.append(project_name)
    if operation_name:
        parts.append(operation_name)
    if thickener_type:
        parts.append(thickener_type)
    if user_name:
        parts.append(f"by {user_name}")

    if not parts:
        return ""

    # Ejemplo: "Yanacocha TH - Tailings - HRT-S by Max"
    return " - ".join(parts)


# =========================
# Run local
# =========================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True, use_reloader=False)
