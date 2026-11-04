"""Unified data model (spec section 7.2).

Every DataSource returns pandas DataFrames with exactly these columns.
`validate()` checks a frame against its table schema and returns a copy
with normalized dtypes, so the rest of the system can rely on them.

Key rule: a missing stock observation is an empty value (NA), never 0.
"""

from dataclasses import dataclass

import pandas as pd


class SchemaError(ValueError):
    """Raised when a DataFrame does not match the unified data model."""


@dataclass(frozen=True)
class Column:
    name: str
    dtype: str  # pandas dtype: "string", "Int64", "Float64", "boolean", "datetime", "object"
    nullable: bool = False
    non_negative: bool = False


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[Column, ...]
    key: tuple[str, ...]

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


PRODUCTS = TableSchema(
    name="products",
    columns=(
        Column("product_id", "string"),
        Column("seller_id", "string"),
        Column("category", "string"),
        Column("price", "Float64", non_negative=True),
        Column("attributes", "object", nullable=True),  # dict: material, season, gender, ...
        Column("launch_date", "datetime", nullable=True),
        Column("has_sizes", "boolean"),
    ),
    key=("product_id",),
)

DAILY_SALES = TableSchema(
    name="daily_sales",
    columns=(
        Column("product_id", "string"),
        Column("size", "string", nullable=True),
        Column("date", "datetime"),
        Column("units_ordered", "Int64", non_negative=True),
        Column("units_bought_out", "Int64", nullable=True, non_negative=True),
    ),
    key=("product_id", "size", "date"),
)

DAILY_STOCK = TableSchema(
    name="daily_stock",
    columns=(
        Column("product_id", "string"),
        Column("size", "string", nullable=True),
        Column("date", "datetime"),
        Column("stock_units", "Int64", nullable=True, non_negative=True),
        Column("in_stock", "boolean", nullable=True),
    ),
    key=("product_id", "size", "date"),
)

SUPPLIER_SETTINGS = TableSchema(
    name="supplier_settings",
    columns=(
        Column("seller_id", "string"),
        Column("product_id", "string", nullable=True),  # NA = default for all products
        Column("lead_time_days", "Int64", non_negative=True),
    ),
    key=("seller_id", "product_id"),
)

SCHEMAS = {s.name: s for s in (PRODUCTS, DAILY_SALES, DAILY_STOCK, SUPPLIER_SETTINGS)}


def empty_frame(schema: TableSchema) -> pd.DataFrame:
    """Return an empty DataFrame with the schema's columns and dtypes."""
    return validate(pd.DataFrame({name: [] for name in schema.column_names}), schema)


def validate(df: pd.DataFrame, schema: TableSchema) -> pd.DataFrame:
    """Check `df` against `schema` and return a copy with normalized dtypes.

    Raises SchemaError listing every problem found.
    """
    missing = [c for c in schema.column_names if c not in df.columns]
    if missing:
        raise SchemaError(f"{schema.name}: missing columns {missing}")

    out = df[schema.column_names].copy()
    problems: list[str] = []

    for col in schema.columns:
        try:
            out[col.name] = _coerce(out[col.name], col.dtype)
        except (TypeError, ValueError) as exc:
            problems.append(f"column '{col.name}' cannot be converted to {col.dtype}: {exc}")
            continue

        series = out[col.name]
        if not col.nullable and series.isna().any():
            problems.append(f"column '{col.name}' has {int(series.isna().sum())} empty values")
        if col.non_negative and (series.dropna() < 0).any():
            problems.append(f"column '{col.name}' has negative values")
        if col.dtype == "datetime":
            values = series.dropna()
            if (values != values.dt.normalize()).any():
                problems.append(f"column '{col.name}' must contain dates without time")

    if not problems and out.duplicated(subset=list(schema.key)).any():
        problems.append(f"duplicate rows for key {list(schema.key)}")

    if schema is DAILY_STOCK and not problems:
        problems.extend(_check_stock(out))

    if problems:
        raise SchemaError(f"{schema.name}: " + "; ".join(problems))
    return out.reset_index(drop=True)


def _coerce(series: pd.Series, dtype: str) -> pd.Series:
    if dtype == "datetime":
        return pd.to_datetime(series)
    if dtype == "object":
        return series.astype("object")
    return series.astype(dtype)


def _check_stock(df: pd.DataFrame) -> list[str]:
    """When both stock fields are known they must agree.

    A row with both fields empty is an explicit gap (the day was not observed).
    """
    problems = []
    known = df["stock_units"].notna() & df["in_stock"].notna()
    disagree = known & ((df["stock_units"] > 0) != df["in_stock"])
    if disagree.any():
        problems.append(f"{int(disagree.sum())} rows where in_stock contradicts stock_units")
    return problems
