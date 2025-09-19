from __future__ import annotations
from pathlib import Path
from datetime import datetime
import math, os, glob
import hashlib
from concurrent.futures import ProcessPoolExecutor
from validate import validate_fact

import pandas as pd
from lxml import etree

PARALLEL_MIN_FILES = 120   
BATCHES_PER_WORKER = 6

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 50)

RAW_DIR = Path(os.getenv("TRADE_RAW_DIR", str(Path(__file__).resolve().parents[1] / "data" / "raw")))
PROC_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

def file_metadata(fp: str) -> dict:
    """Return file lineage metadata (size, mtime, name)."""
    st = os.stat(fp)
    return {
        "source_file": os.path.basename(fp),
        "source_filesize": int(st.st_size),
        "source_mtime": pd.to_datetime(st.st_mtime, unit="s", utc=True),
    }

def stable_hash(*parts: str) -> str:
    """Return a stable SHA1 hash over concatenated string parts."""
    h = hashlib.sha1()
    for p in parts:
        h.update((p or "").encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()

def read_one_xml(file_path: str) -> pd.DataFrame:
    """
    Parse one XML file into a DataFrame with lineage fields using a streaming approach (no DOM).
    This avoids building the whole document in memory and reduces per-file overhead.
    """
    try:
        meta = file_metadata(file_path)
    except Exception as e:
        print(f"[SKIP] Could not stat file: {file_path} -> {e}")
        return pd.DataFrame()

    rows = []

    try:
        context = etree.iterparse(
            file_path,
            events=("end",),
            tag="TradeRecord",
            huge_tree=True,
            remove_blank_text=True,
        )
    except Exception as e:
        print(f"[SKIP] Could not open/parse file: {file_path} -> {e}")
        return pd.DataFrame()

    for _event, tr in context:
        get = tr.findtext

        trade_date     = (get("Date") or "").strip()
        reporter_iso2  = (get("Reporter/ISO2") or "").strip()
        reporter_name  = (get("Reporter/Name") or "").strip()
        partner_iso2   = (get("Partner/ISO2") or "").strip()
        partner_name   = (get("Partner/Name") or "").strip()
        commodity_code = (get("Commodity/Code") or "").strip()
        commodity_name = (get("Commodity/Name") or "").strip()
        currency_code  = (get("Currency/Code") or "").strip()
        currency_name  = (get("Currency/Name") or "").strip()
        fx_rate_to_usd = (get("Currency/FxRateToUSD") or "").strip()
        value_numeric  = (get("Value") or "").strip()

        q = tr.find("Quantity")
        quantity_numeric = (q.text or "").strip() if q is not None and q.text else None
        unit = q.get("unit") if q is not None else None

        bk = f"{trade_date}|{reporter_iso2}|{partner_iso2}|{commodity_code}"
        record_hash = stable_hash(
            trade_date, reporter_iso2, partner_iso2, commodity_code,
            value_numeric or "", quantity_numeric or "", unit or "",
            fx_rate_to_usd or "",
        )

        rows.append({
            "trade_date": trade_date or None,
            "reporter_iso2": reporter_iso2 or None,
            "reporter_name": reporter_name or None,
            "partner_iso2": partner_iso2 or None,
            "partner_name": partner_name or None,
            "commodity_code": commodity_code or None,
            "commodity_name": commodity_name or None,
            "currency_code": currency_code or None,
            "currency_name": currency_name or None,
            "fx_rate_to_usd": fx_rate_to_usd or None,
            "value_numeric": value_numeric or None,
            "quantity_numeric": quantity_numeric,
            "unit": unit,
            "bk": bk,
            "record_hash": record_hash,
            **meta,
        })

        # free memory progressively
        tr.clear()
        parent = tr.getparent()
        while parent is not None and parent.getprevious() is not None:
            del parent[0]

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce").dt.date
    for col in ["value_numeric", "quantity_numeric", "fx_rate_to_usd"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["trade_date", "reporter_iso2", "partner_iso2", "commodity_code"])

def extract_all(files: list[str] | None = None) -> pd.DataFrame:
    files = files or sorted(glob.glob(str(RAW_DIR / "*.xml")))
    n = len(files)
    print(f"Scanning {RAW_DIR} for XML ... found {n} file(s).")

    if n == 0:
        raise FileNotFoundError(f"No XML files found in {RAW_DIR}.")

    if n < PARALLEL_MIN_FILES:
        frames = [read_one_xml(fp) for fp in files]
    else:
        frames = _parse_in_parallel_batched(files)

    frames = [f for f in frames if f is not None and not f.empty]
    if not frames:
        raise ValueError("No valid rows from any XML.")

    df = pd.concat(frames, ignore_index=True)
    df["load_ts"] = pd.Timestamp.now(tz="UTC")

    df = df.sort_values(["bk", "source_mtime"], ascending=[True, False], kind="stable")
    df = df.drop_duplicates(subset=["bk"], keep="first").reset_index(drop=True)

    print(f"Extracted rows (after in-batch dedup): {len(df):,}")
    return df

def _parse_in_parallel_batched(files: list[str]):
    """Batch multiple files per process to amortize spawn/IPC overhead."""
    workers = os.cpu_count() or 4

    nbatches = max(BATCHES_PER_WORKER * workers, 1)
    chunk_size = max(math.ceil(len(files) / nbatches), 1)
    batches = [files[i:i+chunk_size] for i in range(0, len(files), chunk_size)]

    def parse_batch(batch: list[str]):
        import pandas as pd
        parts = [read_one_xml(fp) for fp in batch]
        parts = [p for p in parts if p is not None and not p.empty]
        return pd.concat(parts, ignore_index=True) if parts else None

    frames = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for df in ex.map(parse_batch, batches, chunksize=1):
            if df is not None and not df.empty:
                frames.append(df)
    return frames

# Transform

def build_dims(df: pd.DataFrame):
    if "load_ts" not in df.columns:
        df = df.copy()
        df = df.copy()
        df["load_ts"] = pd.Timestamp.now(tz="UTC")

    countries = pd.concat([
        df[["reporter_iso2", "reporter_name"]]
          .rename(columns={"reporter_iso2": "iso2", "reporter_name": "name"}),
        df[["partner_iso2", "partner_name"]]
          .rename(columns={"partner_iso2": "iso2", "partner_name": "name"}),
    ], ignore_index=True).drop_duplicates()

    dim_country = countries.sort_values(["iso2", "name"]).reset_index(drop=True)

    dim_currency = df[["currency_code", "currency_name"]].dropna().drop_duplicates() \
                    .rename(columns={"currency_code": "code", "currency_name": "name"}) \
                    .sort_values(["code"]).reset_index(drop=True)

    dim_commodity = df[["commodity_code", "commodity_name"]].dropna().drop_duplicates() \
                      .rename(columns={"commodity_code": "code", "commodity_name": "name"}) \
                      .sort_values(["code"]).reset_index(drop=True)

    fact = df[[
        "bk","record_hash","trade_date","reporter_iso2","partner_iso2",
        "commodity_code","currency_code","value_numeric","quantity_numeric","unit",
        "fx_rate_to_usd","source_file","source_filesize","source_mtime","load_ts"
    ]].copy()
    fact["value_usd"] = fact["value_numeric"] * fact["fx_rate_to_usd"]

    return dim_country, dim_currency, dim_commodity, fact

def write_parquet(dim_country, dim_currency, dim_commodity, fact):
    dim_country.to_parquet(PROC_DIR / "dim_country.parquet", index=False)
    dim_currency.to_parquet(PROC_DIR / "dim_currency.parquet", index=False)
    dim_commodity.to_parquet(PROC_DIR / "dim_commodity.parquet", index=False)
    fact.to_parquet(PROC_DIR / "fact_trades.parquet", index=False)

def main():
    print(f"[{datetime.utcnow().isoformat()}] Extracting XML from {RAW_DIR} ...")
    df = extract_all()

    print("Transforming to dims + fact ...")
    dim_country, dim_currency, dim_commodity, fact = build_dims(df)

    try:
        fact = validate_fact(fact)
        print("Fact table passed schema validation ✅")
    except Exception as e:
        print("❌ Fact table failed validation:", e)
        return  # stop the pipeline if validation fails

    print(
        f"dim_country={len(dim_country)}, "
        f"dim_currency={len(dim_currency)}, "
        f"dim_commodity={len(dim_commodity)}, "
        f"fact={len(fact)}"
    )

    print("Writing Parquet outputs ...")
    write_parquet(dim_country, dim_currency, dim_commodity, fact)
    print("Done ✅  (Check data/processed/)")

if __name__ == "__main__":
    main()
