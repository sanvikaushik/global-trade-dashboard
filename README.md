# Global Trade Dashboard

Bloomberg-style terminal for global trade analytics. Color themes: Bloomberg, Amber, Midnight, Equity, Ice.

![GT TRADE terminal](docs/gt-trade-terminal.png)

## Run

```bash
make app
```

Or `streamlit run app.py`. The app loads Postgres when available, otherwise `data/processed/fact_trades.parquet`.
