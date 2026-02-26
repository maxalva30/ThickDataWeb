from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
import dash  # para callback_context
from dash import Dash
import numpy as np  # <-- NUEVO

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
# Columnas esperadas en el Excel
# ========================= 
UNDERFLOW_DENSITY_COL = "Underflow, kg/m3"
TONNAGE_COL = "Tonnage, tph"

# OJO: cambia estos nombres para que coincidan con tu archivo real
FLOCC_LMIN_COL = "Flocculant, L/min"
FLOCC_M3H_COL = "Flocculant, m3/h"

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
        dcc.Link(
            href="/",  # siempre lleva a la página principal (index)
            children=html.Img(
                src='/assets/MetsoLogo.png',
                className="logo",
                style={"cursor": "pointer"}
            ),
        ),
        html.H1("Thickener Operational Data Analysis", className="main-title"),
    ],
        ),

        dcc.Location(id="url", refresh=False),
        html.Div(id="page-content", style={"flex": "1"}),

        # Stores
        # Para data pesada, usar "memory" (por defecto) para evitar exceder la cuota del navegador
        dcc.Store(id="raw-data"),              # storage_type="memory" por defecto
        dcc.Store(id="stored-data"),           # idem
        # Esta sí puede ser "session" porque es texto pequeño
        dcc.Store(id="project-name-store", storage_type="session"),
        # Footer
        html.Div(
            className="footer",
            children=[html.P("Copyright © 2025 Metso")],
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
                # -------- COLUMNA IZQUIERDA (STEP 1) --------
                html.Div(
                    className="left-column",
                    style={"width": "30%", "padding": "20px"},
                    children=[
                        html.H4("Step 1 – Project & Data", className="step-title"),

                        html.Div(
                            className="card",
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
                                                html.Tr(
                                                    [
                                                        html.Td(
                                                            html.Label("Solid Specific Gravity (t/m3)"),
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
                                                            html.Label("Flocculant Strength (%)"),
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
                            ],
                        ),

                        html.Div(
                            className="card",
                            style={"marginTop": "20px"},
                            children=[
                                html.H3("Raw Data Entry", className="section-title"),
                                html.Div(
                                    className="upload-container",
                                    style={
                                        "position": "relative",
                                        "width": "100%",        # 👉 ocupa todo el ancho de la card
                                        "display": "block",
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
                                            "width": "100%",          # 👉 barra larga como antes
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
                         
                            ],
                        ),

                        html.Div(
                            className="card",
                            style={"marginTop": "20px"},
                            children=[
                                html.H3("Comments", className="section-title"),
                                dcc.Textarea(
                                    id="comments",
                                    className="comments-box",
                                    placeholder="Enter any additional comments here...",
                                    style={"width": "100%", "height": 150},
                                ),
                            ],
                        ),
                    ],
                ),

                # -------- COLUMNA DERECHA (STEP 2) --------
                html.Div(
                    className="right-column",
                    style={"width": "70%", "padding": "20px"},
                    children=[
                        html.H4("Step 2 – Run the analysis", className="step-title"),

                        # --------- BLOQUE SUPERIOR: DATA TRANSFORMATION ---------
                        html.Div(
                            className="card",
                            children=[
                                html.H3("Data Transformation", className="section-title"),
                                html.P(
                                    "Prepare your raw signals for analysis by creating % solids "
                                    "and flocculant dosage (g/t) from plant tags.",
                                    className="section-help",
                                ),
                                dcc.Checklist(
                                    id="data-transformation-options",
                                    options=[
                                        {
                                            "label": "Convert density (kg/m³) to % solids",
                                            "value": "density_to_percent_s",
                                        },
                                        {
                                            "label": "Convert flocculant flow (L/min) to g/t",
                                            "value": "flocc_to_gt",
                                        },
                                        {
                                            "label": "Convert flocculant flow (m³/h) to g/t",
                                            "value": "flocc_to_gt_m3h",
                                        },
                                    ],
                                    value=[],
                                    labelStyle={"display": "block", "marginBottom": "6px"},
                                    inputStyle={"marginRight": "8px"},
                                    className="checkbox-list",
                                ),
                                html.Button(
                                    "Apply transformations",
                                    id="apply-transformations",
                                    n_clicks=0,
                                    className="primary-button",
                                    style={"marginTop": "10px"},
                                ),
                                html.Div(
                                    id="transformation-status",
                                    className="section-help",
                                    style={"marginTop": "6px"},
                                ),
                            ],
                        ),

                        # --------- BLOQUE INFERIOR: DATA ANALYSIS ---------
                        html.Div(
                            className="card",
                            style={"marginTop": "20px"},
                            children=[
                                html.H3("Data Analysis", className="section-title"),
                                html.P(
                                    "Open the analysis workspace to visualize time series, "
                                    "check correlations and add plots to the report.",
                                    className="section-help",
                                ),
                                html.Div(
                                    className="analysis-container",
                                    style={
                                        "display": "flex",
                                        "justifyContent": "flex-start",
                                        "alignItems": "center",
                                        "gap": "24px",
                                        "marginTop": "10px",
                                    },
                                    children=[
                                        html.Img(
                                            src="/assets/timeimg.png",
                                            className="analysis-img",
                                        ),
                                        html.Div(
                                            children=[
                                                html.Ul(
                                                    children=[
                                                        html.Li("Visualize time series"),
                                                        html.Li("Check correlations between variables"),
                                                        html.Li("Add plots to an auto-generated report"),
                                                    ]
                                                ),
                                            dcc.Link(
                                                href="/plots",
                                                children=html.Button(
                                                    "Open Analysis Workspace",
                                                    id="open-analysis-workspace",
                                                    n_clicks=0,
                                                    className="primary-button",
                                                    style={"marginTop": "12px"},
                                                ),
                                                style={"textDecoration": "none"},  # para que no se vea subrayado
                                            )

                                           ]
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        )


# =========================
# Callback: upload + botón X
# =========================

@app.callback(
    [
        Output("stored-data", "data"),
        Output("upload-text", "children"),
        Output("raw-data", "data"),          # 👈 NUEVO
    ],
    [Input("upload-data", "contents"), Input("remove-upload", "n_clicks")],
    [State("upload-data", "filename")],
)
def handle_uploaded_file(contents, remove_clicks, filename):
    ctx = dash.callback_context

    # Carga inicial de la app
    if not ctx.triggered:
        return None, "Drop or Select a File", None   # 👈 ahora devolvemos 3 valores

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # Si se hizo clic en la X → limpiar todo
    if trigger == "remove-upload":
        return None, "Drop or Select a File", None

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
            records = df.to_dict("records")
            # 👇 guardamos tanto en stored-data como en raw-data
            return records, file_label, records
        except Exception as e:
            print("Error al leer el archivo:", e)
            return None, "Error reading file. Try again.", None

    # Fallback
    return None, "Drop or Select a File", None

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
# Callback: aplicar transformaciones (%S y Floc_Dosage_g/t)
# =========================
@app.callback(
    [
        Output("stored-data", "data", allow_duplicate=True),
        Output("transformation-status", "children"),
    ],
    Input("apply-transformations", "n_clicks"),
    State("raw-data", "data"),           # 👈 leemos SIEMPRE de los datos crudos
    State("specific-gravity", "value"),
    State("flocculant-strength", "value"),
    State("data-transformation-options", "value"),
    prevent_initial_call=True,           # 👈 opcional pero limpio: no se llama al inicio
)
def apply_transformations(n_clicks, raw_data, specific_gravity, flocc_strength, options):
    if not n_clicks:
        # No se ha presionado el botón todavía
        return raw_data, ""   # devolvemos lo que haya (o None)

    if raw_data is None:
        return raw_data, "⚠️ Please upload a file before applying transformations."

    df = pd.DataFrame(raw_data).copy()
    messages = []

    # --- 1) Densidad (kg/m3) -> %S ---
    if "density_to_percent_s" in (options or []):
        if UNDERFLOW_DENSITY_COL not in df.columns:
            messages.append(f"❌ Column '{UNDERFLOW_DENSITY_COL}' not found in data.")
        elif specific_gravity is None or specific_gravity <= 1:
            messages.append("❌ Please enter a valid Solid Specific Gravity (>1).")
        else:
            try:
                rho_pulp = df[UNDERFLOW_DENSITY_COL].astype(float)
                rho_w = 1000.0  # kg/m3
                rho_s = float(specific_gravity) * 1000.0

                ws = (rho_pulp - rho_w) / (rho_s - rho_w)
                percent_s = ws * 100.0
                df["Underflow_%S"] = percent_s.clip(lower=0, upper=100)
                messages.append("✅ Created column 'Underflow_%S' from density.")
            except Exception as e:
                print("Error converting density to %S:", e)
                messages.append("❌ Error converting density to % solids.")

    # --- 2) Flocculant flow (L/min) -> g/t ---
    if "flocc_to_gt" in (options or []):
        if FLOCC_LMIN_COL not in df.columns:
            messages.append(f"❌ Column '{FLOCC_LMIN_COL}' not found in data.")
        elif TONNAGE_COL not in df.columns:
            messages.append(f"❌ Column '{TONNAGE_COL}' not found in data.")
        elif flocc_strength is None or flocc_strength <= 0:
            messages.append("❌ Please enter a valid Flocculant Strength (g/L).")
        else:
            try:
                q_lmin = df[FLOCC_LMIN_COL].astype(float)
                tph = df[TONNAGE_COL].astype(float).replace(0, np.nan)
                c_gl = float(flocc_strength)  # g/L

                df["Floc_Dosage_g/t"] = q_lmin * c_gl*10* 60.0 / tph
                messages.append("✅ Created column 'Floc_Dosage_g/t' from L/min.")
            except Exception as e:
                print("Error converting floc L/min to g/t:", e)
                messages.append("❌ Error converting flocculant L/min to g/t.")

    # --- 3) Flocculant flow (m3/h) -> g/t ---
    if "flocc_to_gt_m3h" in (options or []):
        if FLOCC_M3H_COL not in df.columns:
            messages.append(f"❌ Column '{FLOCC_M3H_COL}' not found in data.")
        elif TONNAGE_COL not in df.columns:
            messages.append(f"❌ Column '{TONNAGE_COL}' not found in data.")
        elif flocc_strength is None or flocc_strength <= 0:
            messages.append("❌ Please enter a valid Flocculant Strength (g/L).")
        else:
            try:
                q_m3h = df[FLOCC_M3H_COL].astype(float)
                tph = df[TONNAGE_COL].astype(float).replace(0, np.nan)
                c_gl = float(flocc_strength)  # g/L

                # m3/h → L/min (·1000/60) y misma lógica g/t
                df["Floc_Dosage_g/t"] = q_m3h * (1000.0 / 60.0) *10* c_gl * 60.0 / tph
                messages.append("✅ Created/updated column 'Floc_Dosage_g/t' from m3/h.")
            except Exception as e:
                print("Error converting floc m3/h to g/t:", e)
                messages.append("❌ Error converting flocculant m3/h to g/t.")

    if not messages:
        messages.append("ℹ️ No transformation selected or nothing was applied.")

    return df.to_dict("records"), " | ".join(messages)

# =========================
# Run local
# =========================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True, use_reloader=False)


