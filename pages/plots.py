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

def _get_df(stored):
    if not stored:
        return None, None
    df = pd.DataFrame(stored["data"])
    time_col = stored.get("time_col")
    if time_col is None or time_col not in df.columns:
        for c in df.columns:
            try:
                tmp = pd.to_datetime(df[c], errors="coerce")
                if not tmp.isna().all():
                    time_col = c
                    break
            except Exception:
                continue
    return df, time_col

def _filter_date_range(df, time_col, start_date, end_date):
    if df is None or time_col is None:
        return df
    if start_date is None and end_date is None:
        return df
    tmp = df.copy()
    tmp[time_col] = pd.to_datetime(tmp[time_col], errors="coerce")
    mask = pd.Series(True, index=tmp.index)
    if start_date is not None:
        mask &= tmp[time_col] >= pd.to_datetime(start_date)
    if end_date is not None:
        mask &= tmp[time_col] <= pd.to_datetime(end_date)
    return tmp.loc[mask]

def _encode_image(path):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return "data:image/png;base64," + encoded
    except Exception:
        return None

# -----------------------------
# Layout
# -----------------------------
before_after_modal = dbc.Modal(
    id="modal-before-after", is_open=False, size="xl", scrollable=True,
    children=[
        dbc.ModalHeader(dbc.ModalTitle("Before vs After — Boxplot")),
        dbc.ModalBody([
            html.Div(
                id="ba_available_range",
                style={"marginBottom":"8px","fontSize":"12px","color":"#555","fontStyle":"italic"},
            ),
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

            dbc.Modal(
                id="ba_cal_modal", is_open=False, size="sm", scrollable=False,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Pick a date"), close_button=True),
                    dbc.ModalBody([
                        html.Div(
                            style={"display":"flex","gap":"8px","alignItems":"center","marginBottom":"8px"},
                            children=[
                                html.Div("Month", style={"width":"60px","fontSize":"12px","color":"#666"}),
                                dcc.Dropdown(id="ba_jump_month", options=MONTH_OPTS,
                                             value=date.today().month, style={"width":"140px"}),
                                dbc.Button("◀", id="ba_year_prev", size="sm", color="secondary", outline=True),
                                dbc.Button("▶", id="ba_year_next", size="sm", color="secondary", outline=True),
                                dbc.Badge(id="ba_year_badge", children=str(date.today().year),
                                          color="light", text_color="dark"),
                                dbc.Button("Today", id="ba_today", size="sm", color="secondary", outline=True,
                                           style={"marginLeft":"auto"}),
                            ]
                        ),
                        dcc.DatePickerSingle(
                            id="ba_cutoff",
                            min_date_allowed=date(2000,1,1),
                            max_date_allowed=date(2050,12,31),
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

            dbc.Modal(
                id="t_cal_modal", is_open=False, size="sm", scrollable=False,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Pick date range"), close_button=True),
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

            html.Hr(),
            dcc.Graph(id="t_graph", figure=go.Figure()),
            html.Div(id="t_summary", style={"marginTop":"6px","color":"#444"}),
        ]),
        dbc.ModalFooter(dbc.Button("Close", id="t_close", color="secondary", outline=True)),
    ],
)

layout = dbc.Container(
    fluid=True,
    children=[
        dcc.Store(id="ba_year_store", data=date.today().year),
        dcc.Store(id="t_year_store", data=date.today().year),
        dcc.Store(id="report-images", data={}),
        html.Div(
            [
                html.H2("Thickener data analysis", className="page-title"),
            ],
            style={"marginBottom": "10px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5("Trend & snapshot"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label("Time period"),
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
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Label("Variable", style={"marginRight":"4px"}),
                                        dcc.Dropdown(
                                            id="trend-variable",
                                            placeholder="Select column",
                                            style={"minWidth":"220px"},
                                        ),
                                    ],
                                    style={"display":"flex","alignItems":"center","gap":"8px"},
                                ),
                                html.Div(
                                    [
                                        dbc.Button("Plot trend", id="plot-trend", color="primary", className="me-2"),
                                        dbc.Button("Add trend snapshot to report", id="add-trend-report",
                                                   color="success", outline=True),
                                    ],
                                    style={"marginTop":"8px"},
                                ),
                            ],
                            className="g-2",
                        ),
                    ],
                    md=8,
                ),
                dbc.Col(
                    [
                        html.H5("Tools"),
                        dbc.Button("Before vs After (boxplot)", id="open-ba-modal",
                                   color="secondary", outline=True, className="me-2", style={"marginBottom":"6px"}),
                        dbc.Button("Target compliance", id="open-target-modal", color="secondary", outline=True),
                        html.Hr(style={"margin":"8px 0"}),
                        html.Div(
                            [
                                html.Div("Report snapshots added:", style={"fontWeight":"bold","marginBottom":"4px"}),
                                html.Ul(id="report-list", style={"paddingLeft":"20px","fontSize":"13px"}),
                            ]
                        ),
                    ],
                    md=4,
                ),
            ],
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            dcc.Graph(id="main-graph", figure=go.Figure()),
                            type="circle",
                        ),
                    ],
                    md=12,
                )
            ]
        ),
        before_after_modal,
        target_modal,
        html.Div(id="debug-area", style={"fontSize":"11px","color":"#999","marginTop":"12px"}),
    ],
)

@dash.callback(
    Output("main-graph", "figure"),
    Output("debug-area", "children"),
    Input("plot-trend", "n_clicks"),
    State("trend-variable", "value"),
    State("time-period", "value"),
    State("stored-data", "data"),
    prevent_initial_call=True,
)
def update_trend(n_clicks, variable, period, stored):
    if not n_clicks:
        return go.Figure(), ""
    df, time_col = _get_df(stored)
    if df is None or variable is None or time_col is None:
        return go.Figure(), "No data or variable selected."

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    df = df.sort_values(time_col)

    if period:
        df = df.set_index(time_col).resample(period).mean().reset_index()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[time_col],
            y=df[variable],
            mode="lines+markers",
            name=variable,
        )
    )
    fig.update_layout(
        margin=dict(l=40, r=10, t=30, b=40),
        xaxis_title=time_col,
        yaxis_title=variable,
        template="plotly_white",
    )
    dbg = f"Trend plotted for {variable}. Rows: {len(df)}."
    return fig, dbg

@dash.callback(
    Output("report-images", "data"),
    Output("report-list", "children"),
    Input("add-trend-report", "n_clicks"),
    State("report-images", "data"),
    State("main-graph", "figure"),
    State("trend-variable", "value"),
    prevent_initial_call=True,
)
def add_trend_snapshot(n_clicks, current, fig, variable):
    if not n_clicks or fig is None:
        raise dash.exceptions.PreventUpdate
    current = current or {}
    key = f"trend_{variable or 'unknown'}"
    current[key] = fig

    items = []
    for k in current:
        items.append(html.Li(k))
    return current, items

@dash.callback(
    Output("modal-before-after", "is_open"),
    Input("open-ba-modal", "n_clicks"),
    Input("ba_close", "n_clicks"),
    State("modal-before-after", "is_open"),
    prevent_initial_call=True,
)
def toggle_ba_modal(open_click, close_click, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "open-ba-modal":
        return True
    elif ctx == "ba_close":
        return False
    return is_open

@dash.callback(
    Output("modal-target", "is_open"),
    Input("open-target-modal", "n_clicks"),
    Input("t_close", "n_clicks"),
    State("modal-target", "is_open"),
    prevent_initial_call=True,
)
def toggle_target_modal(open_click, close_click, is_open):
    ctx = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
    if ctx == "open-target-modal":
        return True
    elif ctx == "t_close":
        return False
    return is_open

@dash.callback(
    Output("trend-variable", "options"),
    Output("t_param", "options"),
    Output("ba_param", "options"),
    Input("stored-data", "data"),
)
def populate_dropdowns(stored):
    df, time_col = _get_df(stored)
    if df is None:
        return [], [], []
    num_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
    opts = [{"label": c, "value": c} for c in num_cols]
    return opts, opts, opts
# -----------------------------
# Before / After — rango de fechas, calendario y boxplot
# -----------------------------

@dash.callback(
    Output("ba_available_range", "children"),
    Output("ba_cutoff", "min_date_allowed"),
    Output("ba_cutoff", "max_date_allowed"),
    Input("stored-data", "data"),
)
def update_ba_date_range(stored):
    """
    Muestra el rango de fechas disponible en el archivo y
    restringe el DatePicker del Before/After a ese rango.
    """
    df, time_col = _get_df(stored)
    # Sin data o sin columna tiempo: devolvemos algo razonable
    if df is None or time_col is None:
        today = date.today()
        msg = "Current available data: -"
        return msg, today.replace(year=today.year - 1), today

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col])
    if df.empty:
        today = date.today()
        msg = "Current available data: (no valid dates in file)"
        return msg, today.replace(year=today.year - 1), today

    d_min = df[time_col].min().date()
    d_max = df[time_col].max().date()
    msg = f"Current available data: {d_min.isoformat()} → {d_max.isoformat()}"
    return msg, d_min, d_max


# -----------------------------
# Calendar (BA) — salto de año y mes visible
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
def step_ba_year(prev, nxt, today_clicks, current_year):
    """
    Controla el año que se muestra en el mini-calendario (badge + store).
    """
    current_year = current_year or date.today().year
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_year, str(current_year)

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "ba_year_prev":
        current_year -= 1
    elif trigger == "ba_year_next":
        current_year += 1
    elif trigger == "ba_today":
        current_year = date.today().year

    return current_year, str(current_year)


@dash.callback(
    Output("ba_cutoff", "initial_visible_month"),
    Input("stored-data", "data"),
    Input("ba_jump_month", "value"),
    Input("ba_year_store", "data"),
    Input("ba_today", "n_clicks"),
    prevent_initial_call=True,
)
def jump_ba_month(stored, month, year, today_clicks):
    """
    Define cuál mes se ve cuando se abre el calendario:

    - Cuando se carga el archivo (stored-data): se usa el mes de la primera fecha disponible.
    - Cuando se pulsa Today: se va al mes actual.
    - Cuando se cambia mes/año manualmente: se usa esos valores.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # 1) Se cargó/actualizó el archivo → ir al mes de la primera fecha
    if trigger == "stored-data":
        df, time_col = _get_df(stored)
        if df is not None and time_col is not None:
            df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
            df = df.dropna(subset=[time_col])
            if not df.empty:
                d_min = df[time_col].min().date()
                return d_min.replace(day=1)
        today = date.today()
        return today.replace(day=1)

    # 2) Botón Today → mes actual
    if trigger == "ba_today":
        today = date.today()
        return today.replace(day=1)

    # 3) Cambio de mes/año desde el dropdown / store
    month = month or date.today().month
    year = year or date.today().year
    return date(int(year), int(month), 1)


@dash.callback(
    Output("ba_cal_modal", "is_open"),
    Output("ba_cutoff_display", "value"),
    Input("ba_cal_btn", "n_clicks"),   # botón 📅
    Input("ba_cutoff", "date"),        # selección en el DatePicker
    State("ba_cal_modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_ba_cal_modal(btn_clicks, picked_date, is_open):
    """
    - Si se pulsa el botón 📅 → abre/cierra el mini-calendario.
    - Si se elige una fecha → cierra el mini-calendario y muestra la fecha en el input de texto.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, no_update

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # Abrir/cerrar modal de calendario
    if trigger == "ba_cal_btn":
        return (not is_open), no_update

    # Al escoger fecha, cerramos modal y actualizamos el display
    if trigger == "ba_cutoff" and picked_date:
        try:
            val = pd.to_datetime(picked_date).date().isoformat()
        except Exception:
            val = picked_date
        return False, val

    return is_open, no_update


# -----------------------------
# Before / After — generación del boxplot
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
def generate_before_after(n_clicks, cutoff_date, param, stored):
    """
    Genera el boxplot Before vs After usando la fecha de corte seleccionada.
    """
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    df, time_col = _get_df(stored)
    if df is None or time_col is None or param is None:
        return go.Figure(), "No data or parameter selected."

    # Preparar data
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col, param])
    df = df.sort_values(time_col)

    if cutoff_date is None:
        return go.Figure(), "Please pick a cut-off date."

    cutoff_ts = pd.to_datetime(cutoff_date)

    before = df[df[time_col] < cutoff_ts][param]
    after = df[df[time_col] >= cutoff_ts][param]

    fig = go.Figure()
    if not before.empty:
        fig.add_trace(go.Box(y=before, name="Before"))
    if not after.empty:
        fig.add_trace(go.Box(y=after, name="After"))

    fig.update_layout(
        boxmode="group",
        template="plotly_white",
        margin=dict(l=40, r=10, t=30, b=40),
        yaxis_title=param,
    )

    # Resumen rápido
    lines = []
    if not before.empty:
        lines.append(
            f"Before (n={len(before)}): mean={before.mean():.2f}, median={before.median():.2f}"
        )
    if not after.empty:
        lines.append(
            f"After (n={len(after)}): mean={after.mean():.2f}, median={after.median():.2f}"
        )

    if not lines:
        summary = "No data found around the selected cut-off date."
    else:
        summary = html.Ul([html.Li(t) for t in lines])

    return fig, summary
