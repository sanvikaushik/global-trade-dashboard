import os, time
from pathlib import Path
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed

import src.etl_extract_transform as etl  

def list_files() -> list[str]:
    raw_dir = etl.RAW_DIR 
    files = sorted(Path(raw_dir).glob("*.xml"))
    if not files:
        raise SystemExit(f"No XML files found in {raw_dir}")
    return [str(f) for f in files]

def parse_sequential(files: list[str]) -> pd.DataFrame:
    frames = [etl.read_one_xml(fp) for fp in files]
    return pd.concat(frames, ignore_index=True)

def parse_parallel(files: list[str], workers: int | None = None) -> pd.DataFrame:
    workers = workers or os.cpu_count() or 4
    frames = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(etl.read_one_xml, fp) for fp in files]
        for fut in as_completed(futures):
            df = fut.result()
            if df is not None and not df.empty:
                frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def time_it(fn, *args, label="run"):
    t0 = time.perf_counter()
    df = fn(*args)
    t1 = time.perf_counter()
    dt = t1 - t0
    rows = 0 if df is None or df.empty else len(df)
    print(f"{label:<20} -> {rows:>7} rows in {dt:6.2f}s")
    return dt, rows

if __name__ == "__main__":
    files = list_files()
    print(f"Files: {len(files)} in {etl.RAW_DIR}")

    _ = parse_sequential(files[:5])

    t_seq, n_seq = time_it(parse_sequential, files, label="sequential")

    t_par, n_par = time_it(parse_parallel, files, label="parallel")

    if t_par > 0:
        print(f"Speedup: {t_seq/t_par:,.2f}×  (rows equal? {n_seq == n_par})")
