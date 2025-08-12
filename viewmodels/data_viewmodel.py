"""ViewModel for exposing data to the view.

The DataViewModel acts as an intermediary between the service layer and
the view.  It contains logic for transforming raw data into forms
useful for presentation.  In an MVVM architecture this layer also
holds the UI state (such as the currently selected category) and
exposes observable properties if using a reactive framework.  Dash
callbacks serve a similar purpose and receive their data from this
class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from services.data_service import DataService


@dataclass
class DataViewModel:
    """Coordinate data retrieval and business logic for the view.

    Args:
        service (DataService): Service used to retrieve data.

    Attributes:
        _data (Optional[pd.DataFrame]): Cached copy of the data to
            avoid unnecessary retrievals during a request lifecycle.
    """

    service: DataService
    _data: Optional[pd.DataFrame] = field(default=None, init=False, repr=False)

    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Load data via the service and cache it locally.

        Args:
            force_reload (bool): Whether to force the service to
                reload the data from the model.

        Returns:
            pd.DataFrame: The loaded data.
        """
        if self._data is None or force_reload:
            self._data = self.service.get_data(force_reload=force_reload)
        return self._data

    def get_time_series_data(self) -> pd.DataFrame:
        """Return the full time series data for DIM2 statistics.

        Returns:
            pd.DataFrame: Time series data with Time, Total Items, Good Reads, No Reads columns.
        """
        return self.load_data()

    def get_metrics_list(self) -> List[str]:
        """Return a list of available metrics for visualization.

        Returns:
            list[str]: List of metric names.
        """
        df = self.load_data()
        # Return all numeric columns except Time
        numeric_cols = [col for col in df.columns if col != 'Time' and pd.api.types.is_numeric_dtype(df[col])]
        return numeric_cols

    def get_latest_values(self) -> dict[str, float]:
        """Return the latest values for each metric.

        Returns:
            dict[str, float]: Dictionary mapping metric names to their latest values.
        """
        df = self.load_data()
        if df.empty or 'Time' not in df.columns:
            return {}
        
        # Get the latest row
        latest_row = df.iloc[-1]
        result = {}
        for col in df.columns:
            if col != 'Time' and pd.api.types.is_numeric_dtype(df[col]):
                result[col] = float(latest_row[col])
        
        return result