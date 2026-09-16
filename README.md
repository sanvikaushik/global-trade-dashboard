# Global Trade Dashboard

Bloomberg-style terminal for global trade analytics. Color themes: Bloomberg, Amber, Midnight, Equity, Ice.

![GT TRADE terminal](docs/gt-trade-terminal.png)

The app loads Postgres when available, otherwise `data/processed/fact_trades.parquet`.

## Quick start
1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set Postgres connection variables as needed (`PG_HOST`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASSWORD`).
4. Prepare the database schema:
   ```bash
   make schema
   ```
5. Place source XML trade files in `data/raw/`, then extract and transform:
   ```bash
   make etl
   ```
6. Load processed data into Postgres:
   ```bash
   make load
   ```
7. Verify row counts and last load timestamp:
   ```bash
   make check
   ```
8. Launch the Streamlit dashboard:
   ```bash
   make app
   ```

Or `streamlit run app.py`.

## Components
- **ETL** (`src/etl_extract_transform.py`, `src/load_to_postgres.py`): Streams XML trade files, deduplicates on business keys, and loads fact rows into the `fact_trades` table.
- **Dashboard** (`app.py`): Bloomberg-style trade terminal with mnemonic filters, workspaces (MONITOR, FLOW, MATRIX, BLOTTER, QUALITY), and switchable color themes. Falls back to parquet when Postgres is unavailable.
- **Utilities** (`src/utils.py`, `src/validate.py`, `src/measure_quality.py`): Shared helpers for stable IDs, schema validation, and quality checks.

## Make targets
- `make schema`: Apply database schema from `sql/schema.sql`.
- `make etl`: Run extract/transform pipeline on raw XML files.
- `make load`: Bulk load processed parquet/csv outputs into Postgres.
- `make check`: Confirm row counts and latest load timestamp in `fact_trades`.
- `make app`: Launch the Streamlit UI for interactive exploration.
