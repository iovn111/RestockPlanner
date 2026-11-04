import pandas as pd
import pytest

from restock.data.base import DataSource
from restock.data.schema import DAILY_SALES, DAILY_STOCK, PRODUCTS, empty_frame, validate


class InMemorySource(DataSource):
    name = "in-memory"

    def load_products(self):
        return empty_frame(PRODUCTS)

    def load_sales(self, start=None, end=None):
        return empty_frame(DAILY_SALES)

    def load_stock(self, start=None, end=None):
        return empty_frame(DAILY_STOCK)


def test_datasource_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        DataSource()


def test_concrete_source_returns_valid_frames():
    source = InMemorySource()
    assert source.frequency == "D"
    validate(source.load_products(), PRODUCTS)
    validate(source.load_sales(), DAILY_SALES)
    validate(source.load_stock(), DAILY_STOCK)
    assert isinstance(source.load_sales(), pd.DataFrame)


def test_package_imports():
    import restock
    from restock import core, db, experiments, gui, notify, services, sync  # noqa: F401

    assert restock.__version__
