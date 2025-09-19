import os, pandas as pd, streamlit as st, psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="Global Trade Dashboard", layout="wide")
PG=dict(host=os.getenv("PG_HOST","127.0.0.1"),port=int(os.getenv("PG_PORT",5432)),
        dbname=os.getenv("PG_DB","trade"),user=os.getenv("PG_USER","postgres"),
        password=os.getenv("PG_PASSWORD","postgres"))

@st.cache_data(ttl=300)
def q(sql, params=None):
    with psycopg2.connect(**PG) as c, c.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params or {})
        return pd.DataFrame(cur.fetchall())

st.title("🌍 Global Trade Analytics")
m1, m2, m3 = st.columns(3)
m1.metric("Rows", int(q("select count(*) rows from fact_trades").iloc[0]["rows"]))
m2.metric("Last Load", str(q("select max(load_ts) last from fact_trades").iloc[0]["last"]))
m3.metric("Dup BKs", int(q("select count(*) dup from (select bk from fact_trades group by bk having count(*)>1)t").iloc[0]["dup"]))

st.subheader("Top partners (last 12m)")
st.dataframe(q("""
select reporter_iso2, partner_iso2, sum(value_usd) usd
from fact_trades where trade_date >= (current_date - interval '12 months')
group by 1,2 order by usd desc limit 25
"""))

st.subheader("Monthly trend")
rep = st.text_input("Reporter ISO2", "CA")
prt = st.text_input("Partner ISO2 (optional)", "")
trend = q("""
select date_trunc('month', trade_date)::date month, sum(value_usd) usd
from fact_trades
where reporter_iso2=%(r)s and (%(p)s='' or partner_iso2=%(p)s)
group by 1 order by 1
""", {"r": rep, "p": prt})
if not trend.empty: st.line_chart(trend.set_index("month")["usd"])
