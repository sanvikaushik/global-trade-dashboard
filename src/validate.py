import pandas as pd
import pandera as pa
from pandera import DataFrameSchema, Column, Check, DateTime
from pandera.errors import SchemaErrors

ISO2 = Check.str_matches(r"^[A-Z]{2}$")
HS_CODE = Check.str_matches(r"^\d{4,8}$")               # HS 4–8 digit code
CURRENCY = Check.str_matches(r"^[A-Z]{3}$")             # ISO-4217 format
NONNEG = Check.ge(0)
POSITIVE = Check.gt(0)

_schema = DataFrameSchema({
    "bk":               Column(str,  nullable=False),
    "record_hash":      Column(str,  nullable=False),

    "trade_date":       Column(DateTime, nullable=False, checks=[
                            Check.le(pd.Timestamp("today").normalize()),  
                        ]),

    "reporter_iso2":    Column(str,  checks=ISO2, nullable=False),
    "partner_iso2":     Column(str,  checks=ISO2, nullable=False),
    "commodity_code":   Column(str,  checks=HS_CODE, nullable=False),

    "currency_code":    Column(str,  checks=CURRENCY, nullable=True),

    "value_numeric":    Column(float, nullable=True, checks=[NONNEG]),
    "quantity_numeric": Column(float, nullable=True, checks=[NONNEG]),
    "unit":             Column(str,  nullable=True),

    "fx_rate_to_usd":   Column(float, nullable=True, checks=[NONNEG, Check.le(1000)]),  # sanity cap
    "value_usd":        Column(float, nullable=True, checks=[NONNEG]),

    "source_file":      Column(str,  nullable=False),
    "source_filesize":  Column(int,  checks=POSITIVE, nullable=False),

    "source_mtime":     Column(DateTime, nullable=False),
    "load_ts":          Column(DateTime, nullable=False),
})

def validate_fact(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["trade_date"]   = pd.to_datetime(out["trade_date"], errors="coerce")
    out["source_mtime"] = pd.to_datetime(out["source_mtime"], errors="coerce").dt.tz_convert("UTC").dt.tz_localize(None)
    out["load_ts"]      = pd.to_datetime(out["load_ts"], errors="coerce").dt.tz_convert("UTC").dt.tz_localize(None)

    for c in ["value_numeric", "quantity_numeric", "fx_rate_to_usd", "value_usd"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype("float64")

    for c in ["reporter_iso2", "partner_iso2"]:
        if c in out.columns:
            out[c] = out[c].astype(str).str.upper()

    _ = _schema.validate(out, lazy=True)
    return out

def validate_fact_with_stats(df: pd.DataFrame):
    """
    Validate and return (valid_df, invalid_df, failure_cases_df).
    - valid_df: rows that passed schema
    - invalid_df: the original rows that failed
    - failure_cases_df: pandera failure details (column, check, index, etc.)
    """
    out = df.copy()

    out["trade_date"]   = pd.to_datetime(out["trade_date"], errors="coerce")
    out["source_mtime"] = pd.to_datetime(out["source_mtime"], errors="coerce").dt.tz_convert("UTC").dt.tz_localize(None)
    out["load_ts"]      = pd.to_datetime(out["load_ts"], errors="coerce").dt.tz_convert("UTC").dt.tz_localize(None)
    for c in ["value_numeric", "quantity_numeric", "fx_rate_to_usd", "value_usd"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype("float64")
    for c in ["reporter_iso2", "partner_iso2"]:
        if c in out.columns:
            out[c] = out[c].astype(str).str.upper()

    try:
        _ = _schema.validate(out, lazy=True)

        return out, pd.DataFrame(columns=out.columns), pd.DataFrame()
    except SchemaErrors as err:
        fc = err.failure_cases.copy()

        bad_idx = (
            fc["index"]
            .dropna()
            .astype(int)
            .drop_duplicates()
            .tolist()
        )
        invalid_df = out.iloc[bad_idx].copy() if bad_idx else pd.DataFrame(columns=out.columns)
        valid_df   = out.drop(index=bad_idx).copy()
        return valid_df, invalid_df, fc