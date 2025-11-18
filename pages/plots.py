import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import base64

from datetime import datetime, date

dash.register_page(__name__, path="/plots", name="Plots")

# -----------------------------
# Helpers
# -----------------------------
def _get_df(stored):
    if not stored:
        return None, "No data loaded. Go back to the main page and upload an Excel file."
    try:
        df = pd.DataFrame(stored)
    except Exception as e:
        return None, f"Could not read stored-data: {e}"

    # Try to detect time column
    time_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
    if not time_cols:
        time_cols = [df.columns[0]]
    time_col = time_cols[0]

    return df, time_col


def _resample(df, time_col, rule):
    if not rule:
        return df.copy()

    try:
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col])
        df = df.set_index(time_col).sort_index()
        df_res = df.resample(rule).mean(numeric_only=True)
        df_res = df_res.reset_index()
        return df_res
    except Exception:
        return df.copy()


def _fig_to_base64_png(fig, width=1200, height=650):
    try:
        png_bytes = pio.to_image(fig, format="png", width=width, height=height, scale=2)
        return "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
    except Exception:
        return None

def _fig_to_inline_html(fig):
    try:
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)
    except Exception:
        return None


# -----------------------------
# Init date pickers from data
# -----------------------------
@dash.callback(
    Output("ba_cutoff", "min_date_allowed"),
    Output("ba_cutoff", "max_date_allowed"),
    Output("ba_cutoff", "date"),
    Output("t_range", "min_date_allowed"),
    Output("t_range", "max_date_allowed"),
    Output("t_range", "start_date"),
    Output("t_range", "end_date"),
    Input("stored-data", "data"),
)
def init_date_pickers(stored):
    df, time_col = _get_df(stored)
    default_min = date(2000, 1, 1)
    default_max = date(2050, 12, 31)

    if df is None or isinstance(df, str):
        return (
            default_min,
            default_max,
            None,
            default_min,
            default_max,
            None,
            None,
        )

    try:
        dmin = pd.to_datetime(df[time_col].min()).date()
        dmax = pd.to_datetime(df[time_col].max()).date()
    except Exception:
        dmin, dmax = default_min, default_max

    # BA: cutoff default = última fecha
    # Target: rango completo
    return dmin, dmax, dmax, dmin, dmax, dmin, dmax


# -----------------------------
# Stores
# -----------------------------
project_name_store = dcc.Store(id="project-name-store")
ba_year_store = dcc.Store(id="ba_year_store", data=date.today().year)
t_year_store = dcc.Store(id="t_year_store", data=date.today().year)
report_items = dcc.Store(id="report-items", data=[])

# -----------------------------
# Modals
# -----------------------------
MONTH_OPTS = [
    {"label": "Jan", "value": 1},
    {"label": "Feb", "value": 2},
    {"label": "Mar", "value": 3},
    {"label": "Apr", "value": 4},
    {"label": "May", "value": 5},
    {"label": "Jun", "value": 6},
    {"label": "Jul", "value": 7},
    {"label": "Aug", "value": 8},
    {"label": "Sep", "value": 9},
    {"label": "Oct", "value": 10},
    {"label": "Nov", "value": 11},
    {"label": "Dec", "value": 12},
]

ba_modal = dbc.Modal(
    id="ba_modal",
    is_open=False,
    size="xl",
    scrollable=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Before vs After analysis")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Parameter"),
                    dcc.Dropdown(id="ba_param", placeholder="Select column", clearable=False),
                ], md=4),
                dbc.Col([
                    html.Label("Cutoff date"),
                    dbc.InputGroup([
                        dbc.Input(id="ba_cutoff_display", placeholder="Pick a date", readonly=True),
                        dbc.Button("📅", id="ba_cal_btn", color="secondary", outline=True, n_clicks=0),
                    ], size="md"),
                ], md=4),
                dbc.Col([
                    html.Label("Window (days)"),
                    dcc.Input(id="ba_window", type="number", value=7, min=1, max=90, step=1,
                              style={"width": "100%"}),
                ], md=4),
            ], className="g-3"),

            # --- Calendar popup inside BA modal ---
            dbc.Modal(
                id="ba_cal_modal", is_open=False, size="sm", scrollable=False,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Pick cutoff date"), close_button=True),
                    dbc.ModalBody([
                        html.Div(
                            style={"display": "flex", "gap": "8px", "alignItems": "center", "marginBottom": "8px"},
                            children=[
                                html.Div("Month", style={"width": "60px", "fontSize": "12px", "color": "#666"}),
                                dcc.Dropdown(
                                    id="ba_jump_month",
                                    options=MONTH_OPTS,
                                    value=date.today().month,
                                    style={"width": "140px"},
                                ),
                                dbc.Button("◀", id="ba_year_prev", size="sm", color="secondary", outline=True),
                                dbc.Button("▶", id="ba_year_next", size="sm", color="secondary", outline=True),
                                dbc.Badge(
                                    id="ba_year_badge",
                                    children=str(date.today().year),
                                    color="light",
                                    text_color="dark",
                                ),
                                dbc.Button(
                                    "Today",
                                    id="ba_today",
                                    size="sm",
                                    color="secondary",
                                    outline=True,
                                    style={"marginLeft": "auto"},
                                ),
                            ]
                        ),
                        dcc.DatePickerSingle(
                            id="ba_cutoff",
                            min_date_allowed=date(2000, 1, 1),
                            max_date_allowed=date(2050, 12, 31),
                            display_format="YYYY-MM-DD",
                        ),
                    ]),
                ],
            ),

            dbc.Row([
                dbc.Col(dbc.Button("Generate", id="ba_go", color="primary"), md="auto"),
                dbc.Col(dbc.Button("Add to report", id="ba_add", color="success", outline=True), md="auto"),
            ], className="g-2", style={"marginTop": "6px"}),

            html.Hr(),
            dcc.Graph(id="ba_graph", figure=go.Figure()),
            html.Div(id="ba_summary", style={"marginTop": "6px", "color": "#444"}),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="ba_close", color="secondary", outline=True)),
    ],
)

target_modal = dbc.Modal(
    id="target_modal",
    is_open=False,
    size="xl",
    scrollable=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Target compliance analysis")),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Date range"),
                    dbc.InputGroup([
                        dbc.Input(id="t_range_display", placeholder="Start → End Date", readonly=True),
                        dbc.Button("📅", id="t_cal_btn", color="secondary", outline=True, n_clicks=0),
                    ], size="md"),
                ], md=7),
                dbc.Col([
                    html.Label("Parameter"),
                    dcc.Dropdown(id="t_param", placeholder="Select column", clearable=False),
                ], md=3),
                dbc.Col([
                    html.Label("Target"),
                    dcc.Input(id="t_target", type="number", placeholder="e.g., 60", style={"width": "100%"}),
                ], md=1),
                dbc.Col([
                    html.Label("± Tolerance"),
                    dcc.Input(id="t_tol", type="number", placeholder="e.g., 5", style={"width": "100%"}),
                ], md=1),
            ], className="g-3"),

            # --- Calendar popup (small modal) ---
            dbc.Modal(
                id="t_cal_modal", is_open=False, size="sm", scrollable=False,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Pick a date range"), close_button=True),
                    dbc.ModalBody([
                        html.Div(
                            style={"display": "flex", "gap": "8px", "alignItems": "center", "marginBottom": "8px"},
                            children=[
                                html.Div("Month", style={"width": "60px", "fontSize": "12px", "color": "#666"}),
                                dcc.Dropdown(
                                    id="t_jump_month",
                                    options=MONTH_OPTS,
                                    value=date.today().month,
                                    style={"width": "140px"},
                                ),
                                dbc.Button("◀", id="t_year_prev", size="sm", color="secondary", outline=True),
                                dbc.Button("▶", id="t_year_next", size="sm", color="secondary", outline=True),
                                dbc.Badge(
                                    id="t_year_badge",
                                    children=str(date.today().year),
                                    color="light",
                                    text_color="dark",
                                ),
                                dbc.Button(
                                    "Today",
                                    id="t_today",
                                    size="sm",
                                    color="secondary",
                                    outline=True,
                                    style={"marginLeft": "auto"},
                                ),
                            ]
                        ),
                        dcc.DatePickerRange(
                            id="t_range",
                            minimum_nights=0,
                            min_date_allowed=date(2000, 1, 1),  # overwritten by callback
                            max_date_allowed=date(2050, 12, 31),
                            display_format="YYYY-MM-DD",
                        ),
                        html.Div(
                            dbc.Button("OK", id="t_cal_ok", color="primary", size="sm", className="mt-2"),
                            style={"textAlign": "right", "marginTop": "8px"},
                        ),
                    ]),
                ],
            ),

            dbc.Row([
                dbc.Col(dbc.Button("Generate", id="t_go", color="primary"), md="auto"),
                dbc.Col(dbc.Button("Add to report", id="t_add", color="success", outline=True), md="auto"),
            ], className="g-2", style={"marginTop": "8px"}),

            html.Hr(),
            dcc.Graph(id="t_graph", figure=go.Figure()),
            html.Div(id="t_kpis",
                     style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginTop": "8px"}),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="t_close", color="secondary", outline=True)),
    ],
)

# -----------------------------
# Page layout
# -----------------------------
layout = html.Div(
    className="main-container",
    children=[
        project_name_store,
        ba_year_store,
        t_year_store,
        report_items,

        html.Div(
            className="controls-bar",
            style={"display": "flex", "flexWrap": "wrap", "gap": "16px", "alignItems": "center", "marginBottom": "12px"},
            children=[
                html.Div([
                    html.H4("Thickener Trends", className="mb-0"),
                    html.Small(id="project-name-label", style={"color": "#666"}),
                ], style={"minWidth": "220px"}),

                html.Div(
                    children=[
                        html.Div("Primary variable", style={"fontSize": "12px", "color": "#555"}),
                        dcc.Dropdown(id="primary-variable", placeholder="Select main variable", clearable=False,
                                     style={"width": "250px"}),
                    ],
                    style={"flex": 1, "minWidth": "220px"},
                ),
                html.Div(
                    children=[dcc.Dropdown(id="secondary-variable", placeholder="Choose secondary variables", multi=True,
                                           style={"width": "250px"})],
                    style={"flex": 1, "minWidth": "220px"}
                ),
                html.Div(children=[
                    dcc.Dropdown(
                        id="time-period",
                        options=[
                            {"label": "15 min", "value": "15min"},
                            {"label": "30 min", "value": "30min"},
                            {"label": "1 Hour", "value": "1H"},
                            {"label": "4 Hours", "value": "4H"},
                            {"label": "12 Hours", "value": "12H"},
                            {"label": "1 Day", "value": "1D"},
                            {"label": "7 Days", "value": "7D"},
                        ],
                        placeholder="Resample",
                        style={"width": "160px"},
                    ),
                ]),
                html.Div(children=[
                    html.Div("Customer Input #1", style={"fontSize": "12px", "color": "#555"}),
                    dcc.Input(id="line1-value", type="number", placeholder="Y value",
                              style={"width": "100px", "marginRight": "6px"}),
                    dcc.Dropdown(
                        id="axis1-choice",
                        options=[{"label": "Primary", "value": "y1"}, {"label": "Secondary", "value": "y2"}],
                        placeholder="Axis",
                        style={"width": "110px"},
                    ),
                ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
                html.Div(children=[
                    html.Div("Customer Input #2", style={"fontSize": "12px", "color": "#555"}),
                    dcc.Input(id="line2-value", type="number", placeholder="Y value",
                              style={"width": "100px", "marginRight": "6px"}),
                    dcc.Dropdown(
                        id="axis2-choice",
                        options=[{"label": "Secondary", "value": "y2"}, {"label": "Primary", "value": "y1"}],
                        placeholder="Axis",
                        style={"width": "110px"},
                    ),
                ], style={"display": "flex", "alignItems": "center", "gap": "6px"}),
                html.Div(
                    children=[
                        dbc.Button("Plot graph", id="plot-button", color="primary", className="me-2"),
                        dbc.Button("Save", id="save-button", color="secondary", outline=True),
                        dbc.Button(
                            "Add snapshot to report",
                            id="ts_add",
                            color="success",
                            outline=True,
                            className="ms-2",
                        ),
                        dcc.Download(id="download-graph"),
                    ],
                    style={"marginLeft": "auto"},
                ),
            ],
        ),

        html.Div(
            style={"display": "flex", "gap": "16px", "alignItems": "flex-start"},
            children=[
                html.Div(
                    style={"flex": 3, "minWidth": 0},
                    children=[
                        dcc.Graph(id="time-series-graph", figure=go.Figure()),
                        html.Div(
                            style={"display": "flex", "gap": "8px", "justifyContent": "flex-end", "marginTop": "4px"},
                            children=[
                                dbc.Button("Before vs After", id="btn-ba", color="info", outline=True, size="sm"),
                                dbc.Button("Target compliance", id="btn-target", color="info", outline=True, size="sm"),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    style={"flex": 1.4, "minWidth": "260px"},
                    children=[
                        html.H5("Report builder"),
                        html.P(
                            "Use the buttons to send Before/After, Target compliance and time-series snapshots to this "
                            "report. Then export it as an HTML summary.",
                            style={"fontSize": "12px", "color": "#555"},
                        ),
                        html.Hr(),
                        html.Div(id="report-preview", style={"maxHeight": "520px", "overflowY": "auto"}),
                        dbc.Button(
                            "Download HTML report", id="btn-print-report",
                            color="primary", className="mt-3", size="sm",
                        ),
                        dcc.Download(id="download-report"),
                    ],
                ),
            ],
        ),

        ba_modal,
        target_modal,
    ],
)

# -----------------------------
# Populate dropdowns based on data
# -----------------------------
@dash.callback(
    Output("primary-variable", "options"),
    Output("secondary-variable", "options"),
    Output("t_param", "options"),
    Output("ba_param", "options"),
    Output("project-name-label", "children"),
    Input("stored-data", "data"),
    Input("project-name-store", "data"),
)
def fill_variable_options(stored, project_name):
    df, time_col = _get_df(stored)
    if df is None:
        return [], [], [], [], ""

    # numeric cols for Y
    numeric_cols = df.select_dtypes("number").columns.tolist()
    y_options = [{"label": c, "value": c} for c in numeric_cols]

    # For secondary: allow all numeric
    secondary_opts = y_options

    label = f"Project: {project_name}" if project_name else ""
    return y_options, secondary_opts, y_options, y_options, label

# -----------------------------
# Plot main time-series graph
# -----------------------------
@dash.callback(
    Output("time-series-graph", "figure"),
    Input("plot-button", "n_clicks"),
    State("stored-data", "data"),
    State("primary-variable", "value"),
    State("secondary-variable", "value"),
    State("time-period", "value"),
    State("line1-value", "value"),
    State("axis1-choice", "value"),
    State("line2-value", "value"),
    State("axis2-choice", "value"),
    prevent_initial_call=True,
)
def update_time_series(n_clicks, stored, primary, secondaries, resample_rule,
                       line1, axis1, line2, axis2):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure()

    if not primary:
        return go.Figure()

    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).sort_values(time_col)

    df_res = _resample(df, time_col, resample_rule)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_res[time_col],
        y=df_res[primary],
        mode="lines",
        name=primary,
        yaxis="y1",
    ))

    if secondaries:
        for col in secondaries:
            fig.add_trace(go.Scatter(
                x=df_res[time_col],
                y=df_res[col],
                mode="lines",
                name=col,
                yaxis="y2",
            ))

    shapes = []
    if line1 is not None and axis1 in ("y1", "y2"):
        shapes.append({
            "type": "line",
            "xref": "x",
            "yref": axis1,
            "x0": df_res[time_col].min(),
            "x1": df_res[time_col].max(),
            "y0": line1,
            "y1": line1,
            "line": {"dash": "dot", "width": 1},
        })
    if line2 is not None and axis2 in ("y1", "y2"):
        shapes.append({
            "type": "line",
            "xref": "x",
            "yref": axis2,
            "x0": df_res[time_col].min(),
            "x1": df_res[time_col].max(),
            "y0": line2,
            "y1": line2,
            "line": {"dash": "dot", "width": 1},
        })

    fig.update_layout(
        margin={"l": 60, "r": 30, "t": 40, "b": 40},
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.2},
        shapes=shapes,
        xaxis={"title": "Time"},
        yaxis={"title": primary},
        yaxis2={
            "title": "Secondary variables",
            "overlaying": "y",
            "side": "right",
        },
    )
    return fig

# -----------------------------
# Save time-series graph as PNG
# -----------------------------
@dash.callback(
    Output("download-graph", "data"),
    Input("save-button", "n_clicks"),
    State("time-series-graph", "figure"),
    prevent_initial_call=True,
)
def download_graph(n, fig_dict):
    if not fig_dict:
        return no_update
    fig = go.Figure(fig_dict)
    img_b64 = _fig_to_base64_png(fig)
    if not img_b64:
        return no_update
    return dict(
        content=f'<img src="{img_b64}" alt="Thickener trend">',
        filename="thickener_trend.html",
        type="text/html",
    )

# -----------------------------
# Before vs After modal behaviour
# -----------------------------
@dash.callback(
    Output("ba_modal", "is_open"),
    Input("btn-ba", "n_clicks"),
    Input("ba_close", "n_clicks"),
    State("ba_modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_ba_modal(open_click, close_click, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx in ("btn-ba", "ba_close"):
        return not is_open
    return is_open

@dash.callback(
    Output("ba_year_store", "data"),
    Output("ba_year_badge", "children"),
    Input("ba_year_prev", "n_clicks"),
    Input("ba_year_next", "n_clicks"),
    Input("ba_today", "n_clicks"),
    State("ba_year_store", "data"),
    prevent_initial_call=True,
)
def step_ba_year(prev, nxt, today, current):
    current = current or date.today().year
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "ba_year_prev":
        current -= 1
    elif ctx == "ba_year_next":
        current += 1
    elif ctx == "ba_today":
        current = date.today().year
    return current, str(current)

@dash.callback(
    Output("ba_cutoff", "initial_visible_month"),
    Input("ba_jump_month", "value"),
    Input("ba_year_store", "data"),
    Input("ba_today", "n_clicks"),
    prevent_initial_call=True,
)
def jump_ba_month(month, year, today):
    if dash.callback_context.triggered[0]["prop_id"].startswith("ba_today"):
        return date.today().replace(day=1)
    month = month or date.today().month
    year = year or date.today().year
    return date(int(year), int(month), 1)

@dash.callback(
    Output("ba_cal_modal", "is_open"),
    Output("ba_cutoff_display", "value"),
    Input("ba_cal_btn", "n_clicks"),      # botón 📅
    Input("ba_cutoff", "date"),           # selección calendario
    State("ba_cal_modal", "is_open"),
    prevent_initial_call=True,
)
def ba_modal_and_display(btn, picked_date, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "ba_cal_btn":
        return (not is_open), no_update
    if ctx == "ba_cutoff" and picked_date:
        try:
            val = pd.to_datetime(picked_date).date().isoformat()
        except Exception:
            val = picked_date
        return False, val
    return is_open, no_update

# -----------------------------
# Calendar (Target) — year jump & modal unified
# -----------------------------
@dash.callback(
    Output("t_year_store", "data"),
    Output("t_year_badge", "children"),
    Input("t_year_prev", "n_clicks"),
    Input("t_year_next", "n_clicks"),
    Input("t_today", "n_clicks"),
    State("t_year_store", "data"),
    prevent_initial_call=True,
)
def step_t_year(prev, nxt, today, current):
    current = current or date.today().year
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "t_year_prev":
        current -= 1
    elif ctx == "t_year_next":
        current += 1
    elif ctx == "t_today":
        current = date.today().year
    return current, str(current)

@dash.callback(
    Output("t_range", "initial_visible_month"),
    Input("t_jump_month", "value"),
    Input("t_year_store", "data"),
    Input("t_today", "n_clicks"),
    prevent_initial_call=True,
)
def jump_t_month(month, year, today):
    if dash.callback_context.triggered[0]["prop_id"].startswith("t_today"):
        return date.today().replace(day=1)
    month = month or date.today().month
    year = year or date.today().year
    return date(int(year), int(month), 1)

@dash.callback(
    Output("t_cal_modal", "is_open"),
    Output("t_range_display", "value"),
    Input("t_cal_btn", "n_clicks"),       # abre/cierra el modal
    Input("t_cal_ok", "n_clicks"),        # confirma selección
    State("t_cal_modal", "is_open"),
    State("t_range", "start_date"),
    State("t_range", "end_date"),
    prevent_initial_call=True,
)
def t_modal_and_display(btn, ok_clicks, is_open, start, end):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # Botón calendario: solo alterna abrir/cerrar
    if trigger == "t_cal_btn":
        return (not is_open), no_update

    # Botón OK: cierra modal y actualiza texto con el rango
    if trigger == "t_cal_ok" and start and end:
        try:
            s = pd.to_datetime(start).date().isoformat()
            e = pd.to_datetime(end).date().isoformat()
        except Exception:
            s, e = start, end
        return False, f"{s} → {e}"

    return is_open, no_update

# -----------------------------
# Target modal toggle
# -----------------------------
@dash.callback(
    Output("target_modal", "is_open"),
    Input("btn-target", "n_clicks"),
    Input("t_close", "n_clicks"),
    State("target_modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_target_modal(open_click, close_click, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx in ("btn-target", "t_close"):
        return not is_open
    return is_open

# -----------------------------
# Before vs After analysis
# -----------------------------
@dash.callback(
    Output("ba_graph", "figure"),
    Output("ba_summary", "children"),
    Input("ba_go", "n_clicks"),
    State("stored-data", "data"),
    State("ba_param", "value"),
    State("ba_cutoff", "date"),
    State("ba_window", "value"),
    prevent_initial_call=True,
)
def compute_before_after(n_clicks, stored, param, cutoff, window):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure(), "No data."

    if not (param and cutoff and window):
        return go.Figure(), "Please select a parameter, cutoff date and window."

    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    cutoff = pd.to_datetime(cutoff)

    delta = pd.Timedelta(days=int(window))
    before_mask = (df[time_col] >= cutoff - delta) & (df[time_col] < cutoff)
    after_mask = (df[time_col] >= cutoff) & (df[time_col] <= cutoff + delta)

    before = df.loc[before_mask, param]
    after = df.loc[after_mask, param]

    fig = go.Figure()
    fig.add_box(y=before, name="Before")
    fig.add_box(y=after, name="After")
    fig.update_layout(
        yaxis_title=param,
        title=f"Before vs After — {param}",
        margin={"l": 60, "r": 20, "t": 40, "b": 40},
    )

    if before.empty or after.empty:
        msg = "Not enough data before or after the cutoff date."
    else:
        msg = (
            f"Before (n={len(before)}): mean={before.mean():.2f}, median={before.median():.2f} — "
            f"After (n={len(after)}): mean={after.mean():.2f}, median={after.median():.2f}"
        )

    return fig, msg

# -----------------------------
# Target compliance analysis
# -----------------------------
@dash.callback(
    Output("t_graph", "figure"),
    Output("t_kpis", "children"),
    Input("t_go", "n_clicks"),
    State("stored-data", "data"),
    State("t_param", "value"),
    State("t_target", "value"),
    State("t_tol", "value"),
    State("t_range", "start_date"),
    State("t_range", "end_date"),
    prevent_initial_call=True,
)
def compute_target_compliance(n_clicks, stored, param, target, tol, start, end):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure(), []

    if not (param and target is not None and tol is not None and start and end):
        return go.Figure(), []

    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    mask = (df[time_col] >= start) & (df[time_col] <= end)
    df = df.loc[mask]
    if df.empty:
        return go.Figure(), []

    low = target - tol
    high = target + tol

    below = df[df[param] < low]
    within = df[(df[param] >= low) & (df[param] <= high)]
    above = df[df[param] > high]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[time_col],
        y=df[param],
        mode="lines",
        name=param,
    ))
    fig.add_hrect(y0=low, y1=high, fillcolor="green", opacity=0.15, line_width=0)
    fig.add_hline(y=target, line_dash="dash", annotation_text="Target", annotation_position="top left")
    fig.update_layout(
        title=f"Target compliance — {param}",
        xaxis_title="Time",
        yaxis_title=param,
        margin={"l": 60, "r": 20, "t": 40, "b": 40},
        hovermode="x unified",
    )

    total = len(df)
    pct_below = 100 * len(below) / total
    pct_within = 100 * len(within) / total
    pct_above = 100 * len(above) / total

    def kpi(label, value, color):
        return html.Div(
            style={"padding": "6px 10px", "borderRadius": "6px", "backgroundColor": "#f7f7f7", "minWidth": "120px"},
            children=[
                html.Div(label, style={"fontSize": "11px", "color": "#555"}),
                html.Div(f"{value:.1f} %", style={"fontWeight": "600", "color": color}),
            ],
        )

    kpis = [
        kpi("Below", pct_below, "#d9534f"),
        kpi("Within target", pct_within, "#5cb85c"),
        kpi("Above", pct_above, "#f0ad4e"),
    ]
    return fig, kpis

# -----------------------------
# Add to report
# -----------------------------
@dash.callback(
    Output("report-items", "data"),
    Input("ba_add", "n_clicks"),
    Input("t_add", "n_clicks"),
    Input("ts_add", "n_clicks"),
    State("report-items", "data"),
    # Before/After
    State("ba_graph", "figure"),
    State("ba_summary", "children"),
    State("ba_param", "value"),
    State("ba_cutoff", "date"),
    # Target compliance
    State("t_graph", "figure"),
    State("t_param", "value"),
    State("t_target", "value"),
    State("t_tol", "value"),
    State("t_range", "start_date"),
    State("t_range", "end_date"),
    State("stored-data", "data"),
    # Time-series snapshot
    State("time-series-graph", "figure"),
    State("primary-variable", "value"),
    State("secondary-variable", "value"),
    State("time-period", "value"),
    State("line1-value", "value"),
    State("line2-value", "value"),
    prevent_initial_call=True,
)
def add_to_report(
    ba_clicks,
    t_clicks,
    ts_clicks,
    items,
    ba_fig,
    ba_summary,
    ba_param,
    ba_cutoff,
    t_fig,
    t_param,
    t_target,
    t_tol,
    t_start,
    t_end,
    stored,
    ts_fig,
    ts_primary,
    ts_secondary,
    ts_period,
    ts_line1,
    ts_line2,
):
    items = items or []
    ctx = dash.callback_context
    if not ctx.triggered:
        return items

    trig = ctx.triggered[0]["prop_id"].split(".")[0]

    # -------------------------
    # Before vs After section
    # -------------------------
    if trig == "ba_add":
        if not ba_fig or not ba_param or not ba_cutoff:
            return items
        fig = go.Figure(ba_fig)
        img_b64 = _fig_to_base64_png(fig)
        entry = {
            "type": "before_after",
            "title": f"Before vs After — {ba_param}",
            "meta": f"Cutoff: {ba_cutoff}",
            "summary": ba_summary or "",
        }
        if img_b64:
            entry["image"] = img_b64
        else:
            entry["html"] = _fig_to_inline_html(fig)
        return items + [entry]

    # -------------------------
    # Target compliance section
    # -------------------------
    if trig == "t_add":
        if not (t_fig and t_param and t_target is not None and t_tol is not None and t_start and t_end):
            return items
        df, time_col = _get_df(stored)
        if df is None:
            return items
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        try:
            mask = (df[time_col] >= pd.to_datetime(t_start)) & (df[time_col] <= pd.to_datetime(t_end))
            dff = df.loc[mask]
        except Exception:
            dff = df.copy()
        if dff.empty:
            return items
        low, high = t_target - t_tol, t_target + t_tol
        below = int((dff[t_param] < low).sum())
        within = int(((dff[t_param] >= low) & (dff[t_param] <= high)).sum())
        above = int((dff[t_param] > high).sum())
        pct_in = 100 * within / len(dff)
        summary = (
            f"Window: {t_start} to {t_end} | Target: {t_target} ±{t_tol}  →  "
            f"Below={below}, Within={within}, Above={above}  ({pct_in:.1f}% within)"
        )

        fig = go.Figure(t_fig)
        img_b64 = _fig_to_base64_png(fig)
        entry = {
            "type": "target",
            "title": f"Target compliance — {t_param}",
            "meta": summary,
            "summary": "",
        }
        if img_b64:
            entry["image"] = img_b64
        else:
            entry["html"] = _fig_to_inline_html(fig)
        return items + [entry]

    # -------------------------
    # Time-series snapshot
    # -------------------------
    if trig == "ts_add":
        if not ts_fig:
            return items

        fig = go.Figure(ts_fig)
        img_b64 = _fig_to_base64_png(fig)

        meta_parts = []
        if ts_primary:
            meta_parts.append(f"Primary: {ts_primary}")
        if ts_secondary:
            meta_parts.append(f"Secondary: {ts_secondary}")
        if ts_period:
            meta_parts.append(f"Period: {ts_period}")
        if ts_line1 is not None:
            meta_parts.append(f"Customer line 1: {ts_line1}")
        if ts_line2 is not None:
            meta_parts.append(f"Customer line 2: {ts_line2}")
        meta = " | ".join(meta_parts)

        entry = {
            "type": "snapshot",
            "title": "Time series snapshot",
            "meta": meta,
            "summary": "",
        }
        if img_b64:
            entry["image"] = img_b64
        else:
            entry["html"] = _fig_to_inline_html(fig)
        return items + [entry]

    return items

# -----------------------------
# Print report (HTML)
# -----------------------------
@dash.callback(
    Output("download-report", "data"),
    Input("btn-print-report", "n_clicks"),
    State("report-items", "data"),
    State("project-name-store", "data"),
    prevent_initial_call=True,
)
def print_report(_, items, project_name):
    items = items or []
    if not items:
        return no_update
    project_name = project_name or "Thickener DataWeb"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    parts = [
        "<html><head><meta charset='utf-8'><title>Thickener report</title>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }",
        ".item { border: 1px solid #ddd; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; }",
        ".item h3 { margin: 0 0 4px 0; font-size: 16px; }",
        ".meta { font-size: 11px; color: #666; margin-bottom: 6px; }",
        ".summary { font-size: 13px; color: #333; }",
        "</style>",
        "</head><body>",
        f"<h1>Thickener Report — {project_name}</h1>",
        f"<p><em>Generated: {now}</em></p>",
    ]

    for it in items:
        parts.append("<div class='item'>")
        parts.append(f"<h3>{it.get('title','')}</h3>")
        meta = it.get("meta")
        if meta:
            parts.append(f"<div class='meta'>{meta}</div>")
        summary = it.get("summary")
        if summary:
            parts.append(f"<div class='summary'>{summary}</div>")
        img = it.get("image")
        html_block = it.get("html")
        if img:
            parts.append(f"<div><img src='{img}' style='max-width:100%; border-radius:4px;'/></div>")
        elif html_block:
            parts.append("<div>" + html_block + "</div>")
        parts.append("</div>")

    parts.append("</body></html>")
    html_report = "\n".join(parts)
    return dict(
        content=html_report,
        filename="thickener_report.html",
        type="text/html",
    )
