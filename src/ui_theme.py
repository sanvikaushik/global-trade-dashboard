"""Bloomberg-style color themes and terminal CSS for the trade dashboard."""

from __future__ import annotations

from string import Template

THEMES: dict[str, dict] = {
    "BLOOMBERG": {
        "name": "BLOOMBERG",
        "bg": "#050505",
        "panel": "#0C0C0C",
        "panel2": "#141414",
        "border": "#2C2C2C",
        "accent": "#FF9F1A",
        "accent2": "#FFC857",
        "text": "#E6E6E6",
        "muted": "#8D8D8D",
        "up": "#3DFF8A",
        "down": "#FF4D4D",
        "warn": "#FFE08A",
        "grid": "rgba(255,159,26,0.07)",
        "input": "#101010",
        "header": "#000000",
        "shadow": "0 0 0 1px #2C2C2C",
        "tape": "#FF9F1A",
        "plot_grid": "#1F1F1F",
        "ink": "#050505",
        "header_fg": "#E6E6E6",
        "header_muted": "#8D8D8D",
        "cs0": "#1A0C00",
        "cs1": "#C45C00",
        "cs2": "#FFD28A",
    },
    "AMBER": {
        "name": "AMBER",
        "bg": "#0A0803",
        "panel": "#120E06",
        "panel2": "#1A1408",
        "border": "#3A2E14",
        "accent": "#FFB000",
        "accent2": "#FFD36A",
        "text": "#F3E2B8",
        "muted": "#A6894A",
        "up": "#B8FF64",
        "down": "#FF6B4A",
        "warn": "#FFE9A8",
        "grid": "rgba(255,176,0,0.08)",
        "input": "#140F05",
        "header": "#070501",
        "shadow": "0 0 0 1px #3A2E14",
        "tape": "#FFB000",
        "plot_grid": "#2A220E",
        "ink": "#120E06",
        "header_fg": "#F3E2B8",
        "header_muted": "#A6894A",
        "cs0": "#1A1200",
        "cs1": "#C48A00",
        "cs2": "#FFE7A0",
    },
    "MIDNIGHT": {
        "name": "MIDNIGHT",
        "bg": "#070B14",
        "panel": "#0C1422",
        "panel2": "#121C2E",
        "border": "#24344C",
        "accent": "#4CC9F0",
        "accent2": "#BDE8F7",
        "text": "#E8F1F8",
        "muted": "#7E93AB",
        "up": "#5CFFB0",
        "down": "#FF6B8A",
        "warn": "#FFE08A",
        "grid": "rgba(76,201,240,0.07)",
        "input": "#0A1220",
        "header": "#05080F",
        "shadow": "0 0 0 1px #24344C",
        "tape": "#4CC9F0",
        "plot_grid": "#1B2A40",
        "ink": "#05080F",
        "header_fg": "#E8F1F8",
        "header_muted": "#7E93AB",
        "cs0": "#041018",
        "cs1": "#1B7FA3",
        "cs2": "#8CE9FF",
    },
    "EQUITY": {
        "name": "EQUITY",
        "bg": "#06110C",
        "panel": "#0B1A13",
        "panel2": "#10241A",
        "border": "#1E3D2C",
        "accent": "#2EE59D",
        "accent2": "#A6FFD6",
        "text": "#DFF7EA",
        "muted": "#6F9A82",
        "up": "#6CFFB2",
        "down": "#FF5D6C",
        "warn": "#E8F07A",
        "grid": "rgba(46,229,157,0.07)",
        "input": "#08150F",
        "header": "#040C08",
        "shadow": "0 0 0 1px #1E3D2C",
        "tape": "#2EE59D",
        "plot_grid": "#163325",
        "ink": "#040C08",
        "header_fg": "#DFF7EA",
        "header_muted": "#6F9A82",
        "cs0": "#03140C",
        "cs1": "#0E8A5B",
        "cs2": "#9CFFD3",
    },
    "ICE": {
        "name": "ICE",
        "bg": "#EEF2F6",
        "panel": "#FFFFFF",
        "panel2": "#F7F9FB",
        "border": "#D5DEE8",
        "accent": "#0B3A6E",
        "accent2": "#C45500",
        "text": "#122033",
        "muted": "#5C6B7A",
        "up": "#0B8F55",
        "down": "#C62828",
        "warn": "#B45309",
        "grid": "rgba(11,58,110,0.05)",
        "input": "#FFFFFF",
        "header": "#FFFFFF",
        "shadow": "0 1px 2px rgba(15,35,55,0.06)",
        "tape": "#C45500",
        "plot_grid": "#E1E7EE",
        "ink": "#FFFFFF",
        "header_fg": "#122033",
        "header_muted": "#5C6B7A",
        "cs0": "#E8EEF5",
        "cs1": "#3D6FA3",
        "cs2": "#0B3A6E",
    },
}

CSS = Template(
    """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg: $bg;
  --panel: $panel;
  --panel2: $panel2;
  --border: $border;
  --accent: $accent;
  --accent2: $accent2;
  --text: $text;
  --muted: $muted;
  --up: $up;
  --down: $down;
  --warn: $warn;
  --grid: $grid;
  --input: $input;
  --header: $header;
  --tape: $tape;
  --ink: $ink;
  --header-fg: $header_fg;
  --header-muted: $header_muted;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace !important;
}

.stApp {
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px) !important;
  background-size: 56px 56px !important;
  background-color: var(--bg) !important;
}

header[data-testid="stHeader"],
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
#MainMenu, footer, .stDeployButton, .stAppDeployButton {
  display: none !important;
  visibility: hidden !important;
}

.block-container {
  padding: 0.55rem 0.8rem 1.1rem !important;
  max-width: 100% !important;
  overflow-x: hidden !important;
}

[data-testid="stVerticalBlock"] { gap: 0.42rem !important; }
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }

h1, h2, h3, p, label, span, div, .stMarkdown {
  font-family: "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace !important;
}

.stSelectbox label, .stTextInput label, [data-testid="stWidgetLabel"] {
  color: var(--muted) !important;
  font-size: 10px !important;
  letter-spacing: 0.14em !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
  background: var(--input) !important;
  color: var(--accent) !important;
  border: 1px solid var(--border) !important;
  border-radius: 2px !important;
  font-family: "IBM Plex Mono", monospace !important;
  font-size: 12px !important;
  font-weight: 600 !important;
}

[data-testid="stSelectbox"] svg { fill: var(--accent) !important; }

div[data-testid="stSegmentedControl"] button,
div[data-testid="stSegmentedControl"] label,
div[data-testid="stButtonGroup"] button {
  background: var(--panel) !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
  border-radius: 2px !important;
  font-size: 11px !important;
  letter-spacing: 0.08em !important;
  font-weight: 600 !important;
}

div[data-testid="stSegmentedControl"] button[aria-checked="true"],
div[data-testid="stSegmentedControl"] [data-checked="true"],
div[data-testid="stSegmentedControl"] label[data-selected="true"],
div[data-testid="stButtonGroup"] button[kind="primary"] {
  background: var(--accent) !important;
  color: var(--ink) !important;
  border-color: var(--accent) !important;
}

[data-testid="stPlotlyChart"], .stPlotlyChart, [data-testid="stDataFrame"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: 2px !important;
}

[data-testid="stHorizontalBlock"] > div { min-width: 0 !important; }

[data-testid="stTextInput"] input::placeholder {
  color: var(--muted) !important;
  opacity: 0.55 !important;
  font-weight: 400 !important;
}

[data-testid="stDataFrame"] { overflow: hidden; }

[data-testid="stVerticalBlockBorderWrapper"]:has(.gt-tape) ,
[data-testid="stVerticalBlockBorderWrapper"]:has(.gt-kpis) {
  border: none !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.gt-tape) [style*="overflow"],
[data-testid="stVerticalBlockBorderWrapper"]:has(.gt-kpis) [style*="overflow"] {
  overflow: hidden !important;
}
[data-testid="stMarkdownContainer"] { padding: 0 !important; }
[data-testid="stMarkdownContainer"] > p { margin: 0 !important; }
[data-testid="stMarkdownContainer"]:has(.gt-top) { min-height: 58px !important; }
[data-testid="stMarkdownContainer"]:has(.gt-tape) { min-height: 40px !important; }
[data-testid="stMarkdownContainer"]:has(.gt-kpis) { min-height: 112px !important; }
[data-testid="stMarkdownContainer"]:has(.gt-tblwrap) { min-height: 280px !important; }
[data-testid="stMarkdownContainer"]:has(.gt-bar) { min-height: 36px !important; }

iframe { background: transparent !important; }

hr { border-color: var(--border) !important; margin: 0.2rem 0 !important; }

/* Terminal chrome */
.gt-top {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 12px;
  background: var(--header);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  padding: 8px 12px;
  max-width: 100%;
  box-sizing: border-box;
}
.gt-brand { display: flex; align-items: baseline; gap: 10px; min-width: 280px; }
.gt-logo {
  background: var(--accent);
  color: var(--ink);
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.08em;
  padding: 3px 7px;
}
.gt-name { color: var(--accent); font-size: 18px; font-weight: 700; letter-spacing: 0.18em; }
.gt-go { color: var(--warn); font-size: 12px; font-weight: 700; }
.gt-meta { display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 2px; }
.gt-clock { color: var(--header-fg); font-size: 13px; font-weight: 600; letter-spacing: 0.08em; }
.gt-sub { color: var(--header-muted); font-size: 10px; letter-spacing: 0.12em; }
.gt-live { display: flex; align-items: center; gap: 14px; color: var(--header-muted); font-size: 11px; letter-spacing: 0.12em; }
.gt-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--up);
  box-shadow: 0 0 8px var(--up);
  animation: gt-pulse 1.6s ease-in-out infinite;
  display: inline-block;
}
@keyframes gt-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
.gt-chip {
  border: 1px solid var(--border);
  padding: 2px 7px;
  color: var(--accent);
  background: var(--panel);
}

.gt-tape {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border);
  background: var(--panel);
  height: 32px;
  min-height: 32px;
  margin: 0 0 8px;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
}
.gt-tape-lbl {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  z-index: 2;
  width: 72px;
  color: var(--ink);
  background: var(--tape);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-align: center;
  display: flex; align-items: center; justify-content: center;
}
.gt-tape-track {
  position: absolute;
  left: 72px;
  top: 0;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 28px;
  white-space: nowrap;
  animation: gt-scroll 38s linear infinite;
  padding-left: 16px;
  color: var(--text);
  font-size: 12px;
  font-weight: 500;
  will-change: transform;
}
.gt-tape-track b { color: var(--accent); font-weight: 700; }
.gt-up { color: var(--up) !important; }
.gt-dn { color: var(--down) !important; }
@keyframes gt-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.gt-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 8px;
  max-width: 100%;
}
.gt-kpi {
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 10px 12px 9px;
  min-height: 86px;
  position: relative;
}
.gt-kpi::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--accent);
}
.gt-kpi .lbl {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.16em;
  font-weight: 600;
}
.gt-kpi .val {
  color: var(--text);
  font-size: 22px;
  font-weight: 700;
  margin-top: 6px;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}
.gt-kpi .chg {
  margin-top: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.gt-kpi .hint { color: var(--muted); font-size: 10px; }

.gt-ptitle {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  padding: 2px 2px 6px;
}
.gt-ptitle span { color: var(--muted); font-weight: 500; letter-spacing: 0.08em; }

.gt-tblwrap {
  background: var(--panel);
  border: 1px solid var(--border);
  overflow: auto;
  max-height: 320px;
}
table.gt-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
table.gt-tbl th {
  position: sticky; top: 0;
  background: var(--panel2);
  color: var(--accent);
  text-align: left;
  font-size: 10px;
  letter-spacing: 0.14em;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  font-weight: 700;
}
table.gt-tbl th.r, table.gt-tbl td.r { text-align: right; }
table.gt-tbl td {
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
  white-space: nowrap;
}
table.gt-tbl tr:hover td { background: var(--panel2); color: var(--accent2); }
table.gt-tbl .dim { color: var(--muted); }

.gt-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid var(--border);
  background: var(--header);
  padding: 6px 10px;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.12em;
}
.gt-fk { color: var(--accent); font-weight: 700; padding: 0 6px; }
.gt-fk em { color: var(--muted); font-style: normal; font-weight: 500; margin-left: 4px; }

.gt-empty {
  border: 1px dashed var(--border);
  color: var(--muted);
  padding: 28px;
  text-align: center;
  letter-spacing: 0.16em;
}

@media (max-width: 1200px) {
  .gt-kpis { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 760px) {
  .gt-kpis { grid-template-columns: repeat(2, 1fr); }
  .gt-top { flex-direction: column; }
}
"""
)


def inject_css(theme_name: str) -> str:
    theme = THEMES.get(theme_name, THEMES["BLOOMBERG"])
    return f"<style>{CSS.substitute(theme)}</style>"
