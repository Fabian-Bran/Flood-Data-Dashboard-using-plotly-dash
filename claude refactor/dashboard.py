"""
Nepal Flood Dashboard
---------------------
Dash application for exploring and filtering the Nepal flood dataset.
"""

# =============================================================================
# IMPORTS
# =============================================================================

import pandas as pd
from dash import Dash, Input, Output, State, callback_context, dcc, html

import plotly.express as px

# =============================================================================
# CONSTANTS
# =============================================================================

PAGE_SIZE = 20

RISK_ORDER = {"Critical": 0, "High": 1, "Moderate": 2, "Low": 3}

RISK_COLORS = {
    "high":     "#ff4d4f",
    "critical": "#ff4d4f",
    "medium":   "#faad14",
    "moderate": "#faad14",
    "low":      "#52c41a",
    "safe":     "#52c41a",
}
RISK_COLOR_FALLBACK = "#8c8c8c"

ALL_OPTION = "All"

PIE_CHART_GROUPS = [
    "RiskLevel",
    "InsuranceStatus",
    "BuildingType",
    "PrimaryLanguage",
    "PowerStatus",
    "GasShutoff",
    "MobilityAssistance",
    "RouteToShelterClear",
    "CurrentStatus",
    "EvacuationZone",
]

# =============================================================================
# FILTER CONFIG
# Each key is the Dash component id; each value describes the column it filters
# and whether it's an exact-match dropdown or a range slider.
# =============================================================================

DROPDOWN_FILTERS = {
    "risklevel_filter":   {"column": "RiskLevel",             "label": "Risk Level"},
    "insurance_filter":   {"column": "InsuranceStatus",       "label": "Insurance Status"},
    "buildingtype_filter":{"column": "BuildingType",          "label": "Building Type"},
    "language_filter":    {"column": "PrimaryLanguage",       "label": "Language"},
    "powerstatus_filter": {"column": "PowerStatus",           "label": "Power Status"},
    "gasshutoff_filter":  {"column": "GasShutoff",            "label": "Gas Shutoff"},
    "evacuationzone_filter":{"column": "EvacuationZone",      "label": "Evacuation Zone"},
    "currentstatus_filter":{"column": "CurrentStatus",        "label": "Current Status"},
    "mobility_filter":    {"column": "MobilityAssistance",    "label": "Mobility Assistance"},
    "routeclear_filter":  {"column": "RouteToShelterClear",   "label": "Route Clear"},
}

SLIDER_FILTERS = {
    "age_slider":          {"column": "Age",                    "label": "Age Range"},
    "household_slider":    {"column": "HouseholdSize",          "label": "Household Size"},
    "yearbuilt_slider":    {"column": "YearBuilt",              "label": "Year Built"},
    "waterdepth_slider":   {"column": "WaterDepth_cm",          "label": "Water Depth"},
    "waterrise_slider":    {"column": "WaterRisingRate_cm_hr",  "label": "Water Rise"},
    "damage_slider":       {"column": "StructuralDamage_Pct",   "label": "Damage Level"},
    "elevation_slider":    {"column": "Elevation_m",            "label": "Elevation"},
    "riverdistance_slider":{"column": "DistanceToRiver_m",      "label": "River Distance"},
}

# Combined for the filter callback — dropdowns first, then sliders (order matters).
FILTER_CONFIG = {
    **{k: {**v, "type": "exact"} for k, v in DROPDOWN_FILTERS.items()},
    **{k: {**v, "type": "range"} for k, v in SLIDER_FILTERS.items()},
}

# =============================================================================
# APP INIT & DATA
# =============================================================================

app = Dash(name="Nepal Flood Dashboard")

flood_data_df = pd.read_csv("flood_data.csv")

# =============================================================================
# UTILS
# =============================================================================

def make_options(values: list) -> list[dict]:
    """Return a list of Dash dropdown options with a leading 'All' entry."""
    return [{"label": ALL_OPTION, "value": ALL_OPTION}] + [
        {"label": v, "value": v} for v in sorted(values)
    ]


def get_risk_color(risk: str) -> str:
    """Return a colour hex string for a given risk level label."""
    return RISK_COLORS.get(str(risk).lower(), RISK_COLOR_FALLBACK)


def col_range(df: pd.DataFrame, column: str) -> tuple[int, int]:
    """Return the (min, max) integer range for a DataFrame column."""
    return int(df[column].min()), int(df[column].max())

# =============================================================================
# CHART BUILDERS
# =============================================================================

def create_risk_table(data: list[dict]) -> html.Div:
    """
    Build a styled card-list from a list of row dicts.

    Expected keys: ID, FullName, Phone, Address, Lat, Lng, RiskLevel
    """
    if not data:
        return html.Div("No data available", className="text-white")

    cards = []
    for row in data:
        risk_color = get_risk_color(row["RiskLevel"])

        card = html.Div(
            className="risk-card",
            children=[
                # --- ID bubble ---
                html.Div(str(row["ID"]), className="risk-card__id-bubble"),

                # --- Centre content ---
                html.Div(
                    className="risk-card__body",
                    children=[
                        html.Div(
                            className="risk-card__top-row",
                            children=[
                                html.Div(row["FullName"], className="risk-card__name"),
                                html.Div(row["Phone"],    className="risk-card__phone"),
                            ],
                        ),
                        html.Div(
                            className="risk-card__bottom-row",
                            children=[
                                html.Div(row["Address"],          className="risk-card__address"),
                                html.Div(f"Lat: {row['Lat']}",   className="risk-card__coord"),
                                html.Div(f"Lng: {row['Lng']}",   className="risk-card__coord risk-card__coord--right"),
                            ],
                        ),
                    ],
                ),

                # --- Risk bubble ---
                html.Div(
                    className="risk-card__risk-badge",
                    style={"borderColor": risk_color},
                    children=[
                        html.Div(className="risk-card__risk-dot", style={"backgroundColor": risk_color}),
                        html.Div(str(row["RiskLevel"]), className="risk-card__risk-label"),
                    ],
                ),
            ],
        )
        cards.append(card)

    return html.Div(cards)


def create_pie_chart(filtered_data: list[dict] | None, pie_group: str):
    """Return a Plotly donut chart grouped by *pie_group*."""
    BG = "#222222"

    if not filtered_data:
        fig = px.pie(names=["No Data"], values=[1], hole=0.5)
        fig.update_layout(paper_bgcolor=BG, margin={"t": 0})
        return fig

    df = pd.DataFrame(filtered_data)
    counts = df.groupby(pie_group).size().reset_index(name="Count")
    total = counts["Count"].sum()

    fig = px.pie(counts, values="Count", names=pie_group, hole=0.5)

    fig.update_traces(
        textinfo="label+percent+value",
        texttemplate="%{label}<br>%{value} (%{percent})",
        marker={"line": {"width": 2, "color": "black"}},
        hovertemplate=(
            f"<b>%{{label}}</b><br>"
            f"Count: %{{value}}<br>"
            f"Percent: %{{percent}}<br>"
            f"Total: {total}<extra></extra>"
        ),
    )

    fig.update_layout(
        paper_bgcolor=BG,
        margin={"t": 0},
        annotations=[
            dict(text=f"Total<br>{total}", x=0.5, y=0.5, font_size=18, showarrow=False)
        ],
        legend=dict(font=dict(color="white")),
    )

    return fig

# =============================================================================
# COMPONENT BUILDERS
# =============================================================================
def make_page_number(current_page, max_page):
    return html.Span(f"{current_page}/{max_page}")

def make_dropdown(filter_id: str) -> dcc.Dropdown:
    """Build a sidebar dropdown for *filter_id* from DROPDOWN_FILTERS."""
    column = DROPDOWN_FILTERS[filter_id]["column"]
    options = make_options(flood_data_df[column].dropna().unique())
    return dcc.Dropdown(id=filter_id, options=options, value=ALL_OPTION, clearable=False)


def make_slider(filter_id: str) -> dcc.RangeSlider:
    """Build a range slider for *filter_id* from SLIDER_FILTERS."""
    column = SLIDER_FILTERS[filter_id]["column"]
    lo, hi = col_range(flood_data_df, column)
    return dcc.RangeSlider(
        id=filter_id,
        min=lo, max=hi,
        value=[lo, hi],
        tooltip={"placement": "bottom"},
        
    )


def make_sidebar_filter_block(filter_id: str, component) -> list:
    """Return [Label, Component, (Br)?] for a sidebar filter.

    Sliders get a trailing <Br> for visual breathing room; dropdowns don't.
    """
    cfg = FILTER_CONFIG[filter_id]
    label = cfg.get("label", filter_id.replace("_", " ").title())
    items = [html.Label(label, className="sidebar-label"), component]
    if cfg["type"] == "range":
        items.append(html.Br())
    return items

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

# Build all dropdowns and sliders from config
dropdowns = {fid: make_dropdown(fid) for fid in DROPDOWN_FILTERS}
sliders   = {fid: make_slider(fid)   for fid in SLIDER_FILTERS}

sidebar_children = (
    [html.H4("Filters", className="sidebar-title"), dcc.Store(id="filtered_data_store")]
    + [item for fid, comp in dropdowns.items() for item in make_sidebar_filter_block(fid, comp)]
    + [html.Hr()]
    + [item for fid, comp in sliders.items()   for item in make_sidebar_filter_block(fid, comp)]
)

sidebar = html.Div(sidebar_children, className="sidebar col-2 bg-dark text-white")

main_content = html.Div(
    className="col bg-dark text-white main-content",
    children=[
        html.Br(),
        html.H2("Nepal Flood Dataset Analysis", className="text-center fw-bold fs-1"),
        html.Br(),
        html.Label("Group by", className="sidebar-label"),
        dcc.Dropdown(
            id="piegroup",
            options=PIE_CHART_GROUPS,
            value=PIE_CHART_GROUPS[0],
            clearable=False,
        ),
        html.Br(),
        html.Div(
            dcc.Graph(id="pie_chart", className="bg-dark col-md-6 col-lg-8 col-sm-4"),
            className="chart-wrapper",
        ),
    ],
)

pagination_controls = html.Div(
    className="pagination-controls row",
    children=[
        html.Button("Previous",     id="prev_btn"),
        html.Button("Next",         id="next_btn"),
        html.Button("Sort by Risk", id="sort_risk_btn"),
    ],
)
pagination_number = html.Div(
    className="pagination-number row",
    children=[
        html.Div(id="page_numbers")
    ],
)

app.layout = html.Div(
    className="container-fluid bg-dark",
    children=[
        html.Div([sidebar, main_content], className="row bg-dark"),
        html.Br(),
        dcc.Store(id="pagination_meta", data=0),
        dcc.Store(id="current_page", data=0),
        dcc.Store(id="sorted_risk",  data=False),
        html.Div(id="risk_table", className="bg-dark"),
        html.Div([pagination_controls, pagination_number]),
    ],
)

# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    Output("pie_chart", "figure"),
    Input("filtered_data_store", "data"),
    Input("piegroup", "value"),
)
def update_pie_chart(filtered_data, pie_group):
    return create_pie_chart(filtered_data, pie_group)


@app.callback(
    Output("filtered_data_store", "data"),
    Input("sorted_risk", "data"),
    [Input(fid, "value") for fid in FILTER_CONFIG],
)
def filter_dataframe(is_sorted, *filter_values):
    """Apply all active filters to the dataset and return matching rows."""
    mask = pd.Series(True, index=flood_data_df.index)

    for filter_id, value in zip(FILTER_CONFIG, filter_values):
        cfg = FILTER_CONFIG[filter_id]
        column, kind = cfg["column"], cfg["type"]

        if kind == "exact" and value != ALL_OPTION:
            mask &= flood_data_df[column] == value

        elif kind == "range":
            lo, hi = value
            mask &= flood_data_df[column].between(lo, hi, inclusive="both")

    result = flood_data_df[mask].copy()

    if is_sorted:
        result["_risk_sort"] = result["RiskLevel"].map(RISK_ORDER)
        result = result.sort_values("_risk_sort").drop(columns="_risk_sort")

    return result.to_dict("records")


@app.callback(
    Output("risk_table", "children"),
    Input("filtered_data_store", "data"),
    Input("current_page", "data"),
)
def update_table(filtered_data, current_page):
    if not filtered_data:
        return html.Div("No data available", className="text-white")

    start = current_page * PAGE_SIZE
    paginated = filtered_data[start : start + PAGE_SIZE]
    return create_risk_table(paginated)


@app.callback(
    Output("current_page", "data"),
    Input("prev_btn", "n_clicks"),
    Input("next_btn", "n_clicks"),
    Input("filtered_data_store", "data"),
    State("current_page", "data"),
    State("pagination_meta", "data"),
    prevent_initial_call=True,
)
def handle_pagination(prev_clicks, next_clicks, filtered_data, current_page, meta):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0]

    if trigger == "filtered_data_store":
        return 0

    max_page = meta

    if trigger == "next_btn":
        current_page += 1
    elif trigger == "prev_btn" and current_page > 0:
        current_page -= 1

    return min(current_page, max_page)


@app.callback(
    Output("sorted_risk", "data"),
    Input("sort_risk_btn", "n_clicks"),
    State("sorted_risk", "data"),
    prevent_initial_call=True,
)
def toggle_sort(sort_clicks, current_state):
    return not current_state

@app.callback(
    Output("pagination_meta", "data"),
    Input("filtered_data_store", "data")
)
def compute_pagination_meta(filtered_data):
    max_page = (len(filtered_data) - 1) // PAGE_SIZE if filtered_data else 0
    return max_page
    

@app.callback(
    Output("page_numbers", "children"),
    Input("current_page", "data"),
    Input("pagination_meta", "data"),
)
def update_page_numbers(current_page, max_page):
    return make_page_number(current_page+1,max_page+1)

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)
