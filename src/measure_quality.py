from __future__ import annotations
import os
import pandas as pd
from src.etl_extract_transform import extract_all, build_dims
from src.validate import validate_fact_with_stats

def main():
    df = extract_all()
    _, _, _, fact = build_dims(df)

    total = len(fact)

    valid, invalid, failures = validate_fact_with_stats(fact)

    n_valid   = len(valid)
    n_invalid = len(invalid)
    pct_block = (n_invalid / total * 100.0) if total else 0.0

    print("\n******* Data Quality Metrics *******")
    print(f"Total rows processed          : {total:,}")
    print(f"Rows passed validation        : {n_valid:,}")
    print(f"Rows blocked by validation    : {n_invalid:,}  ({pct_block:.2f}%)")

    if total:
        print(f"Approx. downstream issues avoided: ~{pct_block:.2f}% of batch")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "data", "qa")
    os.makedirs(out_dir, exist_ok=True)
    if n_invalid:
        invalid.to_parquet(os.path.join(out_dir, "invalid_fact.parquet"), index=False)
        failures.to_csv(os.path.join(out_dir, "pandera_failures.csv"), index=False)
        print(f"\nSaved invalid rows -> {out_dir}/invalid_fact.parquet")
        print(f"Saved failure details -> {out_dir}/pandera_failures.csv")

if __name__ == "__main__":
    main()
