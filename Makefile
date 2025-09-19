.PHONY: etl load schema check app

etl: ; python src/etl_extract_transform.py
load: ; python src/load_to_postgres.py
schema: ; psql -h 127.0.0.1 -U postgres -d trade -f sql/schema.sql
check: ; psql -h 127.0.0.1 -U postgres -d trade -c "select count(*) rows, max(load_ts) last from fact_trades;"
app: ; streamlit run app.py
