import pandas as pd
import numpy as np
from dash import dcc, html, Dash, callback, Input, Output, callback_context, State
import plotly.express as px
import plotly.graph_objects as go

################### UTILS ########################################################
def make_options(values):
    return [{"label": "All", "value": "All"}] + [
        {"label": v, "value": v} for v in sorted(values)
    ]

PAGE_SIZE = 20

# css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css", ]
# app = Dash(name="Gapminder Dashboard", external_stylesheets=css)
app = Dash(name="Nepal flood Dashboard")

################### DATASET ####################################
flood_data_df = pd.read_csv("flood_data.csv")



#################### CHARTS #####################################
def create_risk_table(data: list[dict]):
    """
    Creates a custom table-style component from a list of dictionaries.

    Expected dictionary keys:
    - ID
    - FullName
    - Phone
    - Address
    - Lat
    - Lng
    - RiskLevel
    """

    def get_risk_color(risk):
        """Return color based on risk rating."""

        risk = str(risk).lower()

        if risk in ["high", "critical"]:
            return "#ff4d4f"

        elif risk in ["medium", "moderate"]:
            return "#faad14"

        elif risk in ["low", "safe"]:
            return "#52c41a"

        return "#8c8c8c"

    rows = []

    # Convert list of dictionaries into iterable rows
    if not data:
        return html.Div("No data available")

    for row in data:

        risk_color = get_risk_color(row["RiskLevel"])

        card = html.Div(
            [
                # =============================
                # LEFT ID BUBBLE
                # =============================
                html.Div(
                    str(row["ID"]),
                    style={
                        "minWidth": "60px",
                        "height": "60px",
                        "borderRadius": "50%",
                        "backgroundColor": "#1890ff",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "bold",
                        "fontSize": "18px",
                        "color": "white",
                    },
                ),

                # =============================
                # CENTER CONTENT
                # =============================
                html.Div(
                    [
                        # TOP ROW
                        html.Div(
                            [
                                html.Div(
                                    row["FullName"],
                                    style={
                                        "fontWeight": "bold",
                                        "fontSize": "18px",
                                        "flex": "2",
                                    },
                                ),
                                html.Div(
                                    row["Phone"],
                                    style={
                                        "fontSize": "15px",
                                        "opacity": "0.9",
                                        "flex": "1",
                                        "textAlign": "right",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "justifyContent": "spaceBetween",
                                "alignItems": "center",
                                "marginBottom": "8px",
                            },
                        ),

                        # BOTTOM ROW
                        html.Div(
                            [
                                html.Div(
                                    row["Address"],
                                    style={
                                        "flex": "2",
                                        "fontSize": "14px",
                                        "opacity": "0.85",
                                    },
                                ),
                                html.Div(
                                    f"Lat: {row['Lat']}",
                                    style={
                                        "flex": "1",
                                        "fontSize": "13px",
                                        "textAlign": "center",
                                    },
                                ),
                                html.Div(
                                    f"Lng: {row['Lng']}",
                                    style={
                                        "flex": "1",
                                        "fontSize": "13px",
                                        "textAlign": "right",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "gap": "10px",
                            },
                        ),
                    ],
                    style={
                        "flex": "1",
                        "padding": "0 20px",
                    },
                ),

                # =============================
                # RIGHT RISK BUBBLE
                # =============================
                html.Div(
                    [
                        html.Div(
                            style={
                                "width": "16px",
                                "height": "16px",
                                "borderRadius": "50%",
                                "backgroundColor": risk_color,
                                "marginBottom": "8px",
                            }
                        ),
                        html.Div(
                            str(row["RiskLevel"]),
                            style={
                                "fontWeight": "bold",
                                "fontSize": "15px",
                            },
                        ),
                    ],
                    style={
                        "minWidth": "100px",
                        "height": "70px",
                        "borderRadius": "35px",
                        "backgroundColor": "#2b2b2b",
                        "display": "flex",
                        "flexDirection": "column",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "border": f"2px solid {risk_color}",
                        "color": "white",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "spaceBetween",
                "backgroundColor": "#1f1f1f",
                "padding": "18px",
                "borderRadius": "18px",
                "marginBottom": "14px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.3)",
                "color": "white",
            },
        )

        rows.append(card)

    return html.Div(rows)


def create_pie_chart(filtered_data, pie_group):

    filtered_df = pd.DataFrame(filtered_data)

    # Handle empty case
    if filtered_df.empty:

        fig = px.pie(
            names=["No Data"],
            values=[1],
            hole=0.5
        )

        fig.update_layout(
            paper_bgcolor="#000000",
            margin={"t": 0}
        )

        return fig

    # Group data
    data_value = (
        filtered_df
        .groupby(pie_group)
        .size()
        .reset_index(name="Count")
    )

    total = data_value["Count"].sum()

    # Pie chart
    fig = px.pie(
        data_value,
        values="Count",
        names=pie_group,
        hole=0.5
    )

    # Show % + label
    fig.update_traces(
        textinfo="label+percent+value",
        texttemplate="%{label}<br>%{value} (%{percent})",
        marker={
            "line": {
                "width": 2,
                "color": "black"
            }
        },
        hovertemplate=(
            f"<b>%{{label}}</b><br>"
            f"Count: %{{value}}<br>"
            f"Percent: %{{percent}}<br>"
            f"Total: {total}<extra></extra>"
        )
    )

    fig.update_layout(
        paper_bgcolor="#222222",
        margin={"t": 0},
        annotations=[
            dict(
                text=f"Total<br>{total}",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False
            )
            
        ],
        legend=dict(
        font=dict(
            color="white"   # change to any colour you want
        )
    ),
    )

    return fig


from dash import dcc



## =========================================================
# FILTER CONFIG
# =========================================================

FILTER_CONFIG = {

    # =====================================================
    # DROPDOWN FILTERS
    # =====================================================

    "risklevel_filter": {
        "column": "RiskLevel",
        "type": "exact"
    },

    "insurance_filter": {
        "column": "InsuranceStatus",
        "type": "exact"
    },

    "buildingtype_filter": {
        "column": "BuildingType",
        "type": "exact"
    },

    "language_filter": {
        "column": "PrimaryLanguage",
        "type": "exact"
    },

    "powerstatus_filter": {
        "column": "PowerStatus",
        "type": "exact"
    },

    "gasshutoff_filter": {
        "column": "GasShutoff",
        "type": "exact"
    },

    "evacuationzone_filter": {
        "column": "EvacuationZone",
        "type": "exact"
    },

    "currentstatus_filter": {
        "column": "CurrentStatus",
        "type": "exact"
    },

    "mobility_filter": {
        "column": "MobilityAssistance",
        "type": "exact"
    },

    "routeclear_filter": {
        "column": "RouteToShelterClear",
        "type": "exact"
    },

    # =====================================================
    # RANGE SLIDER FILTERS
    # =====================================================

    "age_slider": {
        "column": "Age",
        "type": "range"
    },

    "household_slider": {
        "column": "HouseholdSize",
        "type": "range"
    },

    "yearbuilt_slider": {
        "column": "YearBuilt",
        "type": "range"
    },

    "waterdepth_slider": {
        "column": "WaterDepth_cm",
        "type": "range"
    },

    "waterrise_slider": {
        "column": "WaterRisingRate_cm_hr",
        "type": "range"
    },

    "damage_slider": {
        "column": "StructuralDamage_Pct",
        "type": "range"
    },

    "elevation_slider": {
        "column": "Elevation_m",
        "type": "range"
    },

    "riverdistance_slider": {
        "column": "DistanceToRiver_m",
        "type": "range"
    }
}

# =========================
# UNIQUE VALUES / FILTERS
# =========================

risk_levels = sorted(flood_data_df.RiskLevel.dropna().unique())
insurance_statuses = sorted(flood_data_df.InsuranceStatus.dropna().unique())
building_types = sorted(flood_data_df.BuildingType.dropna().unique())
languages = sorted(flood_data_df.PrimaryLanguage.dropna().unique())
power_statuses = sorted(flood_data_df.PowerStatus.dropna().unique())
gas_shutoff_statuses = sorted(flood_data_df.GasShutoff.dropna().unique())
evacuation_zones = sorted(flood_data_df.EvacuationZone.dropna().unique())
current_statuses = sorted(flood_data_df.CurrentStatus.dropna().unique())
mobility_assistance_options = sorted(flood_data_df.MobilityAssistance.dropna().unique())
route_clear_options = sorted(flood_data_df.RouteToShelterClear.dropna().unique())

pie_chart_groups = [
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

# Numeric ranges (better for sliders)
age_min = int(flood_data_df.Age.min())
age_max = int(flood_data_df.Age.max())

household_min = int(flood_data_df.HouseholdSize.min())
household_max = int(flood_data_df.HouseholdSize.max())

yearbuilt_min = int(flood_data_df.YearBuilt.min())
yearbuilt_max = int(flood_data_df.YearBuilt.max())

waterdepth_min = int(flood_data_df.WaterDepth_cm.min())
waterdepth_max = int(flood_data_df.WaterDepth_cm.max())

waterrise_min = int(flood_data_df.WaterRisingRate_cm_hr.min())
waterrise_max = int(flood_data_df.WaterRisingRate_cm_hr.max())

damage_min = int(flood_data_df.StructuralDamage_Pct.min())
damage_max = int(flood_data_df.StructuralDamage_Pct.max())

elevation_min = int(flood_data_df.Elevation_m.min())
elevation_max = int(flood_data_df.Elevation_m.max())

riverdistance_min = int(flood_data_df.DistanceToRiver_m.min())
riverdistance_max = int(flood_data_df.DistanceToRiver_m.max())


# =========================
# DROPDOWNS
# =========================

risklevel_dropdow_side = dcc.Dropdown(
    id="risklevel_filter",
    options=make_options(risk_levels),
    value="All",
    clearable=False
)

insurance_dropdown_side = dcc.Dropdown(
    id="insurance_filter",
    options=make_options(insurance_statuses),
    value="All",
    clearable=False
)

buildingtype_dropdown_side = dcc.Dropdown(
    id="buildingtype_filter",
    options=make_options(building_types),
    value="All",
    clearable=False
)

language_dropdown_side = dcc.Dropdown(
    id="language_filter",
    options=make_options(languages),
    value="All",
    clearable=False
)

powerstatus_dropdown_side = dcc.Dropdown(
    id="powerstatus_filter",
    options=make_options(power_statuses),
    value="All",
    clearable=False
)

gasshutoff_dropdown_side = dcc.Dropdown(
    id="gasshutoff_filter",
    options=make_options(gas_shutoff_statuses),
    value="All",
    clearable=False
)

evacuationzone_dropdown_side = dcc.Dropdown(
    id="evacuationzone_filter",
    options=make_options(evacuation_zones),
    value="All",
    clearable=False
)

currentstatus_dropdown_side = dcc.Dropdown(
    id="currentstatus_filter",
    options=make_options(current_statuses),
    value="All",
    clearable=False
)

mobility_dropdown_side = dcc.Dropdown(
    id="mobility_filter",
    options=make_options(mobility_assistance_options),
    value="All",
    clearable=False
)

routeclear_dropdown_side = dcc.Dropdown(
    id="routeclear_filter",
    options=make_options(route_clear_options),
    value="All",
    clearable=False
)

piegroup_dropdown_main = dcc.Dropdown(
    id="piegroup",
    options=pie_chart_groups,
    value=pie_chart_groups[0],
    clearable=False
)

# =========================
# SLIDERS
# =========================

age_slider = dcc.RangeSlider(
    id="age_slider",
    min=age_min,
    max=age_max,
    value=[age_min, age_max],
    tooltip={"placement": "bottom"}
)

household_slider = dcc.RangeSlider(
    id="household_slider",
    min=household_min,
    max=household_max,
    value=[household_min, household_max],
    tooltip={"placement": "bottom"}
)

yearbuilt_slider = dcc.RangeSlider(
    id="yearbuilt_slider",
    min=yearbuilt_min,
    max=yearbuilt_max,
    value=[yearbuilt_min, yearbuilt_max],
    tooltip={"placement": "bottom"}
)

waterdepth_slider = dcc.RangeSlider(
    id="waterdepth_slider",
    min=waterdepth_min,
    max=waterdepth_max,
    value=[waterdepth_min, waterdepth_max],
    tooltip={"placement": "bottom"}
)

waterrise_slider = dcc.RangeSlider(
    id="waterrise_slider",
    min=waterrise_min,
    max=waterrise_max,
    value=[waterrise_min, waterrise_max],
    tooltip={"placement": "bottom"}
)

damage_slider = dcc.RangeSlider(
    id="damage_slider",
    min=damage_min,
    max=damage_max,
    value=[damage_min, damage_max],
    tooltip={"placement": "bottom"}
)

elevation_slider = dcc.RangeSlider(
    id="elevation_slider",
    min=elevation_min,
    max=elevation_max,
    value=[elevation_min, elevation_max],
    tooltip={"placement": "bottom"}
)

riverdistance_slider = dcc.RangeSlider(
    id="riverdistance_slider",
    min=riverdistance_min,
    max=riverdistance_max,
    value=[riverdistance_min, riverdistance_max],
    tooltip={"placement": "bottom"}
)


##################### APP LAYOUT ####################################
sidebar = html.Div(
    [
        html.H4("Filters", className="sidebar-title"),
        dcc.Store(id="filtered_data_store"),
        # =========================
        # DROPDOWNS
        # =========================
        html.Label("Risk Level"),
        risklevel_dropdow_side,

        html.Label("Insurance Status"),
        insurance_dropdown_side,

        html.Label("Building Type"),
        buildingtype_dropdown_side,

        html.Label("Language"),
        language_dropdown_side,

        html.Label("Power Status"),
        powerstatus_dropdown_side,

        html.Label("Gas Shutoff"),
        gasshutoff_dropdown_side,

        html.Label("Evacuation Zone"),
        evacuationzone_dropdown_side,

        html.Label("Current Status"),
        currentstatus_dropdown_side,

        html.Label("Mobility Assistance"),
        mobility_dropdown_side,

        html.Label("Route Clear"),
        routeclear_dropdown_side,

        html.Hr(),

        # =========================
        # SLIDERS
        # =========================
        html.Label("Age Range"),
        age_slider,

        html.Br(),

        html.Label("Household Size"),
        household_slider,

        html.Br(),

        html.Label("Year Built"),
        yearbuilt_slider,

        html.Br(),

        html.Label("Water Depth"),
        waterdepth_slider,

        html.Br(),

        html.Label("Water Rise"),
        waterrise_slider,

        html.Br(),

        html.Label("Damage Level"),
        damage_slider,

        html.Br(),

        html.Label("Elevation"),
        elevation_slider,

        html.Br(),

        html.Label("River Distance"),
        riverdistance_slider,
    ],
    style={
        "background": "#222222",
        "width": "300px",
        "padding": "20px",
        "borderRight": "1px solid #ddd",
        "height": "100vh",
        "overflowY": "auto",
    }, className="col-2 bg-dark text-white",
)

main_content = html.Div([
    html.Br(),
    html.H2("Nepal Flood Dataset Analysis", className="text-center fw-bold fs-1"),
    html.Br(),
    html.Label("Group by"),
    piegroup_dropdown_main,
    html.Br(),
        html.Div([dcc.Graph(id="pie_chart",  className="bg-dark col-md-6 col-lg-4 col-sm-4"),], style={"display":"flex","justifyContent":"center"}),
        
    ], className="col bg-dark text-white", style={"height": "100vh",},
)

table_content = html.Div(id="risk_table"
)

app.layout = html.Div([
    html.Div([sidebar, main_content], className="row bg-dark"),
    html.Br(),
    dcc.Store(id="current_page", data=0),
    dcc.Store(id="sorted_risk", data=False),
    html.Div([table_content], className="bg-dark"),
    html.Div(
    [
        html.Button("Previous", id="prev_btn"),
        html.Button("Next", id="next_btn"),
        html.Button("SORT BY RISK", id="sort_risk_btn"),
    ],
    style={"display": "flex", "gap": "10px"}
)
], className="container-fluid bg-dark", style={"height": "100vh"})

##################### CALLBACKS ####################################
@callback(Output("pie_chart", "figure"), [Input("filtered_data_store", "data"), Input("piegroup", "value"),])
def update_pie_chart(filters, current_group):
    return create_pie_chart(filters, current_group)

# =========================================================
# ALL Filters CALLBACK
# =========================================================

@app.callback(
    Output("filtered_data_store", "data"),
    Input("sorted_risk", "data"),
    [
        Input(filter_id, "value")
        for filter_id in FILTER_CONFIG.keys()
    ]
)
def filter_dataframe(is_sorted, *filter_values):

    # Start with all rows included
    mask = pd.Series(True, index=flood_data_df.index)

    # Apply each filter dynamically
    for filter_id, value in zip(
        FILTER_CONFIG.keys(),
        filter_values
    ):

        config = FILTER_CONFIG[filter_id]

        column = config["column"]
        filter_type = config["type"]

        # =================================================
        # EXACT MATCH FILTERS
        # =================================================
        if filter_type == "exact":

            if value != "All":

                mask &= (
                    flood_data_df[column] == value
                )

        # =================================================
        # RANGE FILTERS
        # =================================================
        elif filter_type == "range":

            min_val, max_val = value

            mask &= (
                flood_data_df[column]
                .between(min_val, max_val, inclusive="both")
            )

    filtered_df = flood_data_df[mask]

    # Return serializable data
    if is_sorted:
        risk_order = {
        "Critical": 0,
        "High": 1,
        "Moderate": 2,
        "Low": 3
    }

        filtered_df["risk_sort"] = (
            filtered_df["RiskLevel"]
            .map(risk_order)
        )

        filtered_df = filtered_df.sort_values("risk_sort")

        return filtered_df.to_dict("records")

    return filtered_df.to_dict("records")

# =========================================================
# table CALLBACK
# =========================================================
@app.callback(
    Output("risk_table", "children"),
    Input("filtered_data_store", "data"),
    Input("current_page", "data"),
)
def update_table(filtered_data, current_page):

    if not filtered_data:
        return html.Div("No data available")

    start = current_page * PAGE_SIZE
    end = start + PAGE_SIZE

    paginated_data = filtered_data[start:end]

    return create_risk_table(paginated_data)

# =========================================================
# Pagination CALLBACK
# =========================================================

@app.callback(
    Output("current_page", "data"),
    Input("prev_btn", "n_clicks"),
    Input("next_btn", "n_clicks"),
    Input("filtered_data_store", "data"),
    State("current_page", "data"),
    prevent_initial_call=True
)
def change_page(prev_clicks, next_clicks, filtered_data, current_page):

    
    ctx = callback_context

    if not ctx.triggered:
        return current_page

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # reset on filter change
    if trigger == "filtered_data_store":
        return 0

    if trigger == "next_btn":
        current_page = current_page + 1

    if trigger == "prev_btn" and current_page > 0:
        current_page = current_page - 1

    max_page = len(filtered_data) // PAGE_SIZE
    current_page = min(current_page, max_page)
    return current_page

# =========================================================
# Sort Risk CALLBACK
# =========================================================

@app.callback(
    Output("sorted_risk", "data"),
    Input("sort_risk_btn", "n_clicks"),
    State("sorted_risk", "data"),
    prevent_initial_call=True
)
def change_page(sort_clicks, current_state):

    ctx = callback_context

    if not ctx.triggered:
        return current_state
    return not current_state



##################### RUN ####################################
if __name__ == "__main__":
    app.run(debug=True)