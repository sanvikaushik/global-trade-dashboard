BEGIN;

DROP VIEW IF EXISTS v_monthly_trade CASCADE;
DROP VIEW IF EXISTS v_top_partners_last_12m CASCADE;
DROP TABLE IF EXISTS fact_trades CASCADE;

CREATE TABLE fact_trades (
  bk TEXT PRIMARY KEY,
  record_hash TEXT,
  trade_date DATE NOT NULL,
  reporter_iso2 TEXT NOT NULL,
  partner_iso2 TEXT NOT NULL,
  commodity_code TEXT NOT NULL,
  currency_code TEXT,
  value_numeric NUMERIC,
  quantity_numeric NUMERIC,
  unit TEXT,
  fx_rate_to_usd NUMERIC,
  value_usd NUMERIC,
  load_ts TIMESTAMPTZ,
  source_file TEXT NOT NULL,
  source_filesize BIGINT NOT NULL,
  source_mtime TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_trades(trade_date);
CREATE INDEX IF NOT EXISTS idx_fact_reporter_partner ON fact_trades(reporter_iso2, partner_iso2);
CREATE INDEX IF NOT EXISTS idx_fact_commodity ON fact_trades(commodity_code);

-- QA views
CREATE OR REPLACE VIEW v_monthly_trade AS
SELECT date_trunc('month', trade_date)::date AS month,
       reporter_iso2, partner_iso2, commodity_code,
       sum(value_usd) AS usd, sum(quantity_numeric) AS qty
FROM fact_trades
GROUP BY 1,2,3,4;

CREATE OR REPLACE VIEW v_top_partners_last_12m AS
SELECT reporter_iso2, partner_iso2, sum(value_usd) AS usd
FROM fact_trades
WHERE trade_date >= (current_date - interval '12 months')
GROUP BY 1,2
ORDER BY usd DESC;

CREATE TABLE IF NOT EXISTS etl_audit (
  id BIGSERIAL PRIMARY KEY,
  batch_ts TIMESTAMPTZ NOT NULL DEFAULT now(),
  source_files TEXT[],
  row_count INT,
  notes JSONB
);

COMMIT;
