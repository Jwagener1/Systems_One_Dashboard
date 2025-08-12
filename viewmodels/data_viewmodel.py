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

    def get_categories(self) -> List[str]:
        """Return a sorted list of categories present in the data.

        Returns:
            list[str]: Unique categories sorted alphabetically.
        """
        df = self.load_data()
        categories = df["Category"].unique().tolist()
        categories.sort()
        return categories

    def get_filtered_data(self, category: Optional[str] = None) -> pd.DataFrame:
        """Return data filtered by category.

        Args:
            category (Optional[str]): The category by which to filter.
                If None or not present in the dataset, the full
                dataset will be returned.

        Returns:
            pd.DataFrame: The filtered data subset.
        """
        df = self.load_data()
        if category and category in df["Category"].unique():
            return df[df["Category"] == category]
        return df

    def compute_summary_statistics(self, category: Optional[str] = None) -> pd.DataFrame:
        """Compute summary statistics (mean) for numeric columns.

        This method groups the data by category and computes the mean
        of numerical columns.  If a category is provided, statistics
        are computed for that subset; otherwise, overall statistics are
        returned for each category.

        Args:
            category (Optional[str]): Optional category filter.

        Returns:
            pd.DataFrame: A DataFrame with the category and mean values.
        """
        df = self.get_filtered_data(category)
        grouped = df.groupby("Category").agg({"Value1": "mean", "Value2": "mean"}).reset_index()
        # Rename columns for readability
        grouped.columns = ["Category", "Mean Value1", "Mean Value2"]
        return grouped