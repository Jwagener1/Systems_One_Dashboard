"""Dash view implementation.

This module defines the Dash layout and callbacks for the application.
The view consumes a view‑model instance to obtain data and delegates
all business logic to it.  Only presentational concerns, such as
defining components and specifying callback inputs/outputs, live here.
"""

from __future__ import annotations

from typing import Any, List, Optional

import plotly.express as px
from dash import Dash, Input, Output, dcc, html

from viewmodels.data_viewmodel import DataViewModel


def create_app(view_model: DataViewModel) -> Dash:
    """Create and configure a Dash application.

    Args:
        view_model (DataViewModel): The view‑model providing data and
            business logic for the view.

    Returns:
        dash.Dash: The configured Dash application ready to run.
    """
    app = Dash(__name__)

    # Precompute category options for the dropdown.
    categories = view_model.get_categories()
    dropdown_options = [
        {"label": "All Categories", "value": ""}
    ] + [
        {"label": category, "value": category} for category in categories
    ]

    # Define the layout using Dash HTML and Core Components.
    app.layout = html.Div(
        className="container",
        children=[
            html.H2("Plotly Dash MVVM Example", style={"textAlign": "center"}),
            html.Div(
                children=[
                    html.Label("Select Category:"),
                    dcc.Dropdown(
                        id="category-dropdown",
                        options=dropdown_options,
                        value="",
                        clearable=False,
                        style={"width": "50%"},
                    ),
                ],
                style={"marginBottom": "1rem"},
            ),
            dcc.Graph(id="scatter-graph"),
            dcc.Graph(id="summary-bar-graph"),
        ],
    )

    # Callback to update the scatter graph when the category changes.
    @app.callback(
        Output("scatter-graph", "figure"),
        Input("category-dropdown", "value"),
    )
    def update_scatter(selected_category: str) -> Any:
        """Update scatter plot based on selected category.

        Args:
            selected_category (str): Category selected in the dropdown.

        Returns:
            plotly.graph_objs._figure.Figure: A scatter figure.
        """
        # Convert empty string to None for convenience.
        category = selected_category or None
        df = view_model.get_filtered_data(category)
        # Use plotly.express to construct a scatter plot with color by category.
        fig = px.scatter(
            df,
            x="Value1",
            y="Value2",
            color="Category",
            title="Scatter Plot of Value2 vs. Value1",
            labels={"Value1": "Value 1", "Value2": "Value 2"},
        )
        fig.update_layout(legend_title_text="Category")
        return fig

    # Callback to update the summary bar chart when the category changes.
    @app.callback(
        Output("summary-bar-graph", "figure"),
        Input("category-dropdown", "value"),
    )
    def update_bar(selected_category: str) -> Any:
        """Update bar chart summarising mean values per category.

        Args:
            selected_category (str): Category selected in the dropdown.

        Returns:
            plotly.graph_objs._figure.Figure: A bar figure.
        """
        category = selected_category or None
        summary_df = view_model.compute_summary_statistics(category)
        # Plotly Express can handle multiple y columns directly for grouped bars.
        fig = px.bar(
            summary_df,
            x="Category",
            y=["Mean Value1", "Mean Value2"],
            barmode="group",
            title="Mean Values per Category",
            labels={"value": "Mean", "variable": "Metric"},
        )
        fig.update_layout(legend_title_text="Metric")
        return fig

    return app