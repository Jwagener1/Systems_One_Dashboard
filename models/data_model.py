"""Data model for the Dash application.

This class encapsulates the logic for loading and providing data to
the rest of the application.  The example uses a synthetic data
source (generated via pandas) for demonstration purposes, but in a
real‑world scenario this model would be responsible for connecting to
databases, reading files or querying external APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union, List, cast

import pandas as pd

from utils import config

try:  # Optional dependency
    from influxdb_client import InfluxDBClient  # type: ignore

    _has_influx: bool = True
except Exception:  # pragma: no cover - optional dependency handling
    _has_influx = False


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
        """Generate a synthetic time series dataset for demonstration purposes.

        Returns:
            pd.DataFrame: A DataFrame with Time and DIM2 statistics columns.
        """
        # Create sample time series data that mimics DIM2 statistics
        
        # Generate timestamps for the last 6 hours 
        end_time = pd.Timestamp.now()
        start_time = end_time - pd.Timedelta(hours=6)
        time_range = pd.date_range(start=start_time, end=end_time, freq='5min')
        
        # Generate realistic DIM2 statistics data
        import numpy as np
        n_points = len(time_range)
        
        # Simulate total items (gradually increasing over time)
        total_items = 800 + np.cumsum(np.random.normal(2, 1, n_points))
        total_items = np.maximum(total_items, 0)  # Ensure non-negative
        
        # Good reads should be close to total items but slightly less
        good_reads = total_items * np.random.uniform(0.85, 0.98, n_points)
        
        # No reads should be low and occasional
        no_reads = np.random.poisson(2, n_points)
        
        df = pd.DataFrame({
            'Time': time_range,
            'Total Items': total_items,
            'Good Reads': good_reads,
            'No Reads': no_reads
        })
        
        return df

    # --- InfluxDB integration -------------------------------------------------
    def _influx_configured(self) -> bool:
        return bool(
            _has_influx
            and config.INFLUXDB_URL
            and config.INFLUXDB_TOKEN
            and config.INFLUXDB_ORG
            and config.INFLUXDB_BUCKET
        )

    def _load_from_influx(self) -> pd.DataFrame:
        """Load DIM2 statistics data from InfluxDB as time series.

        Returns proper time-series data for visualization with time on x-axis
        and metric values on y-axis.
        """
        if not self._influx_configured():  # Fallback guard
            return self._generate_sample_data()

        # Hardcode the DIM2 query directly in the application code
        flux = f"""
        from(bucket: "{config.INFLUXDB_BUCKET}")
          |> range(start: {config.INFLUXDB_RANGE_START})
          |> filter(fn: (r) => r["_measurement"] == "device_data")
          |> filter(fn: (r) => r["station"] == "DIM2")
          |> filter(fn: (r) => r["message_type"] == "statistics")
          |> filter(fn: (r) => r["_field"] == "statistics_total_items" or r["_field"] == "statistics_good_reads" or r["_field"] == "statistics_no_reads")
          |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
          |> keep(columns: ["_time", "statistics_total_items", "statistics_good_reads", "statistics_no_reads"])
          |> sort(columns: ["_time"])
        """
        try:
            with InfluxDBClient(url=config.INFLUXDB_URL, token=config.INFLUXDB_TOKEN, org=config.INFLUXDB_ORG, timeout=10_000) as client:  # type: ignore
                query_api = client.query_api()  # type: ignore[attr-defined]
                tables: Union[pd.DataFrame, List[pd.DataFrame]] = query_api.query_data_frame(org=config.INFLUXDB_ORG, query=flux)  # type: ignore[attr-defined]
        except Exception as e:
            # Log the error for debugging
            print(f"InfluxDB query failed: {e}")
            return self._generate_sample_data()

        if isinstance(tables, list):  # influx client may return list of DFs
            df: pd.DataFrame = pd.concat(
                cast(List[pd.DataFrame], tables), ignore_index=True
            )
        else:
            df = cast(pd.DataFrame, tables)

        # Check if we got data
        if df.empty:
            print("No data returned from InfluxDB")
            return self._generate_sample_data()

        # Ensure we have the required columns
        required_cols = ['_time', 'statistics_total_items', 'statistics_good_reads', 'statistics_no_reads']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Missing columns in InfluxDB data: {missing_cols}")
            return self._generate_sample_data()

        # Convert time and sort
        df['_time'] = pd.to_datetime(df['_time'])
        df = df.sort_values('_time').reset_index(drop=True)
        
        # Rename columns for the application
        df = df.rename(columns={
            '_time': 'Time',
            'statistics_total_items': 'Total Items',
            'statistics_good_reads': 'Good Reads', 
            'statistics_no_reads': 'No Reads'
        })
        
        # Convert numeric columns to float
        for col in ['Total Items', 'Good Reads', 'No Reads']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df

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
        # Decide source: Influx (if configured) else synthetic
        if self._influx_configured():
            df = self._load_from_influx()
        else:
            df = self._generate_sample_data()
        self._cache = df
        return df
