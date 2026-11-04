"""DataSource: the single interface every data source implements.

The demo store, open-dataset adapters and the Wildberries API all return
frames in the unified data model (see schema.py), so the rest of the system
does not know where the data came from.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Literal

import pandas as pd

Frequency = Literal["D", "W"]


class DataSource(ABC):
    """Abstract data source.

    Implementations must return frames that pass `schema.validate`.
    For weekly sources (`frequency == "W"`) the `date` column holds the
    Monday of each week; weekly and daily data must never be mixed silently.
    """

    name: str = "unnamed"
    frequency: Frequency = "D"

    @abstractmethod
    def load_products(self) -> pd.DataFrame:
        """Return the `products` table."""

    @abstractmethod
    def load_sales(self, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        """Return `daily_sales` rows with start <= date <= end (bounds optional)."""

    @abstractmethod
    def load_stock(self, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        """Return `daily_stock` rows with start <= date <= end (bounds optional)."""
