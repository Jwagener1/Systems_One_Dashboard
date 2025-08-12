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
    """Create and configure a Dash application for DIM2 time series monitoring.

    Args:
        view_model (DataViewModel): The view‑model providing data and
            business logic for the view.

    Returns:
        dash.Dash: The configured Dash application ready to run.
    """
    app = Dash(__name__)
    
    # Define the layout for DIM2 monitoring dashboard
    app.layout = html.Div(
        className="container",
        children=[
            html.H1("DIM2 Statistics Monitor", style={"textAlign": "center", "marginBottom": "2rem"}),
            
            # Latest values display
            html.Div(id="latest-values", style={"marginBottom": "2rem"}),
            
            # Time series chart
            dcc.Graph(id="timeseries-chart"),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=30*1000,  # Update every 30 seconds
                n_intervals=0
            ),
        ],
    )

    # Callback to update latest values display
    @app.callback(
        Output("latest-values", "children"),
        Input("interval-component", "n_intervals"),
    )
    def update_latest_values(n: int) -> List[Any]:
        """Update the latest values display.

        Args:
            n (int): Number of intervals elapsed.

        Returns:
            List[Any]: List of HTML components showing latest values.
        """
        # Force reload to get fresh data
        view_model.load_data(force_reload=True)
        latest_values = view_model.get_latest_values()
        
        if not latest_values:
            return [html.Div("No data available", style={"textAlign": "center"})]
        
        cards = []
        for metric, value in latest_values.items():
            card = html.Div([
                html.H4(metric, style={"margin": "0"}),
                html.H2(f"{value:,.0f}", style={"margin": "0", "color": "#1f77b4"})
            ], style={
                "border": "1px solid #ddd", 
                "borderRadius": "5px", 
                "padding": "1rem", 
                "textAlign": "center",
                "margin": "0.5rem",
                "flex": "1"
            })
            cards.append(card)
        
        return [html.Div(cards, style={"display": "flex", "justifyContent": "space-around"})]

    # Callback to update the time series chart
    @app.callback(
        Output("timeseries-chart", "figure"),
        Input("interval-component", "n_intervals"),
    )
    def update_timeseries_chart(n: int) -> Any:
        """Update time series chart with DIM2 statistics.

        Args:
            n (int): Number of intervals elapsed.

        Returns:
            plotly.graph_objs._figure.Figure: A time series figure.
        """
        # Force reload to get fresh data
        df = view_model.get_time_series_data()
        
        if df.empty or 'Time' not in df.columns:
            # Return empty figure if no data
            return {
                'data': [],
                'layout': {
                    'title': 'No data available',
                    'xaxis': {'title': 'Time'},
                    'yaxis': {'title': 'Count'}
                }
            }
        
        # Create time series plot with multiple metrics
        fig = px.line(
            df, 
            x='Time', 
            y=['Total Items', 'Good Reads', 'No Reads'],
            title='DIM2 Statistics Over Time',
            labels={'value': 'Count', 'variable': 'Metric', 'Time': 'Time'},
            template='plotly_white'
        )
        
        # Customize layout
        fig.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig

    return app