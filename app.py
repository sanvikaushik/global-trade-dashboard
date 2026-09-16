from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.ui_theme import THEMES, inject_css

ROOT = Path(__file__).resolve().parent
PROC = ROOT / "data" / "processed"
TZ = ZoneInfo("America/New_York")

COMMODITY_MNEM = {
    "0808": "APPLE",
    "1006": "RICE",
    "2709": "CRUDE",
    "8703": "AUTOS",
}
st.set_page_config(
    page_title="GT TRADE <GO>",
    page_icon="🟧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if st.session_state.get("theme_name") not in THEMES:
    st.session_state.theme_name = "BLOOMBERG"


def ui(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def fmt_usd(n: float | int | None, digits: int = 2) -> str:
    if n is None or pd.isna(n):
        return "-"
    n = float(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1e12:
        return f"{sign}${n/1e12:.{digits}f}T"
    if n >= 1e9:
        return f"{sign}${n/1e9:.{digits}f}B"
    if n >= 1e6:
        return f"{sign}${n/1e6:.{digits}f}M"
    if n >= 1e3:
        return f"{sign}${n/1e3:.1f}K"
    return f"{sign}${n:,.0f}"


def fmt_int(n) -> str:
    if n is None or pd.isna(n):
        return "-"
    return f"{int(n):,}"


def fmt_pct(n: float | None) -> str:
    if n is None or pd.isna(n):
        return "n/a"
    return f"{n:+.1f}%"


def mnem(code: str) -> str:
    return COMMODITY_MNEM.get(str(code), str(code))


def try_postgres() -> pd.DataFrame | None:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception:
        return None
    kwargs = dict(
        host=os.getenv("PG_HOST", "127.0.0.1"),
        port=int(os.getenv("PG_PORT", 5432)),
        dbname=os.getenv("PG_DB", "trade"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        connect_timeout=2,
    )
    try:
        with psycopg2.connect(**kwargs) as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                select bk, record_hash, trade_date, reporter_iso2, partner_iso2,
                       commodity_code, currency_code, value_numeric, quantity_numeric,
                       unit, fx_rate_to_usd, value_usd, load_ts, source_file
                from fact_trades
                """
            )
            rows = cur.fetchall()
        if not rows:
            return None
        return pd.DataFrame(rows)
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_fact() -> tuple[pd.DataFrame, str]:
    pg = try_postgres()
    if pg is not None and not pg.empty:
        df, src = pg, "POSTGRES"
    else:
        path = PROC / "fact_trades.parquet"
        if not path.exists():
            return pd.DataFrame(), "EMPTY"
        df, src = pd.read_parquet(path), "PARQUET"

    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
    df["load_ts"] = pd.to_datetime(df["load_ts"], utc=True, errors="coerce")
    for col in ["value_usd", "value_numeric", "quantity_numeric", "fx_rate_to_usd"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "value_usd" not in df.columns:
        df["value_usd"] = df["value_numeric"] * df["fx_rate_to_usd"]
    df = df.dropna(subset=["trade_date", "reporter_iso2", "partner_iso2", "value_usd"])
    return df, src


def parse_mnemonic(raw: str, reporters, partners, comms) -> dict:
    out = {}
    if not raw:
        return out
    tokens = raw.upper().replace("<GO>", "").replace("/", " ").replace("→", " ").split()
    used_rep = False
    for tok in tokens:
        mapped = next((c for c, n in COMMODITY_MNEM.items() if n == tok), None)
        if tok in comms or mapped:
            out["commodity"] = mapped or tok
        elif tok in reporters and not used_rep:
            out["reporter"] = tok
            used_rep = True
        elif tok in partners:
            out["partner"] = tok
        elif tok in {"7D", "30D", "MAX"}:
            out["window"] = tok
    return out


def window_slice(df: pd.DataFrame, window: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df, df
    end = df["trade_date"].max()
    if window == "7D":
        days = 7
    elif window == "30D":
        days = 30
    else:
        span = (end - df["trade_date"].min()).days or 1
        days = max(span // 2, 1)
    cur_start = end - pd.Timedelta(days=days)
    prev_start = cur_start - pd.Timedelta(days=days)
    current = df[df["trade_date"] >= cur_start]
    prior = df[(df["trade_date"] >= prev_start) & (df["trade_date"] < cur_start)]
    if window == "MAX":
        current = df
    return current, prior


def delta(cur: float, prev: float) -> float | None:
    if prev in (0, None) or pd.isna(prev) or prev == 0:
        return None
    return (cur - prev) / prev * 100.0


def chg_html(pct: float | None) -> str:
    if pct is None:
        return '<div class="chg hint">NO PRIOR</div>'
    cls = "gt-up" if pct >= 0 else "gt-dn"
    arrow = "▲" if pct >= 0 else "▼"
    return f'<div class="chg {cls}">{arrow} {fmt_pct(pct)} VS PRIOR</div>'


def plot_layout(fig: go.Figure, theme: dict, title: str, height: int = 280) -> go.Figure:
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=11, color=theme["accent"], family="IBM Plex Mono"),
            x=0.01,
            y=0.98,
        ),
        paper_bgcolor=theme["panel"],
        plot_bgcolor=theme["panel"],
        font=dict(color=theme["text"], family="IBM Plex Mono", size=11),
        height=height,
        margin=dict(l=48, r=16, t=36, b=36),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=1,
            xanchor="right",
            font=dict(size=10, color=theme["muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            gridcolor=theme["plot_grid"],
            linecolor=theme["border"],
            tickfont=dict(color=theme["muted"], size=10),
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=theme["plot_grid"],
            linecolor=theme["border"],
            tickfont=dict(color=theme["muted"], size=10),
            zeroline=False,
            separatethousands=True,
        ),
        hoverlabel=dict(font=dict(family="IBM Plex Mono", size=11)),
        coloraxis_colorbar=dict(tickfont=dict(color=theme["muted"], size=10)),
    )
    return fig


def fig_trend(daily: pd.DataFrame, theme: dict) -> go.Figure:
    fig = go.Figure()
    if daily.empty:
        return plot_layout(fig, theme, "TRADE VALUE", 300)
    fig.add_trace(
        go.Scatter(
            x=daily["trade_date"],
            y=daily["value_usd"],
            mode="lines",
            name="USD",
            line=dict(color=theme["accent"], width=2),
            fill="tozeroy",
            fillcolor=theme["accent"].replace(")", ",0.18)").replace("rgb", "rgba")
            if theme["accent"].startswith("rgb")
            else hex_alpha(theme["accent"], 0.16),
            hovertemplate="%{x|%d %b %y}<br>%{y:$,.0f}<extra></extra>",
        )
    )
    if len(daily) >= 5:
        ma = daily["value_usd"].rolling(7, min_periods=3).mean()
        fig.add_trace(
            go.Scatter(
                x=daily["trade_date"],
                y=ma,
                mode="lines",
                name="7D MA",
                line=dict(color=theme["accent2"], width=1.4, dash="dot"),
                hovertemplate="MA %{y:$,.0f}<extra></extra>",
            )
        )
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return plot_layout(fig, theme, "", 300)


def fig_sankey(df: pd.DataFrame, theme: dict) -> go.Figure:
    routes = (
        df.groupby(["reporter_iso2", "partner_iso2"], as_index=False)["value_usd"]
        .sum()
        .sort_values("value_usd", ascending=False)
        .head(18)
    )
    fig = go.Figure()
    if routes.empty:
        return plot_layout(fig, theme, "", 300)
    left = [f"{r} RPT" for r in routes["reporter_iso2"]]
    right = [f"{p} PRT" for p in routes["partner_iso2"]]
    labels = list(dict.fromkeys(left + right))
    idx = {n: i for i, n in enumerate(labels)}
    node_color = [
        theme["accent"] if "RPT" in lab else hex_alpha(theme["accent2"], 0.75) for lab in labels
    ]
    fig.add_trace(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=[lab.replace(" RPT", "").replace(" PRT", "") for lab in labels],
                pad=18,
                thickness=14,
                color=node_color,
                line=dict(color=theme["border"], width=0.5),
            ),
            link=dict(
                source=[idx[a] for a in left],
                target=[idx[b] for b in right],
                value=routes["value_usd"],
                color=[hex_alpha(theme["accent"], 0.28)] * len(routes),
                hovertemplate="%{source.label} → %{target.label}<br>%{value:$,.0f}<extra></extra>",
            ),
        )
    )
    return plot_layout(fig, theme, "", 300)


def fig_heatmap(df: pd.DataFrame, theme: dict) -> go.Figure:
    pivot = df.pivot_table(
        index="reporter_iso2",
        columns="partner_iso2",
        values="value_usd",
        aggfunc="sum",
        fill_value=0,
    )
    fig = go.Figure()
    if pivot.empty:
        return plot_layout(fig, theme, "", 300)
    text = pivot.map(lambda v: fmt_usd(v, 1) if v else "")
    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=list(pivot.columns),
            y=list(pivot.index),
            colorscale=[
                [0, theme["cs0"]],
                [0.55, theme["cs1"]],
                [1, theme["cs2"]],
            ],
            text=text.values,
            texttemplate="%{text}",
            textfont=dict(family="IBM Plex Mono", size=11, color=theme["text"]),
            hovertemplate="RPT %{y} / PRT %{x}<br>%{z:$,.0f}<extra></extra>",
            colorbar=dict(thickness=10, outlinewidth=0, tickfont=dict(color=theme["muted"], size=10)),
        )
    )
    fig.update_xaxes(title="PARTNER", side="top")
    fig.update_yaxes(title="REPORTER", autorange="reversed")
    return plot_layout(fig, theme, "", 300)


def fig_commodities(df: pd.DataFrame, theme: dict) -> go.Figure:
    g = (
        df.groupby("commodity_code", as_index=False)["value_usd"]
        .sum()
        .sort_values("value_usd", ascending=True)
    )
    g["label"] = g["commodity_code"].map(lambda c: f"{c} {mnem(c)}")
    fig = go.Figure(
        go.Bar(
            x=g["value_usd"],
            y=g["label"],
            orientation="h",
            marker=dict(color=theme["accent"]),
            hovertemplate="%{y}<br>%{x:$,.0f}<extra></extra>",
        )
    )
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    fig.update_layout(margin=dict(l=90, r=16, t=36, b=36))
    return plot_layout(fig, theme, "", 300)


def hex_alpha(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return hex_color
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def blotter_html(df: pd.DataFrame, avg_usd: float, n: int = 18) -> str:
    rows = df.sort_values("trade_date", ascending=False).head(n)
    body = []
    for r in rows.itertuples(index=False):
        cls = "gt-up" if r.value_usd >= avg_usd else "gt-dn"
        route = f"{r.reporter_iso2}/{r.partner_iso2}"
        body.append(
            "<tr>"
            f"<td>{pd.Timestamp(r.trade_date).strftime('%d %b %y').upper()}</td>"
            f"<td>{route}</td>"
            f"<td>{r.commodity_code} {mnem(r.commodity_code)}</td>"
            f"<td class='r {cls}'>{fmt_usd(r.value_usd)}</td>"
            f"<td>{getattr(r, 'currency_code', '') or '-'}</td>"
            f"<td class='r dim'>{fmt_int(getattr(r, 'quantity_numeric', None))}</td>"
            f"<td class='dim'>{getattr(r, 'unit', '') or ''}</td>"
            "</tr>"
        )
    return (
        "<div class='gt-tblwrap'><table class='gt-tbl'>"
        "<thead><tr>"
        "<th>DATE</th><th>ROUTE</th><th>CMDTY</th>"
        "<th class='r'>USD</th><th>CCY</th><th class='r'>QTY</th><th>UNIT</th>"
        "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def routes_html(df: pd.DataFrame, total: float) -> str:
    g = (
        df.groupby(["reporter_iso2", "partner_iso2"], as_index=False)["value_usd"]
        .sum()
        .sort_values("value_usd", ascending=False)
        .head(12)
    )
    body = []
    for i, r in enumerate(g.itertuples(index=False), 1):
        share = (r.value_usd / total * 100) if total else 0
        body.append(
            "<tr>"
            f"<td class='dim'>{i:02d}</td>"
            f"<td>{r.reporter_iso2}/{r.partner_iso2}</td>"
            f"<td class='r'>{fmt_usd(r.value_usd)}</td>"
            f"<td class='r dim'>{share:.1f}%</td>"
            "</tr>"
        )
    return (
        "<div class='gt-tblwrap'><table class='gt-tbl'>"
        "<thead><tr><th>#</th><th>PAIR</th><th class='r'>USD</th><th class='r'>WGT</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


# ── data ──────────────────────────────────────────────────────────────────
fact, source = load_fact()

now = datetime.now(TZ)
clock = now.strftime("%a %d %b %Y  %H:%M:%S %Z").upper()

theme_name = st.session_state.theme_name if st.session_state.get("theme_name") in THEMES else "BLOOMBERG"
theme = THEMES[theme_name]
st.markdown(inject_css(theme_name), unsafe_allow_html=True)

# ── header ────────────────────────────────────────────────────────────────
range_lbl = "NO DATA"
if not fact.empty:
    range_lbl = (
        f"{fact['trade_date'].min().strftime('%d %b %y').upper()} - "
        f"{fact['trade_date'].max().strftime('%d %b %y').upper()}"
    )

ui(
    f"""
    <div class="gt-top">
      <div class="gt-brand">
        <span class="gt-logo">GT</span>
        <span class="gt-name">TRADE</span>
        <span class="gt-go">&lt;GO&gt;</span>
      </div>
      <div class="gt-live">
        <span><span class="gt-dot"></span> LIVE</span>
        <span class="gt-chip">{source}</span>
        <span class="gt-chip">{fmt_int(len(fact))} PRINTS</span>
        <span>{range_lbl}</span>
      </div>
      <div class="gt-meta">
        <div class="gt-clock">{clock}</div>
        <div class="gt-sub">GLOBAL TRADE TERMINAL · USD</div>
      </div>
    </div>
    """
)

# ── controls ──────────────────────────────────────────────────────────────
reporters = ["ALL"] + sorted(fact["reporter_iso2"].dropna().unique().tolist()) if not fact.empty else ["ALL"]
partners = ["ALL"] + sorted(fact["partner_iso2"].dropna().unique().tolist()) if not fact.empty else ["ALL"]
commodities = ["ALL"] + sorted(fact["commodity_code"].dropna().unique().tolist()) if not fact.empty else ["ALL"]

c_cmd, c_rep, c_prt, c_cmdty, c_win = st.columns([2.4, 1, 1, 1.3, 0.9])
with c_cmd:
    mnemonic = st.text_input("MNEMONIC", placeholder="CA US CRUDE 30D", label_visibility="visible")
with c_rep:
    reporter = st.selectbox("REPORTER", reporters, index=0)
with c_prt:
    partner = st.selectbox("PARTNER", partners, index=0)
with c_cmdty:
    labels = [
        c if c == "ALL" else f"{c} {COMMODITY_MNEM.get(c, c)}"
        for c in commodities
    ]
    cmdty_lbl = st.selectbox("CMDTY", labels, index=0)
    commodity = "ALL" if cmdty_lbl == "ALL" else cmdty_lbl.split()[0]
with c_win:
    window = st.selectbox("WINDOW", ["30D", "7D", "MAX"], index=0)

ws, th = st.columns([1.35, 1])
with ws:
    workspace = st.segmented_control(
        "WORKSPACE",
        options=["MONITOR", "FLOW", "MATRIX", "BLOTTER", "QUALITY"],
        default="MONITOR",
        label_visibility="collapsed",
    )
with th:
    st.segmented_control(
        "COLOR",
        options=list(THEMES),
        key="theme_name",
        label_visibility="collapsed",
    )

parsed = parse_mnemonic(mnemonic, set(reporters), set(partners), set(commodities))
reporter = parsed.get("reporter", reporter)
partner = parsed.get("partner", partner)
commodity = parsed.get("commodity", commodity)
window = parsed.get("window", window)

# ── filter ────────────────────────────────────────────────────────────────
base = fact.copy()
if reporter != "ALL":
    base = base[base["reporter_iso2"] == reporter]
if partner != "ALL":
    base = base[base["partner_iso2"] == partner]
if commodity != "ALL":
    base = base[base["commodity_code"] == commodity]
current, prior = window_slice(base, window)

# ── ticker ────────────────────────────────────────────────────────────────
if not current.empty:
    tape_src = (
        current.groupby(["reporter_iso2", "partner_iso2", "commodity_code"], as_index=False)["value_usd"]
        .sum()
        .sort_values("value_usd", ascending=False)
        .head(10)
    )
    items = []
    for r in tape_src.itertuples(index=False):
        items.append(
            f"{r.reporter_iso2}/{r.partner_iso2} <b>{mnem(r.commodity_code)}</b> "
            f"{fmt_usd(r.value_usd)} <span class='gt-up'>▲</span>"
        )
    tape = " &nbsp;·&nbsp; ".join(items)
    with st.container(height=48, border=False):
        ui(
            f"""
            <div class="gt-tape">
              <div class="gt-tape-lbl">TAPE</div>
              <div class="gt-tape-track">{tape}&nbsp;&nbsp;·&nbsp;&nbsp;{tape}</div>
            </div>
            """
        )

# ── KPIs ──────────────────────────────────────────────────────────────────
usd = float(current["value_usd"].sum()) if not current.empty else 0.0
usd_p = float(prior["value_usd"].sum()) if not prior.empty else 0.0
n_prints = int(len(current))
n_prints_p = int(len(prior))
n_routes = int(current.groupby(["reporter_iso2", "partner_iso2"]).ngroups) if not current.empty else 0
n_routes_p = int(prior.groupby(["reporter_iso2", "partner_iso2"]).ngroups) if not prior.empty else 0
n_cmdty = int(current["commodity_code"].nunique()) if not current.empty else 0
avg_ticket = usd / n_prints if n_prints else 0.0
avg_ticket_p = usd_p / n_prints_p if n_prints_p else 0.0
top_cmd = current.groupby("commodity_code")["value_usd"].sum().sort_values(ascending=False)
top_cmd_code = top_cmd.index[0] if len(top_cmd) else "-"
top_cmd_usd = float(top_cmd.iloc[0]) if len(top_cmd) else 0.0
dups = int(fact.duplicated("bk").sum()) if not fact.empty and "bk" in fact.columns else 0
last_load = "-"
if not fact.empty and "load_ts" in fact.columns and fact["load_ts"].notna().any():
    last_load = pd.to_datetime(fact["load_ts"].max()).strftime("%d %b %H:%M").upper()

with st.container(height=120, border=False):
    ui(
        f"""
        <div class="gt-kpis">
          <div class="gt-kpi">
            <div class="lbl">GROSS TRADE</div>
            <div class="val">{fmt_usd(usd)}</div>
            {chg_html(delta(usd, usd_p))}
          </div>
          <div class="gt-kpi">
            <div class="lbl">PRINTS</div>
            <div class="val">{fmt_int(n_prints)}</div>
            {chg_html(delta(n_prints, n_prints_p))}
          </div>
          <div class="gt-kpi">
            <div class="lbl">AVG TICKET</div>
            <div class="val">{fmt_usd(avg_ticket)}</div>
            {chg_html(delta(avg_ticket, avg_ticket_p))}
          </div>
          <div class="gt-kpi">
            <div class="lbl">ACTIVE ROUTES</div>
            <div class="val">{fmt_int(n_routes)}</div>
            {chg_html(delta(n_routes, n_routes_p))}
          </div>
          <div class="gt-kpi">
            <div class="lbl">LEAD CMDTY</div>
            <div class="val">{mnem(top_cmd_code) if top_cmd_code != "-" else "-"}</div>
            <div class="chg hint">{top_cmd_code} · {fmt_usd(top_cmd_usd)} · {n_cmdty} NAMES</div>
          </div>
          <div class="gt-kpi">
            <div class="lbl">DATA QUALITY</div>
            <div class="val">{'CLEAN' if dups == 0 else f'{dups} DUP'}</div>
            <div class="chg hint">LOAD {last_load} · BK DUP {dups}</div>
          </div>
        </div>
        """
    )

if current.empty:
    ui("<div class='gt-empty'>NO PRINTS FOR SELECTED MNEMONIC</div>")
    st.stop()

daily = (
    current.assign(trade_day=current["trade_date"].dt.normalize())
    .groupby("trade_day", as_index=False)["value_usd"]
    .sum()
    .rename(columns={"trade_day": "trade_date"})
    .sort_values("trade_date")
)
avg_usd = float(current["value_usd"].mean())
cfg = {"displayModeBar": False, "responsive": True}

if workspace in (None, "MONITOR"):
    left, right = st.columns([1.45, 1])
    with left:
        ui("<div class='gt-ptitle'>01  TRADE VALUE <span>DAILY USD · 7D MA</span></div>")
        st.plotly_chart(fig_trend(daily, theme), width="stretch", config=cfg, theme=None)
    with right:
        ui("<div class='gt-ptitle'>02  TOP ROUTES <span>REPORTER / PARTNER</span></div>")
        ui(routes_html(current, usd))
    b1, b2 = st.columns(2)
    with b1:
        ui("<div class='gt-ptitle'>03  COMMODITY STACK <span>GROSS USD</span></div>")
        st.plotly_chart(fig_commodities(current, theme), width="stretch", config=cfg, theme=None)
    with b2:
        ui("<div class='gt-ptitle'>04  BLOTTER <span>LATEST PRINTS VS AVG TICKET</span></div>")
        ui(blotter_html(current, avg_usd, 12))

elif workspace == "FLOW":
    ui("<div class='gt-ptitle'>05  TRADE FLOW <span>REPORTER → PARTNER · USD</span></div>")
    st.plotly_chart(fig_sankey(current, theme), width="stretch", config=cfg, theme=None)
    c1, c2 = st.columns(2)
    with c1:
        ui("<div class='gt-ptitle'>02  TOP ROUTES</div>")
        ui(routes_html(current, usd))
    with c2:
        ui("<div class='gt-ptitle'>03  COMMODITY STACK</div>")
        st.plotly_chart(fig_commodities(current, theme), width="stretch", config=cfg, theme=None)

elif workspace == "MATRIX":
    ui("<div class='gt-ptitle'>06  CORRESPONDENT MATRIX <span>REPORTER × PARTNER USD</span></div>")
    st.plotly_chart(fig_heatmap(current, theme), width="stretch", config=cfg, theme=None)
    ui("<div class='gt-ptitle'>05  TRADE FLOW</div>")
    st.plotly_chart(fig_sankey(current, theme), width="stretch", config=cfg, theme=None)

elif workspace == "BLOTTER":
    ui("<div class='gt-ptitle'>04  TRADE BLOTTER <span>ALL PRINTS IN WINDOW · GREEN ≥ AVG TICKET</span></div>")
    show = current.sort_values("trade_date", ascending=False).copy()
    show["ROUTE"] = show["reporter_iso2"] + "/" + show["partner_iso2"]
    show["CMDTY"] = show["commodity_code"].map(lambda c: f"{c} {mnem(c)}")
    show["DATE"] = show["trade_date"].dt.strftime("%Y-%m-%d")
    cols = ["DATE", "ROUTE", "CMDTY", "value_usd", "currency_code", "quantity_numeric", "unit", "fx_rate_to_usd"]
    present = [c for c in cols if c in show.columns]
    table = show[present].rename(
        columns={
            "value_usd": "USD",
            "currency_code": "CCY",
            "quantity_numeric": "QTY",
            "unit": "UNIT",
            "fx_rate_to_usd": "FX",
        }
    )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=520,
        column_config={
            "USD": st.column_config.NumberColumn(format="$%.0f"),
            "QTY": st.column_config.NumberColumn(format="%.0f"),
            "FX": st.column_config.NumberColumn(format="%.3f"),
        },
    )

else:
    src_files = sorted(fact["source_file"].dropna().unique().tolist()) if "source_file" in fact.columns else []
    n_src = len(src_files)
    missing = int(fact[["trade_date", "reporter_iso2", "partner_iso2", "commodity_code", "value_usd"]].isna().sum().sum())
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        ui(
            f"<div class='gt-kpi'><div class='lbl'>FACT ROWS</div><div class='val'>{fmt_int(len(fact))}</div>"
            f"<div class='chg hint'>WINDOW {fmt_int(len(current))}</div></div>"
        )
    with q2:
        ui(
            f"<div class='gt-kpi'><div class='lbl'>DUP BUSINESS KEYS</div><div class='val'>{fmt_int(dups)}</div>"
            f"<div class='chg hint'>{'PASS' if dups == 0 else 'FAIL'}</div></div>"
        )
    with q3:
        ui(
            f"<div class='gt-kpi'><div class='lbl'>SOURCE FILES</div><div class='val'>{fmt_int(n_src)}</div>"
            f"<div class='chg hint'>NULL CELLS {fmt_int(missing)}</div></div>"
        )
    with q4:
        ui(
            f"<div class='gt-kpi'><div class='lbl'>LAST LOAD</div><div class='val' style='font-size:18px'>{last_load}</div>"
            f"<div class='chg hint'>{source}</div></div>"
        )
    ui("<div class='gt-ptitle'>07  LINEAGE <span>SOURCE FILE</span></div>")
    if src_files:
        agg = {"ROWS": ("bk", "count"), "USD": ("value_usd", "sum")}
        if "source_mtime" in fact.columns:
            agg["MTIME"] = ("source_mtime", "max")
        lineage = fact.groupby("source_file", as_index=False).agg(**agg).sort_values("USD", ascending=False)
        lineage["USD"] = lineage["USD"].map(lambda v: fmt_usd(v))
        if "MTIME" in lineage.columns:
            lineage["MTIME"] = pd.to_datetime(lineage["MTIME"]).dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(lineage, use_container_width=True, hide_index=True, height=360)
    fx = (
        current.groupby("currency_code", as_index=False)
        .agg(PRINTS=("bk", "count"), USD=("value_usd", "sum"), FX=("fx_rate_to_usd", "mean"))
        .sort_values("USD", ascending=False)
    )
    ui("<div class='gt-ptitle'>08  CURRENCY MIX</div>")
    st.dataframe(
        fx,
        use_container_width=True,
        hide_index=True,
        column_config={
            "USD": st.column_config.NumberColumn(format="$%.0f"),
            "FX": st.column_config.NumberColumn(format="%.3f"),
        },
    )

ui(
    f"""
    <div class="gt-bar">
      <div>
        <span class="gt-fk">F8<em>MON</em></span>
        <span class="gt-fk">F9<em>FLOW</em></span>
        <span class="gt-fk">F10<em>MX</em></span>
        <span class="gt-fk">F11<em>BLT</em></span>
        <span class="gt-fk">F12<em>QA</em></span>
      </div>
      <div>{theme_name} · {source} · {reporter}/{partner if partner != 'ALL' else 'WLD'} · {commodity} · {window}</div>
    </div>
    """
)
