"""Service layer for accessing data.

The service layer provides an abstraction over the data model.  In
larger applications this is the place to implement caching,
authorization or request throttling when accessing external systems.
By injecting the service into the view‑model we adhere to the
dependency inversion principle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from models.data_model import DataModel


@dataclass
class DataService:
    """Facade for retrieving data from the model.

    Args:
        model (DataModel): The underlying data model.
    """

    model: DataModel

    def get_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Retrieve data via the model.

        Args:
            force_reload (bool): If True, the model will be asked to
                reload the data even if it has been cached.

        Returns:
            pandas.DataFrame: The requested dataset.
        """
        return self.model.load_data(force_reload=force_reload)