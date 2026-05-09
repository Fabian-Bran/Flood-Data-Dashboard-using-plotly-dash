"""
tests/test_dashboard.py
-----------------------
Unit tests for all pure functions and extracted callback logic in dashboard.py.

Run with:
    pytest tests/test_dashboard.py -v

Dependencies: pytest, pandas, dash, plotly  (all already required by the app).

NOTE: The tests import only the pure-function layer from dashboard.py.
      The Dash app itself (layout, callbacks) is NOT instantiated here, so
      flood_data.csv does not need to exist on the test machine.
      Callback logic is re-implemented as plain functions below and tested
      independently of Dash's callback machinery.
"""

import pytest
import pandas as pd
from dash import html

# ---------------------------------------------------------------------------
# Re-import just the constants and pure functions we want to test.
# We patch pd.read_csv before importing so the module-level CSV load doesn't
# fail when flood_data.csv is absent.
# ---------------------------------------------------------------------------
import unittest.mock as mock
import sys

# Provide a minimal stub DataFrame so the module-level `pd.read_csv(...)` call
# inside dashboard.py doesn't raise FileNotFoundError during test collection.
_STUB_DF = pd.DataFrame({
    "RiskLevel":           ["High", "Low", "Critical", "Moderate"],
    "InsuranceStatus":     ["Yes",  "No",  "Yes",      "No"],
    "BuildingType":        ["Wood", "Brick", "Wood",   "Concrete"],
    "PrimaryLanguage":     ["Nepali", "English", "Nepali", "Nepali"],
    "PowerStatus":         ["On", "Off", "On", "Off"],
    "GasShutoff":          ["Yes", "No", "Yes", "No"],
    "EvacuationZone":      ["A", "B", "A", "C"],
    "CurrentStatus":       ["Safe", "Evacuated", "Safe", "Missing"],
    "MobilityAssistance":  ["No", "Yes", "No", "Yes"],
    "RouteToShelterClear": ["Yes", "No", "Yes", "Yes"],
    "Age":                 [25, 45, 60, 30],
    "HouseholdSize":       [3, 1, 5, 2],
    "YearBuilt":           [2000, 1990, 1980, 2010],
    "WaterDepth_cm":       [10, 50, 100, 20],
    "WaterRisingRate_cm_hr": [2, 5, 10, 3],
    "StructuralDamage_Pct":  [5, 30, 80, 15],
    "Elevation_m":           [100, 50, 200, 150],
    "DistanceToRiver_m":     [500, 100, 1000, 300],
    "ID":      [1, 2, 3, 4],
    "FullName":["Alice Sharma", "Bob Rai", "Carol Thapa", "Dan Gurung"],
    "Phone":   ["9800000001", "9800000002", "9800000003", "9800000004"],
    "Address": ["Kathmandu", "Pokhara", "Chitwan", "Bhaktapur"],
    "Lat":     [27.7, 28.2, 27.6, 27.67],
    "Lng":     [85.3, 83.9, 84.4, 85.4],
})

with mock.patch("pandas.read_csv", return_value=_STUB_DF):
    # Remove cached module if it exists (e.g. from a previous test run in the
    # same process) so the patch takes effect on a fresh import.
    sys.modules.pop("dashboard", None)
    import dashboard as db


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_df():
    """Return a copy of the stub DataFrame for use in filter tests."""
    return _STUB_DF.copy()


@pytest.fixture
def single_row():
    """Return a single valid row dict for table / component tests."""
    return {
        "ID": 42,
        "FullName": "Test Person",
        "Phone": "9800000099",
        "Address": "Test Street",
        "Lat": 27.7,
        "Lng": 85.3,
        "RiskLevel": "High",
    }


@pytest.fixture
def all_rows(sample_df):
    """Return all stub rows as a list of dicts."""
    return sample_df.to_dict("records")


# =============================================================================
# make_options
# =============================================================================

class TestMakeOptions:

    def test_always_starts_with_all(self):
        opts = db.make_options(["B", "A", "C"])
        assert opts[0] == {"label": "All", "value": "All"}

    def test_remaining_options_are_sorted(self):
        opts = db.make_options(["Banana", "Apple", "Cherry"])
        labels = [o["label"] for o in opts[1:]]
        assert labels == sorted(labels)

    def test_empty_input_returns_only_all(self):
        opts = db.make_options([])
        assert len(opts) == 1
        assert opts[0]["value"] == "All"

    def test_label_and_value_match(self):
        opts = db.make_options(["High", "Low"])
        for opt in opts[1:]:
            assert opt["label"] == opt["value"]

    def test_duplicate_values_are_preserved(self):
        # sorted() keeps duplicates; callers should deduplicate upstream
        opts = db.make_options(["A", "A"])
        assert len(opts) == 3  # All + A + A


# =============================================================================
# get_risk_color
# =============================================================================

class TestGetRiskColor:

    @pytest.mark.parametrize("risk,expected", [
        ("High",     "#ff4d4f"),
        ("high",     "#ff4d4f"),
        ("HIGH",     "#ff4d4f"),
        ("Critical", "#ff4d4f"),
        ("Medium",   "#faad14"),
        ("Moderate", "#faad14"),
        ("Low",      "#52c41a"),
        ("Safe",     "#52c41a"),
    ])
    def test_known_risk_levels(self, risk, expected):
        assert db.get_risk_color(risk) == expected

    def test_unknown_risk_returns_fallback(self):
        assert db.get_risk_color("Unknown") == db.RISK_COLOR_FALLBACK

    def test_empty_string_returns_fallback(self):
        assert db.get_risk_color("") == db.RISK_COLOR_FALLBACK

    def test_non_string_input_coerced(self):
        # Should not raise; risk level could come in as a non-string
        result = db.get_risk_color(None)
        assert result == db.RISK_COLOR_FALLBACK


# =============================================================================
# col_range
# =============================================================================

class TestColRange:

    def test_returns_min_and_max(self, sample_df):
        lo, hi = db.col_range(sample_df, "Age")
        assert lo == int(sample_df["Age"].min())
        assert hi == int(sample_df["Age"].max())

    def test_returns_integers(self, sample_df):
        lo, hi = db.col_range(sample_df, "Age")
        assert isinstance(lo, int)
        assert isinstance(hi, int)

    def test_single_value_column(self):
        df = pd.DataFrame({"X": [7, 7, 7]})
        lo, hi = db.col_range(df, "X")
        assert lo == hi == 7

    def test_float_column_truncates_to_int(self):
        df = pd.DataFrame({"Y": [1.9, 5.1]})
        lo, hi = db.col_range(df, "Y")
        assert lo == 1
        assert hi == 5


# =============================================================================
# create_risk_table
# =============================================================================

class TestCreateRiskTable:

    def test_empty_data_returns_no_data_div(self):
        result = db.create_risk_table([])
        assert isinstance(result, html.Div)
        assert "No data available" in str(result.children)

    def test_single_row_produces_one_card(self, single_row):
        result = db.create_risk_table([single_row])
        # Outer div contains a list of cards
        assert isinstance(result, html.Div)
        assert len(result.children) == 1

    def test_multiple_rows_produce_correct_card_count(self, all_rows):
        result = db.create_risk_table(all_rows)
        assert len(result.children) == len(all_rows)

    def test_card_has_correct_css_class(self, single_row):
        result = db.create_risk_table([single_row])
        card = result.children[0]
        assert card.className == "risk-card"

    def test_id_bubble_shows_id(self, single_row):
        result = db.create_risk_table([single_row])
        card = result.children[0]
        id_bubble = card.children[0]
        assert str(single_row["ID"]) in str(id_bubble.children)

    def test_risk_badge_border_colour_matches_risk(self, single_row):
        result = db.create_risk_table([single_row])
        card = result.children[0]
        risk_badge = card.children[2]
        expected_color = db.get_risk_color(single_row["RiskLevel"])
        assert risk_badge.style["borderColor"] == expected_color

    def test_unknown_risk_uses_fallback_colour(self):
        row = {
            "ID": 99, "FullName": "X", "Phone": "0", "Address": "Y",
            "Lat": 0, "Lng": 0, "RiskLevel": "Alien",
        }
        result = db.create_risk_table([row])
        card = result.children[0]
        risk_badge = card.children[2]
        assert risk_badge.style["borderColor"] == db.RISK_COLOR_FALLBACK


# =============================================================================
# create_pie_chart
# =============================================================================

class TestCreatePieChart:

    def test_empty_data_returns_no_data_figure(self):
        fig = db.create_pie_chart([], "RiskLevel")
        labels = fig.data[0].labels
        assert "No Data" in labels

    def test_none_data_returns_no_data_figure(self):
        fig = db.create_pie_chart(None, "RiskLevel")
        labels = fig.data[0].labels
        assert "No Data" in labels

    def test_valid_data_groups_correctly(self, all_rows):
        fig = db.create_pie_chart(all_rows, "RiskLevel")
        # Should have one pie trace
        assert len(fig.data) == 1
        # All RiskLevel values from the stub should appear
        expected = set(_STUB_DF["RiskLevel"].unique())
        actual = set(fig.data[0].labels)
        assert expected == actual

    def test_total_annotation_is_set(self, all_rows):
        fig = db.create_pie_chart(all_rows, "RiskLevel")
        annotation_texts = [a["text"] for a in fig.layout.annotations]
        total = len(all_rows)
        assert any(str(total) in t for t in annotation_texts)

    def test_hole_is_donut(self, all_rows):
        fig = db.create_pie_chart(all_rows, "RiskLevel")
        assert fig.data[0].hole == 0.5

    def test_background_colour_is_dark(self, all_rows):
        fig = db.create_pie_chart(all_rows, "RiskLevel")
        assert fig.layout.paper_bgcolor == "#222222"

    def test_different_group_column(self, all_rows):
        fig = db.create_pie_chart(all_rows, "InsuranceStatus")
        expected = set(_STUB_DF["InsuranceStatus"].unique())
        actual = set(fig.data[0].labels)
        assert expected == actual


# =============================================================================
# make_sidebar_filter_block
# =============================================================================

class TestMakeSidebarFilterBlock:

    def test_dropdown_block_has_two_items(self):
        from dash import dcc
        comp = dcc.Dropdown(id="risklevel_filter")
        items = db.make_sidebar_filter_block("risklevel_filter", comp)
        assert len(items) == 2  # Label + Dropdown (no Br for exact)

    def test_slider_block_has_three_items(self):
        from dash import dcc
        comp = dcc.RangeSlider(id="age_slider")
        items = db.make_sidebar_filter_block("age_slider", comp)
        assert len(items) == 3  # Label + Slider + Br

    def test_label_text_matches_config(self):
        from dash import dcc
        comp = dcc.Dropdown(id="risklevel_filter")
        items = db.make_sidebar_filter_block("risklevel_filter", comp)
        label = items[0]
        assert isinstance(label, html.Label)
        assert label.children == db.DROPDOWN_FILTERS["risklevel_filter"]["label"]


# =============================================================================
# Callback logic — filter_dataframe (tested as a pure function)
# =============================================================================
#
# We replicate the callback's filtering logic here without Dash machinery.
# This keeps tests fast and free of browser/server dependencies.

def _apply_filters(df: pd.DataFrame, filter_values: dict, is_sorted: bool = False) -> list[dict]:
    """
    Pure re-implementation of the filter_dataframe callback logic,
    accepting a dict of {filter_id: value} instead of *args.
    """
    mask = pd.Series(True, index=df.index)

    for filter_id, value in filter_values.items():
        cfg = db.FILTER_CONFIG[filter_id]
        column, kind = cfg["column"], cfg["type"]

        if kind == "exact" and value != db.ALL_OPTION:
            mask &= df[column] == value
        elif kind == "range":
            lo, hi = value
            mask &= df[column].between(lo, hi, inclusive="both")

    result = df[mask].copy()

    if is_sorted:
        result["_risk_sort"] = result["RiskLevel"].map(db.RISK_ORDER)
        result = result.sort_values("_risk_sort").drop(columns="_risk_sort")

    return result.to_dict("records")


def _default_filter_values(df: pd.DataFrame) -> dict:
    """Return filter values that select everything (All + full ranges)."""
    values = {}
    for fid, cfg in db.FILTER_CONFIG.items():
        if cfg["type"] == "exact":
            values[fid] = db.ALL_OPTION
        else:
            lo, hi = db.col_range(df, cfg["column"])
            values[fid] = [lo, hi]
    return values


class TestFilterDataframe:

    def test_no_filters_returns_all_rows(self, sample_df):
        values = _default_filter_values(sample_df)
        result = _apply_filters(sample_df, values)
        assert len(result) == len(sample_df)

    def test_exact_filter_reduces_rows(self, sample_df):
        values = _default_filter_values(sample_df)
        values["risklevel_filter"] = "High"
        result = _apply_filters(sample_df, values)
        assert all(r["RiskLevel"] == "High" for r in result)
        assert len(result) < len(sample_df)

    def test_multiple_exact_filters_are_anded(self, sample_df):
        values = _default_filter_values(sample_df)
        values["risklevel_filter"]  = "High"
        values["insurance_filter"]  = "Yes"
        result = _apply_filters(sample_df, values)
        for row in result:
            assert row["RiskLevel"] == "High"
            assert row["InsuranceStatus"] == "Yes"

    def test_range_filter_excludes_out_of_range(self, sample_df):
        values = _default_filter_values(sample_df)
        values["age_slider"] = [30, 50]  # only ages 30–50
        result = _apply_filters(sample_df, values)
        assert all(30 <= r["Age"] <= 50 for r in result)

    def test_narrow_range_can_return_empty(self, sample_df):
        values = _default_filter_values(sample_df)
        values["age_slider"] = [999, 999]
        result = _apply_filters(sample_df, values)
        assert result == []

    def test_filter_no_match_returns_empty(self, sample_df):
        values = _default_filter_values(sample_df)
        values["risklevel_filter"] = "Nonexistent"
        result = _apply_filters(sample_df, values)
        assert result == []

    def test_sorted_output_follows_risk_order(self, sample_df):
        values = _default_filter_values(sample_df)
        result = _apply_filters(sample_df, values, is_sorted=True)
        risk_positions = [db.RISK_ORDER.get(r["RiskLevel"], 99) for r in result]
        assert risk_positions == sorted(risk_positions)

    def test_unsorted_output_preserves_original_order(self, sample_df):
        values = _default_filter_values(sample_df)
        result = _apply_filters(sample_df, values, is_sorted=False)
        original_ids = list(sample_df["ID"])
        result_ids = [r["ID"] for r in result]
        assert result_ids == original_ids

    def test_result_is_list_of_dicts(self, sample_df):
        values = _default_filter_values(sample_df)
        result = _apply_filters(sample_df, values)
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)


# =============================================================================
# Callback logic — handle_pagination (tested as a pure function)
# =============================================================================

def _paginate(trigger: str, filtered_data: list, current_page: int) -> int:
    """Pure re-implementation of handle_pagination callback logic."""
    if trigger == "filtered_data_store":
        return 0
    if trigger == "next_btn":
        current_page += 1
    elif trigger == "prev_btn" and current_page > 0:
        current_page -= 1

    max_page = (len(filtered_data) - 1) // db.PAGE_SIZE
    return min(current_page, max_page)


class TestHandlePagination:

    def _make_data(self, n: int) -> list:
        return [{"ID": i} for i in range(n)]

    def test_filter_change_resets_to_page_zero(self):
        data = self._make_data(50)
        assert _paginate("filtered_data_store", data, 2) == 0

    def test_next_increments_page(self):
        data = self._make_data(50)
        assert _paginate("next_btn", data, 0) == 1

    def test_prev_decrements_page(self):
        data = self._make_data(50)
        assert _paginate("prev_btn", data, 2) == 1

    def test_prev_does_not_go_below_zero(self):
        data = self._make_data(50)
        assert _paginate("prev_btn", data, 0) == 0

    def test_next_clamps_at_max_page(self):
        # 20 rows = exactly 1 page (page 0), max_page = 0
        data = self._make_data(20)
        assert _paginate("next_btn", data, 0) == 0

    def test_next_on_last_page_stays(self):
        # 40 rows = 2 pages; max_page = 1
        data = self._make_data(40)
        assert _paginate("next_btn", data, 1) == 1

    def test_max_page_calculation_exact_multiple(self):
        # 40 rows, PAGE_SIZE=20 → pages 0 and 1 → max_page = 1
        data = self._make_data(40)
        result = _paginate("next_btn", data, 0)
        assert result == 1

    def test_single_page_dataset(self):
        data = self._make_data(5)
        assert _paginate("next_btn", data, 0) == 0
        assert _paginate("prev_btn", data, 0) == 0


# =============================================================================
# Callback logic — toggle_sort
# =============================================================================

def _toggle_sort(current_state: bool) -> bool:
    return not current_state


class TestToggleSort:

    def test_false_becomes_true(self):
        assert _toggle_sort(False) is True

    def test_true_becomes_false(self):
        assert _toggle_sort(True) is False

    def test_double_toggle_returns_original(self):
        assert _toggle_sort(_toggle_sort(False)) is False


# =============================================================================
# FILTER_CONFIG integrity
# =============================================================================

class TestFilterConfig:

    def test_all_dropdown_filters_have_required_keys(self):
        for fid, cfg in db.DROPDOWN_FILTERS.items():
            assert "column" in cfg, f"{fid} missing 'column'"
            assert "label"  in cfg, f"{fid} missing 'label'"

    def test_all_slider_filters_have_required_keys(self):
        for fid, cfg in db.SLIDER_FILTERS.items():
            assert "column" in cfg, f"{fid} missing 'column'"
            assert "label"  in cfg, f"{fid} missing 'label'"

    def test_filter_config_type_field_is_set(self):
        for fid, cfg in db.FILTER_CONFIG.items():
            assert cfg["type"] in ("exact", "range"), f"{fid} has invalid type"

    def test_dropdown_filters_have_exact_type(self):
        for fid in db.DROPDOWN_FILTERS:
            assert db.FILTER_CONFIG[fid]["type"] == "exact"

    def test_slider_filters_have_range_type(self):
        for fid in db.SLIDER_FILTERS:
            assert db.FILTER_CONFIG[fid]["type"] == "range"

    def test_no_duplicate_ids_across_configs(self):
        dropdown_ids = set(db.DROPDOWN_FILTERS.keys())
        slider_ids   = set(db.SLIDER_FILTERS.keys())
        assert dropdown_ids.isdisjoint(slider_ids), "Duplicate filter IDs found"

    def test_filter_config_is_superset_of_both(self):
        all_ids = set(db.DROPDOWN_FILTERS) | set(db.SLIDER_FILTERS)
        assert all_ids == set(db.FILTER_CONFIG)
