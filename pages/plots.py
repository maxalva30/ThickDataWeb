# pages/plots.py
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.io as pio
import numpy as np
import pandas as pd
from datetime import datetime, date
import base64

dash.register_page(__name__, path="/plots", name="Plots")

# -----------------------------
# Helpers
# -----------------------------
MONTH_NAMES = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
MONTH_OPTS = [{"label":m,"value":i} for i,m in enumerate(MONTH_NAMES, start=1)]

def _get_df(stored):
    if not stored:
        return None, "No data loaded. Go back and upload an Excel file."
    df = pd.DataFrame(stored)
    if df.empty:
        return None, "Empty DataFrame."
    time_col = df.columns[0]
    try:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    except Exception:
        return None, f"Failed to parse first column ({time_col}) as datetime."
    if df[time_col].isna().all():
        return None, f"First column ({time_col}) has no valid datetime."
    return df, time_col

def _resample(dff, time_col, rule):
    if not rule:
        return dff
    dff = dff.set_index(time_col)
    dff = dff.resample(rule).mean(numeric_only=True)
    dff = dff.reset_index()
    return dff

def _kpi(label, val):
    return dbc.Badge(f"{label}: {val}", color="light", text_color="dark", className="p-2")

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
# Stores
# -----------------------------
report_store = dcc.Store(id="report-items", data=[])
ba_year_store = dcc.Store(id="ba_year_store", data=date.today().year)
t_year_store  = dcc.Store(id="t_year_store",  data=date.today().year)

# -----------------------------
# Toolbar
# -----------------------------
stats_toolbar = html.Div(
    style={"margin":"6px 0 14px","display":"flex","gap":"10px","alignItems":"center"},
    children=[
        dbc.ButtonGroup(
            [
                dbc.Button("Before vs After", id="btn-before-after", color="secondary", outline=True),
                dbc.Button("Target compliance", id="btn-target", color="primary"),
            ],
            size="lg",
        ),
        html.Div(style={"flex":1}),
        dbc.Button("Print report", id="btn-print-report", color="dark", outline=True),
        dcc.Download(id="download-report"),
    ],
)

# -----------------------------
# Modals (Analysis)
# -----------------------------
before_after_modal = dbc.Modal(
    id="modal-before-after", is_open=False, size="xl", scrollable=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Before vs After — Boxplot")),
        dbc.ModalBody([
            # 🔹 NUEVO: rango de fechas disponible en el archivo
            html.Div(
                [
                    html.Div(
                        "Current available time",
                        style={
                            "textAlign": "center",
                            "fontWeight": "bold",
                            "marginBottom": "4px",
                        },
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div("From", style={"fontSize": "12px"}),
                                    dbc.Input(
                                        id="ba_from_display",
                                        readonly=True,
                                        size="sm",
                                    ),
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    html.Div("To", style={"fontSize": "12px"}),
                                    dbc.Input(
                                        id="ba_to_display",
                                        readonly=True,
                                        size="sm",
                                    ),
                                ],
                                md=6,
                            ),
                        ],
                        className="g-1",
                        style={"marginBottom": "10px"},
                    ),
                ]
            ),
            # --- FIN bloque rango disponible ---

            dbc.Row([
                dbc.Col([
                    html.Label("Cut-off date"),
                    dbc.InputGroup([
                        dbc.Input(id="ba_cutoff_display", placeholder="Pick a date", readonly=True),
                        dbc.Button("📅", id="ba_cal_btn", color="secondary", outline=True, n_clicks=0),
                    ], size="md"),
                ], md=6),
                dbc.Col([
                    html.Label("Parameter"),
                    dcc.Dropdown(id="ba_param", placeholder="Select column", clearable=False),
                ], md=6),
            ], className="g-3"),


            # --- Calendar popup (small modal) ---
        dbc.Modal(
    id="ba_cal_modal", is_open=False, size="sm", scrollable=False,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Pick a date"), close_button=True),
        dbc.ModalBody([
            dcc.DatePickerSingle(
                id="ba_cutoff",
                display_format="YYYY-MM-DD",
            ),
        ]),
    ],
),

            dbc.Row([
                dbc.Col(dbc.Button("Generate", id="ba_go", color="primary"), md="auto"),
                dbc.Col(dbc.Button("Add to report", id="ba_add", color="success", outline=True), md="auto"),
            ], className="g-2", style={"marginTop":"6px"}),

            html.Hr(),
            dcc.Graph(id="ba_graph", figure=go.Figure()),
            html.Div(id="ba_summary", style={"marginTop":"6px","color":"#444"}),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="ba_close", color="secondary", outline=True)),
    ],
)

target_modal = dbc.Modal(
    id="modal-target", is_open=False, size="xl", scrollable=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Target compliance — Time window")),
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
                    dcc.Input(id="t_target", type="number", placeholder="e.g., 60", style={"width":"100%"}),
                ], md=1),
                dbc.Col([
                    html.Label("± Tolerance"),
                    dcc.Input(id="t_tol", type="number", placeholder="e.g., 5", style={"width":"100%"}),
                ], md=1),
            ], className="g-3"),

            # --- Calendar popup (small modal) ---
            dbc.Modal(
                id="t_cal_modal", is_open=False, size="sm", scrollable=False,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Pick a date range"), close_button=True),
                    dbc.ModalBody([
                        html.Div(
                            style={"display":"flex","gap":"8px","alignItems":"center","marginBottom":"8px"},
                            children=[
                                html.Div("Month", style={"width":"60px","fontSize":"12px","color":"#666"}),
                                dcc.Dropdown(id="t_jump_month", options=MONTH_OPTS,
                                             value=date.today().month, style={"width":"140px"}),
                                dbc.Button("◀", id="t_year_prev", size="sm", color="secondary", outline=True),
                                dbc.Button("▶", id="t_year_next", size="sm", color="secondary", outline=True),
                                dbc.Badge(id="t_year_badge", children=str(date.today().year),
                                          color="light", text_color="dark"),
                                dbc.Button("Today", id="t_today", size="sm", color="secondary", outline=True,
                                           style={"marginLeft":"auto"}),
                            ]
                        ),
                        dcc.DatePickerRange(
                            id="t_range",
                            minimum_nights=0,
                            min_date_allowed=date(2000,1,1),
                            max_date_allowed=date(2050,12,31),
                            display_format="YYYY-MM-DD",
                        ),
                    ]),
                ],
            ),

            dbc.Row([
                dbc.Col(dbc.Button("Generate", id="t_go", color="primary"), md="auto"),
                dbc.Col(dbc.Button("Add to report", id="t_add", color="success", outline=True), md="auto"),
            ], className="g-2", style={"marginTop":"8px"}),

            html.Hr(),
            dcc.Graph(id="t_graph", figure=go.Figure()),
            html.Div(id="t_kpis", style={"display":"flex","gap":"16px","flexWrap":"wrap","marginTop":"8px"}),
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
        html.Div(
            className="controls-bar",
            style={"display":"flex","flexWrap":"wrap","gap":"16px","alignItems":"center","marginBottom":"12px"},
            children=[
                html.Div(
                    children=[dcc.Dropdown(id="primary-variable", placeholder="Choose primary variables", multi=True,
                                           style={"width":"350px"})],
                    style={"flex":1,"minWidth":"300px"}
                ),
                html.Div(
                    children=[dcc.Dropdown(id="secondary-variable", placeholder="Choose secondary variables", multi=True,
                                           style={"width":"250px"})],
                    style={"flex":1,"minWidth":"220px"}
                ),
                html.Div(children=[
                    dcc.Dropdown(
                        id="time-period",
                        options=[
                            {"label":"15 min","value":"15min"},
                            {"label":"30 min","value":"30min"},
                            {"label":"1 Hour","value":"1H"},
                            {"label":"4 Hours","value":"4H"},
                            {"label":"12 Hours","value":"12H"},
                            {"label":"1 Day","value":"1D"},
                            {"label":"7 Days","value":"7D"},
                        ],
                        placeholder="Resample",
                        style={"width":"160px"},
                    ),
                ]),
                html.Div(children=[
                    html.Div("Customer Input #1", style={"fontSize":"12px","color":"#555"}),
                    dcc.Input(id="line1-value", type="number", placeholder="Y value",
                              style={"width":"100px","marginRight":"6px"}),
                    dcc.Dropdown(
                        id="axis1-choice",
                        options=[{"label":"Primary","value":"y1"},{"label":"Secondary","value":"y2"}],
                        placeholder="Axis",
                        style={"width":"110px"},
                    ),
                ], style={"display":"flex","alignItems":"center","gap":"6px"}),
                html.Div(children=[
                    html.Div("Customer Input #2", style={"fontSize":"12px","color":"#555"}),
                    dcc.Input(id="line2-value", type="number", placeholder="Y value",
                              style={"width":"100px","marginRight":"6px"}),
                    dcc.Dropdown(
                        id="axis2-choice",
                        options=[{"label":"Secondary","value":"y2"},{"label":"Primary","value":"y1"}],
                        placeholder="Axis",
                        style={"width":"110px"},
                    ),
                ], style={"display":"flex","alignItems":"center","gap":"6px"}),
                html.Div(children=[
                    dbc.Button("Plot graph", id="plot-button", color="primary", className="me-2"),
                    dbc.Button("Save", id="save-button", color="secondary", outline=True),
                    dcc.Download(id="download-graph"),
                ], style={"marginLeft":"auto"}),
            ],
        ),

        stats_toolbar,
        before_after_modal,
        target_modal,
        report_store,
        ba_year_store,
        t_year_store,

        html.Hr(),
        html.H3("Time Series Analysis"),
        dcc.Graph(id="time-series-graph", figure=go.Figure()),
    ],
)

# -----------------------------
# Populate variable dropdowns
# -----------------------------
@dash.callback(
    Output("primary-variable", "options"),
    Output("secondary-variable", "options"),
    Input("time-series-graph", "id"),
    State("stored-data", "data"),
)
def fill_variable_options(_, stored):
    df, time_col = _get_df(stored)
    if df is None:
        return [], []
    num_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
    opts = [{"label": c, "value": c} for c in num_cols]
    return opts, opts

# -----------------------------
# Time series chart
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
def update_time_series(_, stored, primaries, secondaries, period, line1_val, axis1, line2_val, axis2):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure()

    primaries = primaries or []
    secondaries = secondaries or []

    dff = _resample(df.copy(), time_col, period) if period else df.copy()
    fig = go.Figure()

    if len(secondaries) > 0:
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", title="Secondary Y axis"))

    for col in primaries:
        fig.add_trace(go.Scatter(x=dff[time_col], y=dff[col], mode="lines", name=col, yaxis="y1"))
    for col in secondaries:
        fig.add_trace(go.Scatter(x=dff[time_col], y=dff[col], mode="lines", name=col, yaxis="y2"))

    def add_hline(value, axis, color):
        if value is None or axis not in ["y1", "y2"]:
            return
        fig.add_shape(
            type="line",
            x0=dff[time_col].min(), x1=dff[time_col].max(),
            y0=value, y1=value,
            line=dict(color=color, dash="dash"),
            xref="x", yref="y" if axis == "y1" else "y2",
        )
    add_hline(line1_val, axis1, "red")
    add_hline(line2_val, axis2, "blue")

    fig.update_layout(
        template="plotly_white",
        title="Time Series Analysis",
        xaxis_title="Time",
        yaxis_title="Primary Y axis",
        height=650,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

# -----------------------------
# Save as HTML
# -----------------------------
@dash.callback(
    Output("download-graph", "data"),
    Input("save-button", "n_clicks"),
    State("time-series-graph", "figure"),
    State("project-name-store", "data"),
    prevent_initial_call=True,
)
def save_graph_as_html(_, figure, project_name):
    project_name = project_name or "time_series_chart"
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return dcc.send_string(pio.to_html(figure), f"{project_name}_{ts}.html")

# -----------------------------
# Open analysis modals & options
# -----------------------------
@dash.callback(
    Output("modal-before-after", "is_open"),
    Input("btn-before-after", "n_clicks"),
    Input("ba_close", "n_clicks"),
    State("modal-before-after", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal_ba(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

@dash.callback(
    Output("modal-target", "is_open"),
    Input("btn-target", "n_clicks"),
    Input("t_close", "n_clicks"),
    State("modal-target", "is_open"),
    prevent_initial_call=True,
)
def toggle_modal_t(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

@dash.callback(
    Output("ba_param", "options"),
    Output("t_param", "options"),
    Input("time-series-graph", "figure"),
    State("stored-data", "data"),
)
def populate_modal_options(_, stored):
    df, time_col = _get_df(stored)
    if df is None:
        return [], []
    num_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
    opts = [{"label": c, "value": c} for c in num_cols]
    return opts, opts
@dash.callback(
    Output("ba_from_display", "value"),
    Output("ba_to_display", "value"),
    Output("ba_cutoff", "min_date_allowed"),
    Output("ba_cutoff", "max_date_allowed"),
    Input("stored-data", "data"),
)
def update_ba_date_range(stored):
    """
    Muestra el rango de fechas disponible y limita el calendario.
    """
    df, time_col = _get_df(stored)
    if df is None or time_col is None:
        today = date.today()
        return "", "", today.replace(year=today.year - 1), today

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    if df.empty:
        today = date.today()
        return "", "", today.replace(year=today.year - 1), today

    d_min = df[time_col].min().date()
    d_max = df[time_col].max().date()
    return d_min.isoformat(), d_max.isoformat(), d_min, d_max
# -----------------------------
# Calendar (BA) — year jump & modal unified
# -----------------------------
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
    Input("stored-data", "data"),
)
def set_initial_month(stored):
    """
    Al cargar el archivo, el calendario abre en el mes donde empieza la data.
    """
    df, time_col = _get_df(stored)
    if df is not None and time_col is not None:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
        df = df.dropna(subset=[time_col])
        if not df.empty:
            d_min = df[time_col].min().date()
            return d_min.replace(day=1)

    # fallback por si acaso
    return date.today().replace(day=1)


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
    year  = year  or date.today().year
    return date(int(year), int(month), 1)

@dash.callback(
    Output("t_cal_modal", "is_open"),
    Output("t_range_display", "value"),
    Input("t_cal_btn", "n_clicks"),       # botón 📅
    Input("t_range", "start_date"),
    Input("t_range", "end_date"),
    State("t_cal_modal", "is_open"),
    prevent_initial_call=True,
)
def t_modal_and_display(btn, start, end, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "t_cal_btn":
        return (not is_open), no_update
    if (ctx in {"t_range.start_date", "t_range.end_date"}) and start and end:
        try:
            s = pd.to_datetime(start).date().isoformat()
            e = pd.to_datetime(end).date().isoformat()
        except Exception:
            s, e = start, end
        return False, f"{s} → {e}"
    return is_open, no_update

# -----------------------------
# Before vs After generate
# -----------------------------
@dash.callback(
    Output("ba_graph", "figure"),
    Output("ba_summary", "children"),
    Input("ba_go", "n_clicks"),
    State("ba_cutoff", "date"),
    State("ba_param", "value"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def generate_before_after(_, cutoff_date, param, stored):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure(), "No valid data."
    if not cutoff_date or not param:
        return go.Figure(), "Select cut-off date and parameter."

    cutoff = pd.to_datetime(cutoff_date)
    before = df[df[time_col] < cutoff]
    after  = df[df[time_col] >= cutoff]
    if before.empty or after.empty:
        return go.Figure(), "One side is empty with that date. Try another."

    fig = go.Figure()
    fig.add_trace(go.Box(y=before[param], name="Before", boxmean="sd"))
    fig.add_trace(go.Box(y=after[param],  name="After",  boxmean="sd"))
    fig.update_layout(template="plotly_white", yaxis_title=param, height=550)

    def stats(x):
        return {
            "n": len(x),
            "mean": float(np.nanmean(x)),
            "p50": float(np.nanmedian(x)),
            "p5":  float(np.nanpercentile(x, 5)),
            "p95": float(np.nanpercentile(x, 95)),
        }
    b, a = stats(before[param]), stats(after[param])
    txt = (f"Before (n={b['n']}): mean={b['mean']:.2f}, p50={b['p50']:.2f}, "
           f"p5–p95=({b['p5']:.2f}–{b['p95']:.2f})  |  "
           f"After (n={a['n']}): mean={a['mean']:.2f}, p50={a['p50']:.2f}, "
           f"p5–p95=({a['p5']:.2f}–{a['p95']:.2f})")
    return fig, txt

# -----------------------------
# Target generate
# -----------------------------
@dash.callback(
    Output("t_graph", "figure"),
    Output("t_kpis", "children"),
    Input("t_go", "n_clicks"),
    State("t_range", "start_date"),
    State("t_range", "end_date"),
    State("t_param", "value"),
    State("t_target", "value"),
    State("t_tol", "value"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def generate_target(_, start, end, param, target, tol, stored):
    df, time_col = _get_df(stored)
    if df is None:
        return go.Figure(), [_kpi("Error","No data")]
    if not (start and end and param and target is not None and tol is not None):
        return go.Figure(), [_kpi("Info","Complete all fields")]

    start = pd.to_datetime(start)
    end   = pd.to_datetime(end) + pd.Timedelta(days=1)
    dff = df[(df[time_col] >= start) & (df[time_col] < end)].copy()
    if dff.empty:
        return go.Figure(), [_kpi("Info","No data in the selected window")]

    low, high = target - tol, target + tol
    below  = int((dff[param] < low).sum())
    within = int(((dff[param] >= low) & (dff[param] <= high)).sum())
    above  = int((dff[param] > high).sum())
    pct_in = 100 * within / len(dff)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dff[time_col], y=dff[param], mode="lines", name=param))
    fig.add_hline(y=target, line_color="blue", line_dash="dash",
                  annotation_text="Target", annotation_position="top left")
    fig.add_hrect(y0=low, y1=high, line_width=0, fillcolor="LightBlue", opacity=0.2,
                  annotation_text=f"±{tol}", annotation_position="right")
    fig.update_layout(template="plotly_white", yaxis_title=param, xaxis_title="Time", height=550)

    kpis = [
        _kpi("% within target", f"{pct_in:.1f}%"),
        _kpi("Below", f"{below}"),
        _kpi("Within", f"{within}"),
        _kpi("Above", f"{above}"),
        _kpi("Mean", f"{np.nanmean(dff[param]):.2f}"),
        _kpi("Median", f"{np.nanmedian(dff[param]):.2f}"),
        _kpi("Samples", f"{len(dff)}"),
    ]
    return fig, kpis

# -----------------------------
# Add to report
# -----------------------------
@dash.callback(
    Output("report-items", "data"),
    Input("ba_add", "n_clicks"),
    Input("t_add", "n_clicks"),
    State("report-items", "data"),
    # BA
    State("ba_graph", "figure"),
    State("ba_summary", "children"),
    State("ba_param", "value"),
    State("ba_cutoff", "date"),
    # Target
    State("t_graph", "figure"),
    State("t_param", "value"),
    State("t_target", "value"),
    State("t_tol", "value"),
    State("t_range", "start_date"),
    State("t_range", "end_date"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def add_to_report(ba_clicks, t_clicks, items,
                  ba_fig, ba_summary, ba_param, ba_cutoff,
                  t_fig, t_param, t_target, t_tol, t_start, t_end, stored):
    items = items or []
    ctx = dash.callback_context
    if not ctx.triggered:
        return items
    trig = ctx.triggered[0]["prop_id"].split(".")[0]

    if trig == "ba_add":
        if not ba_fig or not ba_param or not ba_cutoff:
            return items
        fig = go.Figure(ba_fig)
        img_b64 = _fig_to_base64_png(fig)
        entry = {
            "type": "before_after",
            "title": f"Before vs After — {ba_param}",
            "meta": f"Cut-off: {ba_cutoff}",
            "summary": ba_summary or "",
        }
        if img_b64:
            entry["image"] = img_b64
        else:
            entry["html"] = _fig_to_inline_html(fig)
        return items + [entry]

    if trig == "t_add":
        if not t_fig or not t_param or t_target is None or t_tol is None or not (t_start and t_end):
            return items
        df, time_col = _get_df(stored)
        if df is None:
            return items
        start_dt = pd.to_datetime(t_start)
        end_dt   = pd.to_datetime(t_end) + pd.Timedelta(days=1)
        dff = df[(df[time_col] >= start_dt) & (df[time_col] < end_dt)].copy()
        if dff.empty:
            return items
        low, high = t_target - t_tol, t_target + t_tol
        below  = int((dff[t_param] < low).sum())
        within = int(((dff[t_param] >= low) & (dff[t_param] <= high)).sum())
        above  = int((dff[t_param] > high).sum())
        pct_in = 100 * within / len(dff)
        summary = (f"Window: {t_start} to {t_end} | Target: {t_target} ±{t_tol}  →  "
                   f"Below={below}, Within={within}, Above={above}  ({pct_in:.1f}% within)")

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

    needs_plotly = any("html" in it for it in items)

    parts = [
        "<html><head><meta charset='utf-8' /><title>Report</title>",
        "<style>body{font-family:Arial,Helvetica,sans-serif;margin:24px;} ",
        "h1{margin:0 0 8px 0;} .meta{color:#666;margin-bottom:20px;} ",
        ".card{border:1px solid #ddd;border-radius:10px;padding:14px;margin:14px 0;} ",
        ".img{width:100%;max-width:1200px;border:1px solid #eee;border-radius:8px;} ",
        ".ttl{font-weight:700;font-size:18px;margin-bottom:4px;} ",
        ".sum{color:#333;margin-top:6px;}</style>",
    ]
    if needs_plotly:
        parts.append("<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>")
    parts.append("</head><body>")
    parts.append(f"<h1>{project_name} — Analysis Report</h1>")
    parts.append(f"<div class='meta'>Generated: {now} | Items: {len(items)}</div>")

    for i, it in enumerate(items, start=1):
        parts.append("<div class='card'>")
        parts.append(f"<div class='ttl'>{i}. {it.get('title','')}</div>")
        if it.get("meta"): parts.append(f"<div class='meta'>{it['meta']}</div>")
        if it.get("image"):
            parts.append(f"<img class='img' src='{it['image']}' />")
        elif it.get("html"):
            parts.append(it["html"])
        if it.get("summary"): parts.append(f"<div class='sum'>{it['summary']}</div>")
        parts.append("</div>")

    parts.append("</body></html>")
    html_str = "".join(parts)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return dcc.send_string(html_str, f"{project_name}_report_{ts}.html")
