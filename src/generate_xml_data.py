# src/generate_xml_data.py
from pathlib import Path
from datetime import date, timedelta
import random

OUT_DIR = Path("data/raw_bench")
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPORTERS = [("CA", "Canada"), ("US", "United States"), ("MX", "Mexico")]
PARTNERS  = [("US", "United States"), ("CA", "Canada"), ("MX", "Mexico"), ("CN", "China")]
COMMS     = [("2709", "Crude oil"), ("1006", "Rice"), ("8703", "Cars"), ("0808", "Apples")]
CURS      = [("USD", "US Dollar", 1.0), ("CAD", "Canadian Dollar", 0.74), ("MXN", "Mexican Peso", 0.058)]

def rand_date(start: date, days_window: int) -> date:
    """Pick a random date between start and min(start+window, today)."""
    today = date.today()
    end = min(start + timedelta(days=days_window - 1), today)
    if end < start:
        return today
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def make_record(d: date) -> str:
    rep_iso2, rep_name = random.choice(REPORTERS)
    par_iso2, par_name = random.choice(PARTNERS)
    comm_code, comm_name = random.choice(COMMS)
    cur_code, cur_name, fx = random.choice(CURS)

    value = random.randint(1_000_000, 100_000_000)
    qty   = random.randint(1000, 1_000_000)
    unit  = random.choice(["BBL", "KG", "Units"])

    return f"""
  <TradeRecord>
    <Date>{d}</Date>
    <Reporter>
      <ISO2>{rep_iso2}</ISO2>
      <Name>{rep_name}</Name>
    </Reporter>
    <Partner>
      <ISO2>{par_iso2}</ISO2>
      <Name>{par_name}</Name>
    </Partner>
    <Commodity>
      <Code>{comm_code}</Code>
      <Name>{comm_name}</Name>
    </Commodity>
    <Currency>
      <Code>{cur_code}</Code>
      <Name>{cur_name}</Name>
      <FxRateToUSD>{fx}</FxRateToUSD>
    </Currency>
    <Value>{value}</Value>
    <Quantity unit="{unit}">{qty}</Quantity>
  </TradeRecord>
    """.strip()

def write_batch(file_idx: int, records_per_file: int, start_date: date, days_window: int = 30):
    body = "\n".join(
        make_record(rand_date(start_date, days_window))
        for _ in range(records_per_file)
    )
    xml = f'<TradeBatch generated="{start_date.isoformat()}">\n{body}\n</TradeBatch>\n'
    (OUT_DIR / f"trade_{file_idx:04d}.xml").write_text(xml, encoding="utf-8")

def main(total_records=2000, records_per_file=100, seed=42, days_window: int = 70):
    random.seed(seed)
    files = (total_records + records_per_file - 1) // records_per_file
    start = date(2025, 8, 1)
    for i in range(files):
        write_batch(i+1, records_per_file, start, days_window=days_window)

if __name__ == "__main__":
    main()
