import time, pandas as pd
from pathlib import Path
from src.etl_extract_transform import read_one_xml, extract_all

RAW_DIR = Path("data/raw")

def sequential(files):
    dfs = []
    for f in files:
        dfs.append(read_one_xml(f))
    return pd.concat(dfs, ignore_index=True)

def benchmark():
    files = list(RAW_DIR.glob("*.xml")) * 500  

    t0 = time.time()
    df_seq = sequential(files)
    t1 = time.time()
    print(f"Sequential parse: {len(df_seq)} rows in {t1-t0:.2f}s")

    t0 = time.time()
    df_par = extract_all()  
    t1 = time.time()
    print(f"Parallel parse:   {len(df_par)} rows in {t1-t0:.2f}s")

if __name__ == "__main__":
    benchmark()
