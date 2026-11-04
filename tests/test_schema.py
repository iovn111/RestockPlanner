import pandas as pd
import pytest

from restock.data.schema import (
    DAILY_SALES,
    DAILY_STOCK,
    PRODUCTS,
    SCHEMAS,
    SchemaError,
    empty_frame,
    validate,
)


def make_stock(**overrides):
    data = {
        "product_id": ["p1", "p1", "p1"],
        "size": ["M", "M", "M"],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "stock_units": [5, 0, None],
        "in_stock": [True, False, None],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_valid_stock_keeps_gap_as_na_not_zero():
    out = validate(make_stock(), DAILY_STOCK)
    assert out["stock_units"].dtype == "Int64"
    assert pd.isna(out.loc[2, "stock_units"])
    assert pd.isna(out.loc[2, "in_stock"])
    assert out.loc[1, "stock_units"] == 0


def test_missing_column_is_reported():
    with pytest.raises(SchemaError, match="missing columns"):
        validate(make_stock().drop(columns="in_stock"), DAILY_STOCK)


def test_negative_stock_is_rejected():
    with pytest.raises(SchemaError, match="negative"):
        validate(make_stock(stock_units=[5, -1, None]), DAILY_STOCK)


def test_contradicting_stock_fields_are_rejected():
    with pytest.raises(SchemaError, match="contradicts"):
        validate(make_stock(in_stock=[False, False, None]), DAILY_STOCK)


def test_duplicate_key_is_rejected():
    df = make_stock(date=["2026-01-01", "2026-01-01", "2026-01-03"])
    with pytest.raises(SchemaError, match="duplicate"):
        validate(df, DAILY_STOCK)


def test_dates_with_time_are_rejected():
    df = make_stock(
        date=pd.to_datetime(["2026-01-01 10:00", "2026-01-02 00:00", "2026-01-03 00:00"])
    )
    with pytest.raises(SchemaError, match="without time"):
        validate(df, DAILY_STOCK)


def test_sales_without_sizes_and_optional_buyouts():
    df = pd.DataFrame(
        {
            "product_id": ["p1", "p2"],
            "size": [None, None],
            "date": ["2026-01-01", "2026-01-01"],
            "units_ordered": [3, 0],
            "units_bought_out": [1, None],
        }
    )
    out = validate(df, DAILY_SALES)
    assert out["units_ordered"].tolist() == [3, 0]
    assert pd.isna(out.loc[1, "units_bought_out"])


def test_required_column_cannot_be_empty():
    df = pd.DataFrame(
        {
            "product_id": ["p1"],
            "size": [None],
            "date": ["2026-01-01"],
            "units_ordered": [None],
            "units_bought_out": [None],
        }
    )
    with pytest.raises(SchemaError, match="empty values"):
        validate(df, DAILY_SALES)


def test_products_with_attributes():
    df = pd.DataFrame(
        {
            "product_id": ["p1"],
            "seller_id": ["s1"],
            "category": ["Платья"],
            "price": [1990.0],
            "attributes": [{"material": "хлопок", "season": "лето"}],
            "launch_date": ["2026-03-01"],
            "has_sizes": [True],
        }
    )
    out = validate(df, PRODUCTS)
    assert out.loc[0, "attributes"]["material"] == "хлопок"


@pytest.mark.parametrize("schema", list(SCHEMAS.values()), ids=list(SCHEMAS))
def test_empty_frame_matches_schema(schema):
    df = empty_frame(schema)
    assert df.columns.tolist() == schema.column_names
    assert len(df) == 0
