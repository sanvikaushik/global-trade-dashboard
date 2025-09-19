from __future__ import annotations
import os, time, json
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
PROC_DIR = ROOT / "data" / "processed"

conn_kwargs = dict(
    host=os.getenv("PG_HOST", "127.0.0.1"),
    port=int(os.getenv("PG_PORT", "5432")),
    dbname=os.getenv("PG_DB", "trade"),
    user=os.getenv("PG_USER", "postgres"),
    password=os.getenv("PG_PASSWORD", "postgres"),
)

COLS = [
    "bk","record_hash","trade_date","reporter_iso2","partner_iso2",
    "commodity_code","currency_code","value_numeric","quantity_numeric",
    "unit","fx_rate_to_usd","value_usd","load_ts",
    "source_file","source_filesize","source_mtime"
]

def to_python(val):
    """Coerce pandas/NumPy types to plain Python for psycopg2."""
    if val is None:
        return None

    if isinstance(val, (pd._libs.missing.NAType,)):
        return None

    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    if isinstance(val, pd.Timestamp):
         return val.floor("us").to_pydatetime()
    if isinstance(val, np.integer):
        return int(val)
    if isinstance(val, np.floating):
        return float(val)
    return val

UPSERT_SQL = f"""
INSERT INTO fact_trades ({", ".join(COLS)})
VALUES %s
ON CONFLICT (bk) DO UPDATE SET
  record_hash      = EXCLUDED.record_hash,
  currency_code    = EXCLUDED.currency_code,
  value_numeric    = EXCLUDED.value_numeric,
  quantity_numeric = EXCLUDED.quantity_numeric,
  unit             = EXCLUDED.unit,
  fx_rate_to_usd   = EXCLUDED.fx_rate_to_usd,
  value_usd        = EXCLUDED.value_usd,
  load_ts          = EXCLUDED.load_ts,
  source_file      = EXCLUDED.source_file,
  source_filesize  = EXCLUDED.source_filesize,
  source_mtime     = EXCLUDED.source_mtime
"""

def cast_and_rowify(df: pd.DataFrame):
    df = df.copy()

    if "value_usd" not in df.columns:
        df["value_usd"] = df["value_numeric"] * df["fx_rate_to_usd"]

    df["trade_date"]   = pd.to_datetime(df["trade_date"], errors="coerce").dt.date
    df["load_ts"]      = pd.to_datetime(df["load_ts"], utc=True, errors="coerce")
    df["source_mtime"] = pd.to_datetime(df["source_mtime"], utc=True, errors="coerce")

    for c in ["value_numeric","quantity_numeric","fx_rate_to_usd","value_usd","source_filesize"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    for c in ["bk","record_hash","reporter_iso2","partner_iso2","commodity_code","currency_code","unit","source_file"]:
        if c in df.columns:
            df[c] = df[c].astype(object)

    rows = [tuple(to_python(v) for v in rec)
            for rec in df[COLS].itertuples(index=False, name=None)]
    return rows, len(df)

def upsert_fact(df: pd.DataFrame, page_size: int = 10_000):
    rows, total = cast_and_rowify(df)

    with psycopg2.connect(**conn_kwargs) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM fact_trades")
        before = cur.fetchone()[0]

        t0 = time.perf_counter()
        execute_values(cur, UPSERT_SQL, rows, page_size=page_size)
        elapsed = time.perf_counter() - t0

        cur.execute("SELECT count(*) FROM fact_trades")
        after = cur.fetchone()[0]

        cur.execute("""
            SELECT count(*) FROM (
              SELECT bk FROM fact_trades GROUP BY bk HAVING count(*) > 1
            ) d
        """)
        dup_bk = cur.fetchone()[0]

        inserted = max(after - before, 0)
        rows_per_sec = total / elapsed if elapsed > 0 else 0.0
        rows_per_min = rows_per_sec * 60.0

        metrics = dict(
            total_rows=total,
            elapsed_s=round(elapsed, 3),
            rows_per_min=round(rows_per_min),
            rows_per_sec=round(rows_per_sec),
            before=before, after=after,
            inserted=inserted,
            dup_bk=dup_bk,
        )
        return metrics

def insert_audit(source_files: list[str], metrics: dict):
    with psycopg2.connect(**conn_kwargs) as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO etl_audit (batch_ts, source_files, row_count, notes)
        VALUES (now(), %s, %s, %s::jsonb)
        RETURNING id
        """, (source_files, int(metrics.get("total_rows", 0)), json.dumps(metrics)))
        audit_id = cur.fetchone()[0]
    print(f"[AUDIT] etl_audit.id={audit_id} rows={metrics.get('total_rows')} ~{metrics.get('rows_per_min')}/min")
    return audit_id

if __name__ == "__main__":
    fact = pd.read_parquet(PROC_DIR / "fact_trades.parquet")

    m1 = upsert_fact(fact)
    print(f"[LOAD 1] rows={m1['total_rows']:,} time={m1['elapsed_s']:.2f}s "
          f"≈{m1['rows_per_min']:,}/min inserted={m1['inserted']:,} dup_bk={m1['dup_bk']}")

    src_files = fact["source_file"].dropna().unique().tolist()
    insert_audit(src_files, m1)

    m2 = upsert_fact(fact)
    print(f"[LOAD 2] rows={m2['total_rows']:,} time={m2['elapsed_s']:.2f}s "
          f"≈{m2['rows_per_min']:,}/min inserted={m2['inserted']:,} dup_bk={m2['dup_bk']} (idempotent)")
    