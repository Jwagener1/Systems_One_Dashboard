"""Data model for the Dash application.

This class encapsulates the logic for loading and providing data to
the rest of the application.  The example uses a synthetic data
source (generated via pandas) for demonstration purposes, but in a
real‑world scenario this model would be responsible for connecting to
databases, reading files or querying external APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd


@dataclass
class DataModel:
    """Encapsulates the data retrieval logic.

    Attributes:
        _cache (Optional[pd.DataFrame]): Internal cache of the loaded
            data.  Repeated calls to :meth:`get_data` will return
            the cached DataFrame unless `force_reload` is set.
    """

    _cache: Optional[pd.DataFrame] = field(default=None, init=False, repr=False)

    def _generate_sample_data(self) -> pd.DataFrame:
        """Generate a synthetic dataset for demonstration purposes.

        Returns:
            pd.DataFrame: A DataFrame with categorical and numeric
                columns.
        """
        # Create a simple synthetic dataset.  In practice this method
        # could read from a CSV, database, API, etc.
        data = {
            "Category": ["A", "B", "C", "D", "E"] * 20,
            "Value1": (pd.Series(range(100)) * 1.5).tolist(),
            "Value2": (pd.Series(range(100)) ** 1.2).tolist(),
        }
        return pd.DataFrame(data)

    def load_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Load and return the dataset.

        Args:
            force_reload (bool): If True, ignore any cached data and
                reload it.  Otherwise, return the cached data if
                available.

        Returns:
            pd.DataFrame: The loaded data.
        """
        if self._cache is not None and not force_reload:
            return self._cache
        df = self._generate_sample_data()
        self._cache = df
        return df