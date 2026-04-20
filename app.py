"""
╔══════════════════════════════════════════════════════════════════════╗
║  अर्थगवन — ARTHGAVANA                                                ║
║  Indian Market Net P&L Intelligence System                          ║
║  Hemrek Capital                                                      ║
║                                                                      ║
║  Sanskrit: अर्थगवन (Arthgavana) — "the finding/reckoning of wealth." ║
║  A complete post-charges, post-tax P&L reconciliation engine for     ║
║  the Indian cash + F&O markets.                                      ║
║                                                                      ║
║  Design Thesis: Nirnay / Pragyam — Dark + Gold                      ║
╚══════════════════════════════════════════════════════════════════════╝

Charges & Tax Stack (India, FY 2025-26 / FY 2026-27 rates):

    1. Brokerage        — broker-dependent, ₹20 or 0.03% (whichever lower)
    2. STT              — 0.02% sell (FUT), 0.10% sell premium (OPT),
                          0.10% both sides (Equity Delivery),
                          0.025% sell (Equity Intraday)
    3. Exchange charges — 0.00173% (NSE FUT), 0.03503% (NSE OPT),
                          0.00297% (Equity)
    4. SEBI turnover    — ₹10 / crore = 0.0001%
    5. Stamp duty       — buy side only: 0.002% FUT / 0.003% OPT /
                          0.015% Delivery / 0.003% Intraday
    6. GST 18%          — on (brokerage + exchange + SEBI)
    7. Income tax       — F&O as non-speculative business @ slab
                          Intraday as speculative @ slab
                          STCG 20% (post 23-Jul-2024)
                          LTCG 12.5% above ₹1.25L exemption
"""

from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Arthgavana | Hemrek Capital",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM — Nirnay / Hemrek Dark + Gold
# ══════════════════════════════════════════════════════════════════════

HEMREK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

:root {
    --bg-primary:     #0a0a0f;
    --bg-secondary:   #12121a;
    --bg-tertiary:    #1a1a25;
    --bg-card:        #15151f;
    --bg-elevated:    #1c1c28;
    --accent-gold:        #d4af37;
    --accent-gold-light:  #f4d03f;
    --accent-gold-dark:   #b08e2d;
    --accent-emerald:     #10b981;
    --accent-emerald-soft:#059669;
    --accent-ruby:        #ef4444;
    --accent-ruby-soft:   #dc2626;
    --accent-sapphire:    #3b82f6;
    --accent-amethyst:    #8b5cf6;
    --text-primary:   #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted:     #64748b;
    --text-whisper:   #475569;
    --border-subtle:  rgba(255,255,255,0.06);
    --border-soft:    rgba(255,255,255,0.10);
    --border-accent:  rgba(212,175,55,0.30);
    --border-gold:    rgba(212,175,55,0.45);
    --gradient-gold:  linear-gradient(135deg,#d4af37 0%,#f4d03f 50%,#d4af37 100%);
    --gradient-dark:  linear-gradient(180deg,#0a0a0f 0%,#12121a 100%);
    --gradient-card:  linear-gradient(135deg,#15151f 0%,#1c1c28 100%);
    --shadow-gold:    0 0 40px rgba(212,175,55,0.15);
    --shadow-card:    0 4px 24px rgba(0,0,0,0.4);
    --shadow-lift:    0 8px 32px rgba(0,0,0,0.5);
}

/* ── App shell ─────────────────────────────────────────────── */
.stApp {
    background: var(--gradient-dark);
    font-family: 'Outfit', sans-serif;
    color: var(--text-primary);
}
.block-container {
    padding-top: 3.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}
/* Keep the Streamlit header transparent so the sidebar toggle and
   collapse button remain clickable, but hide the menu and deploy chrome. */
header[data-testid="stHeader"] {
    background: transparent !important;
    backdrop-filter: none !important;
    height: auto !important;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton, [data-testid="stDecoration"] { display: none !important; }
/* Force sidebar toggle button to be visible and on top */
button[data-testid="stSidebarCollapseButton"],
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    color: var(--accent-gold) !important;
    z-index: 999999 !important;
}

/* ── Sidebar ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-subtle);
}
section[data-testid="stSidebar"] > div { padding-top: 1rem; }

/* ── Headers ───────────────────────────────────────────────── */
.hemrek-brand {
    font-family: 'Outfit', sans-serif;
    font-size: 3.4rem;
    font-weight: 800;
    background: var(--gradient-gold);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    line-height: 1.25;
    padding-top: 0.4rem;
    margin: 0;
    overflow: visible;
}
.hemrek-tagline {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-muted);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin-top: 0.35rem;
}
.hemrek-section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--accent-gold);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    margin: 2rem 0 0.9rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-accent);
}
.hemrek-subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    font-weight: 400;
}

/* ── Metric cards ──────────────────────────────────────────── */
.hk-metric {
    background: var(--gradient-card);
    border: 1px solid var(--border-subtle);
    border-radius: 14px;
    padding: 22px 24px;
    box-shadow: var(--shadow-card);
    transition: all 0.25s ease;
    height: 100%;
}
.hk-metric:hover {
    border-color: var(--border-accent);
    box-shadow: var(--shadow-gold);
    transform: translateY(-2px);
}
.hk-metric-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-muted);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hk-metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.hk-metric-value.gold    { color: var(--accent-gold); }
.hk-metric-value.green   { color: var(--accent-emerald); }
.hk-metric-value.red     { color: var(--accent-ruby); }
.hk-metric-value.neutral { color: var(--text-primary); }
.hk-metric-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 6px;
    letter-spacing: 0.06em;
}

/* ── Waterfall / breakdown row ─────────────────────────────── */
.hk-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-subtle);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.92rem;
}
.hk-row:last-child { border-bottom: none; }
.hk-row .label { color: var(--text-secondary); }
.hk-row .value { color: var(--text-primary); font-weight: 500; }
.hk-row.total {
    background: rgba(212,175,55,0.06);
    border-top: 1px solid var(--border-accent);
    border-bottom: 1px solid var(--border-accent);
    padding: 16px;
    font-size: 1rem;
    font-weight: 700;
}
.hk-row.total .label { color: var(--accent-gold); letter-spacing: 0.06em; }
.hk-row.total .value { color: var(--accent-gold); }
.hk-row.positive .value { color: var(--accent-emerald); }
.hk-row.negative .value { color: var(--accent-ruby); }

/* ── Info / note blocks ────────────────────────────────────── */
.hk-note {
    background: rgba(139,92,246,0.06);
    border-left: 3px solid var(--accent-amethyst);
    border-radius: 6px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.55;
}
.hk-note strong { color: var(--text-primary); }

.hk-warn {
    background: rgba(212,175,55,0.06);
    border-left: 3px solid var(--accent-gold);
    border-radius: 6px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.55;
}

/* ── Tabs ──────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg-secondary);
    padding: 6px;
    border-radius: 10px;
    border: 1px solid var(--border-subtle);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    border-radius: 7px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--bg-card) !important;
    color: var(--accent-gold) !important;
    box-shadow: 0 0 0 1px var(--border-accent);
}

/* ── Buttons ───────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-accent) !important;
    color: var(--accent-gold) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 10px 22px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: rgba(212,175,55,0.10) !important;
    border-color: var(--accent-gold) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-gold);
}

/* ── Inputs ────────────────────────────────────────────────── */
.stSelectbox > div > div, .stNumberInput > div > div > input,
.stTextInput > div > div > input {
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    color: var(--text-primary) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stFileUploader {
    background: var(--bg-card);
    border: 1.5px dashed var(--border-accent);
    border-radius: 10px;
    padding: 12px;
}

/* ── DataFrames / editors ──────────────────────────────────── */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    background: var(--bg-card);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 4px;
}

/* ── Dividers ──────────────────────────────────────────────── */
hr {
    border: none;
    height: 1px;
    background: var(--border-subtle);
    margin: 1.5rem 0;
}

/* ── Scrollbars ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-soft); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-gold-dark); }

/* ── Expander ──────────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    color: var(--text-secondary) !important;
}

/* ── Caption ───────────────────────────────────────────────── */
.caption {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
}
</style>
"""

st.markdown(HEMREK_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  INDIAN NUMBER FORMAT
# ══════════════════════════════════════════════════════════════════════

def fmt_inr(x: float, decimals: int = 2) -> str:
    """Indian lakh-crore comma format: 12,34,567.89"""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    sign = "-" if x < 0 else ""
    x = abs(x)
    formatted = f"{x:.{decimals}f}"
    if "." in formatted:
        int_part, dec_part = formatted.split(".")
    else:
        int_part, dec_part = formatted, ""
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        # Group remaining in 2s from the right
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        formatted_int = ",".join(groups) + "," + last3
    if decimals > 0 and dec_part:
        return f"{sign}₹{formatted_int}.{dec_part}"
    return f"{sign}₹{formatted_int}"


def fmt_inr_compact(x: float) -> str:
    """Compact Indian format: 2.3L / 1.25Cr."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    sign = "-" if x < 0 else ""
    a = abs(x)
    if a >= 1e7:
        return f"{sign}₹{a/1e7:,.2f} Cr"
    if a >= 1e5:
        return f"{sign}₹{a/1e5:,.2f} L"
    if a >= 1e3:
        return f"{sign}₹{a/1e3:,.2f} K"
    return f"{sign}₹{a:,.2f}"


def fmt_pct(x: float, decimals: int = 2) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    return f"{x*100:.{decimals}f}%"


# ══════════════════════════════════════════════════════════════════════
#  INSTRUMENT DETECTION + LOT SIZE LIBRARY
# ══════════════════════════════════════════════════════════════════════

# Conservative recent NSE F&O lot sizes (user-editable in app).
LOT_SIZES: dict[str, int] = {
    "NIFTY": 75, "BANKNIFTY": 35, "FINNIFTY": 65, "MIDCPNIFTY": 140,
    "SENSEX": 20, "BANKEX": 30, "NIFTYNXT50": 25,
    "RELIANCE": 500, "TCS": 175, "HDFCBANK": 550, "INFY": 400,
    "ICICIBANK": 700, "SBIN": 750, "HINDUNILVR": 300, "ITC": 1600,
    "BHARTIARTL": 475, "KOTAKBANK": 400, "LT": 300, "AXISBANK": 625,
    "MARUTI": 50, "ASIANPAINT": 200, "WIPRO": 2500, "NESTLEIND": 25,
    "ULTRACEMCO": 50, "HCLTECH": 350, "M&M": 350, "TITAN": 175,
    "BAJFINANCE": 125, "BAJAJFINSV": 500, "POWERGRID": 1800, "NTPC": 1500,
    "SUNPHARMA": 350, "TATAMOTORS": 1425, "TATASTEEL": 5500, "JSWSTEEL": 675,
    "COALINDIA": 2100, "ONGC": 9375, "IOC": 9750, "BPCL": 1800, "HINDALCO": 1400,
    "ADANIENT": 300, "ADANIPORTS": 850,
    "EICHERMOT": 175, "HEROMOTOCO": 300, "BAJAJ-AUTO": 75, "TVSMOTOR": 350,
    "ICICIPRULI": 925, "ICICIGI": 275, "HDFCLIFE": 1100, "SBILIFE": 375,
    "MANAPPURAM": 6000, "MUTHOOTFIN": 375, "PFC": 3000, "RECLTD": 2700,
    "SUPREMEIND": 400, "PIDILITIND": 250, "UBL": 400, "DABUR": 1250,
    "DIVISLAB": 125, "CIPLA": 650, "DRREDDY": 500, "APOLLOHOSP": 125,
    "HAVELLS": 500, "BATAINDIA": 375, "BIOCON": 2400, "IDEA": 70000,
    "VEDL": 1150, "GAIL": 3500, "GRASIM": 400, "PNB": 8000, "BANKBARODA": 2925,
    "PAYTM": 900, "ZOMATO": 3350, "IRCTC": 800, "LICHSGFIN": 1100,
    "INDUSINDBK": 500, "ADANIGREEN": 400, "TATAPOWER": 1350, "DMART": 150,
}


def detect_instrument_type(symbol: str) -> str:
    """Return one of: FUT, OPT, EQ (delivery/intraday distinguished by product)."""
    s = symbol.upper().replace(" ", "")
    if s.endswith("FUT"):
        return "FUT"
    if re.search(r"\d+(CE|PE)$", s):
        return "OPT"
    if s.endswith("CE") or s.endswith("PE"):
        return "OPT"
    return "EQ"


def detect_equity_segment(product: str) -> str:
    """CNC→Delivery, MIS→Intraday, NRML→FUT/OPT overnight (handled separately)."""
    p = (product or "").upper()
    if p in ("CNC",):
        return "DELIVERY"
    if p in ("MIS",):
        return "INTRADAY"
    return "DELIVERY"


def extract_underlying(symbol: str) -> str:
    """Strip expiry and FUT/OPT suffix from NSE instrument name.
    e.g. BHARTIARTL26MAYFUT → BHARTIARTL"""
    s = symbol.upper()
    # Remove FUT
    s = re.sub(r"\d+[A-Z]{3}FUT$", "", s)
    # Remove option — match expiry+strike+CE/PE
    s = re.sub(r"\d+[A-Z]{3}\d+(CE|PE)$", "", s)
    # Monthly option alternate format
    s = re.sub(r"\d{2}[A-Z]{3}\d+(CE|PE)$", "", s)
    # Weekly expiry formats YYMMDD
    s = re.sub(r"\d{2}\d{1,2}\d{1,2}\d+(CE|PE)$", "", s)
    return s


def guess_lot_size(symbol: str, inst_type: str) -> int:
    """Guess lot size from symbol. Equity = 1."""
    if inst_type == "EQ":
        return 1
    underlying = extract_underlying(symbol)
    return LOT_SIZES.get(underlying, 1)


# ══════════════════════════════════════════════════════════════════════
#  CHARGES ENGINE — India, FY 2025-26 / FY 2026-27
# ══════════════════════════════════════════════════════════════════════

@dataclass
class BrokerConfig:
    name: str
    # Equity Delivery
    eq_del_brok_pct: float = 0.0
    eq_del_brok_flat: float = 0.0
    eq_del_brok_max: float = 20.0
    # Equity Intraday
    eq_intra_brok_pct: float = 0.0003
    eq_intra_brok_flat: float = 20.0
    eq_intra_brok_max: float = 20.0
    # Futures
    fut_brok_pct: float = 0.0003
    fut_brok_flat: float = 20.0
    fut_brok_max: float = 20.0
    # Options
    opt_brok_flat: float = 20.0


BROKERS: dict[str, BrokerConfig] = {
    "Zerodha":   BrokerConfig("Zerodha"),
    "Upstox":    BrokerConfig("Upstox"),
    "Groww":     BrokerConfig("Groww", eq_del_brok_pct=0.001, eq_del_brok_max=20.0),
    "Angel One": BrokerConfig("Angel One"),
    "Dhan":      BrokerConfig("Dhan"),
    "Fyers":     BrokerConfig("Fyers"),
    "ICICI Direct (I-Secure)": BrokerConfig(
        "ICICI Direct", eq_del_brok_pct=0.00275, eq_del_brok_max=1e9,
        eq_intra_brok_pct=0.00275, eq_intra_brok_max=1e9,
        fut_brok_pct=0.0005, fut_brok_max=1e9, opt_brok_flat=95.0,
    ),
    "HDFC Securities": BrokerConfig(
        "HDFC Securities", eq_del_brok_pct=0.005, eq_del_brok_max=1e9,
        eq_intra_brok_pct=0.0005, eq_intra_brok_max=1e9,
        fut_brok_pct=0.00039, fut_brok_max=1e9, opt_brok_flat=100.0,
    ),
    "Custom":    BrokerConfig("Custom"),
}


@dataclass
class ChargeResult:
    brokerage:    float = 0.0
    stt:          float = 0.0
    exchange:     float = 0.0
    sebi:         float = 0.0
    stamp:        float = 0.0
    gst:          float = 0.0
    ipft:         float = 0.0  # investor protection fund

    @property
    def total(self) -> float:
        return self.brokerage + self.stt + self.exchange + self.sebi + self.stamp + self.gst + self.ipft

    def as_dict(self) -> dict[str, float]:
        return {
            "Brokerage": self.brokerage, "STT": self.stt,
            "Exchange Txn": self.exchange, "SEBI": self.sebi,
            "Stamp Duty": self.stamp, "GST": self.gst, "IPFT": self.ipft,
            "Total Charges": self.total,
        }


def compute_charges_for_leg(
    buy_value: float,
    sell_value: float,
    inst_type: str,
    product: str,
    broker: BrokerConfig,
) -> ChargeResult:
    """Compute all charges for a single round-trip (buy + sell) position."""
    turnover = buy_value + sell_value
    r = ChargeResult()

    # ── 1. Brokerage ────────────────────────────────────────────
    if inst_type == "OPT":
        # Options: one flat per side, if any side has value
        legs = (1 if buy_value > 0 else 0) + (1 if sell_value > 0 else 0)
        r.brokerage = broker.opt_brok_flat * legs
    elif inst_type == "FUT":
        b_brok = min(buy_value * broker.fut_brok_pct, broker.fut_brok_max) if buy_value > 0 else 0
        s_brok = min(sell_value * broker.fut_brok_pct, broker.fut_brok_max) if sell_value > 0 else 0
        r.brokerage = b_brok + s_brok
    else:  # EQ
        if product == "DELIVERY":
            b_brok = min(buy_value * broker.eq_del_brok_pct, broker.eq_del_brok_max) if buy_value > 0 else 0
            s_brok = min(sell_value * broker.eq_del_brok_pct, broker.eq_del_brok_max) if sell_value > 0 else 0
        else:  # INTRADAY
            b_brok = min(buy_value * broker.eq_intra_brok_pct, broker.eq_intra_brok_max) if buy_value > 0 else 0
            s_brok = min(sell_value * broker.eq_intra_brok_pct, broker.eq_intra_brok_max) if sell_value > 0 else 0
        r.brokerage = b_brok + s_brok

    # ── 2. STT (Securities Transaction Tax) — post Budget 2026, eff 1-Apr-26 ─
    if inst_type == "FUT":
        r.stt = sell_value * 0.0005        # 0.05% sell side (was 0.02% pre-Apr-26)
    elif inst_type == "OPT":
        r.stt = sell_value * 0.0015        # 0.15% on sell of premium (was 0.10%)
    else:
        if product == "DELIVERY":
            r.stt = (buy_value + sell_value) * 0.001  # 0.10% both sides (unchanged)
        else:  # INTRADAY
            r.stt = sell_value * 0.00025   # 0.025% sell side (unchanged)

    # ── 3. Exchange Transaction Charges (NSE, current rate card) ────────────
    if inst_type == "FUT":
        r.exchange = turnover * 0.0000183  # 0.00183%
    elif inst_type == "OPT":
        r.exchange = turnover * 0.0003553  # 0.03553% on premium turnover
    else:
        r.exchange = turnover * 0.0000307  # 0.00307%

    # ── 4. SEBI turnover fee ────────────────────────────────────
    r.sebi = turnover * 0.000001          # ₹10 / crore = 0.0001%

    # ── 5. Stamp Duty (buy side only) ───────────────────────────
    if inst_type == "FUT":
        r.stamp = buy_value * 0.00002     # 0.002%
    elif inst_type == "OPT":
        r.stamp = buy_value * 0.00003     # 0.003%
    else:
        if product == "DELIVERY":
            r.stamp = buy_value * 0.00015 # 0.015%
        else:
            r.stamp = buy_value * 0.00003 # 0.003%

    # ── 6. IPFT (Investor Protection Fund — ₹0.01 per crore) ────────────────
    # Very small: ₹0.01 / crore = 1e-9 of turnover.
    if inst_type in ("FUT", "OPT"):
        r.ipft = turnover * 1e-9

    # ── 7. GST @ 18% on (brokerage + exchange + SEBI) ───────────
    r.gst = 0.18 * (r.brokerage + r.exchange + r.sebi)

    return r


# ══════════════════════════════════════════════════════════════════════
#  INCOME TAX ENGINE (FY 2025-26 / FY 2026-27, New Regime default)
# ══════════════════════════════════════════════════════════════════════

def marginal_slab_tax_new(income_fo: float, existing_income: float, regime: str = "New") -> float:
    """Compute additional tax from F&O/intraday income given existing taxable income.

    Returns the MARGINAL tax = T(existing + fo) - T(existing).
    Uses New Regime FY 2025-26 slabs (₹4L / ₹8L / ₹12L / ₹16L / ₹20L / ₹24L).
    """
    if regime == "New":
        slabs = [
            (400000,  0.00),
            (800000,  0.05),
            (1200000, 0.10),
            (1600000, 0.15),
            (2000000, 0.20),
            (2400000, 0.25),
            (float("inf"), 0.30),
        ]
    else:  # Old regime
        slabs = [
            (250000,  0.00),
            (500000,  0.05),
            (1000000, 0.20),
            (float("inf"), 0.30),
        ]

    def _tax(income: float) -> float:
        if income <= 0: return 0.0
        remaining = income
        prev_cap = 0
        total = 0.0
        for cap, rate in slabs:
            slab_width = cap - prev_cap
            taxable_in_slab = min(remaining, slab_width)
            total += taxable_in_slab * rate
            remaining -= taxable_in_slab
            prev_cap = cap
            if remaining <= 0: break
        return total

    base = _tax(existing_income)
    new = _tax(existing_income + income_fo)
    return max(0.0, new - base)


def income_tax_on_pnl(
    fo_net: float,
    intraday_net: float,
    stcg: float,
    ltcg: float,
    existing_income: float,
    regime: str,
    cess_rate: float = 0.04,
) -> dict[str, float]:
    """Compute income tax across F&O, intraday, STCG, LTCG.

    F&O + Intraday → slab (marginal on top of existing income).
    STCG equity (Section 111A) → 20% (post 23-Jul-2024).
    LTCG equity (Section 112A) → 12.5% above ₹1.25L exemption.

    Losses: F&O and intraday net negatives are NOT taxed (assumed set off /
    carried forward); we floor at zero for tax purposes but track them.
    """
    # Business income (F&O is non-speculative, intraday is speculative but
    # both attract slab rates at individual level).
    slab_income = max(0.0, fo_net) + max(0.0, intraday_net)
    slab_tax = marginal_slab_tax_new(slab_income, existing_income, regime)
    slab_cess = slab_tax * cess_rate

    # STCG @ 20% flat (Section 111A, equity STT-paid)
    stcg_tax = max(0.0, stcg) * 0.20
    stcg_cess = stcg_tax * cess_rate

    # LTCG @ 12.5% above ₹1.25L exemption per year
    ltcg_taxable = max(0.0, ltcg - 125000)
    ltcg_tax = ltcg_taxable * 0.125
    ltcg_cess = ltcg_tax * cess_rate

    total_tax = slab_tax + stcg_tax + ltcg_tax
    total_cess = slab_cess + stcg_cess + ltcg_cess

    return {
        "slab_tax":    slab_tax,
        "slab_cess":   slab_cess,
        "stcg_tax":    stcg_tax,
        "stcg_cess":   stcg_cess,
        "ltcg_tax":    ltcg_tax,
        "ltcg_cess":   ltcg_cess,
        "total_tax":   total_tax,
        "total_cess":  total_cess,
        "grand_total": total_tax + total_cess,
    }


# ══════════════════════════════════════════════════════════════════════
#  CSV PARSER — auto-detect format (Zerodha Kite + generic)
# ══════════════════════════════════════════════════════════════════════

def parse_positions_csv(raw: bytes) -> pd.DataFrame:
    """Parse the uploaded CSV into a standard schema.

    Expected columns (Zerodha Kite positions export):
      Product, Instrument, Qty., Avg., LTP, P&L, Chg.
    """
    text = raw.decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]

    # Normalise common header variations.
    col_map = {}
    for c in df.columns:
        low = c.lower().strip()
        if low in ("product", "prod"): col_map[c] = "product"
        elif low.startswith("instrument") or low == "symbol" or low == "tradingsymbol": col_map[c] = "instrument"
        elif low in ("qty", "qty.", "quantity", "net qty"): col_map[c] = "qty"
        elif low in ("avg", "avg.", "avg price", "avg. price", "average price"): col_map[c] = "avg"
        elif low in ("ltp", "last price", "last"): col_map[c] = "ltp"
        elif low in ("p&l", "pnl", "p and l", "realized p&l", "realised p&l"): col_map[c] = "pnl"
        elif low in ("chg", "chg.", "change", "change %"): col_map[c] = "chg"
    df = df.rename(columns=col_map)

    # Drop junk rows
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(subset=["instrument"]) if "instrument" in df.columns else df
    if "instrument" in df.columns:
        df = df[df["instrument"].astype(str).str.strip() != ""]
        df = df[df["instrument"].astype(str).str.strip().str.lower() != "nan"]

    # Ensure numerics
    for col in ("qty", "avg", "ltp", "pnl", "chg"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df = df.reset_index(drop=True)
    return df


def build_editable_positions(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Take parsed CSV and produce the editable positions dataframe."""
    rows = []
    for _, r in raw_df.iterrows():
        sym = str(r.get("instrument", "")).strip().upper()
        if not sym: continue
        product_raw = str(r.get("product", "")).strip().upper()
        ltp = float(r.get("ltp", 0) or 0)
        pnl = float(r.get("pnl", 0) or 0)
        qty = float(r.get("qty", 0) or 0)
        avg = float(r.get("avg", 0) or 0)

        itype = detect_instrument_type(sym)
        # Map product to segment
        if itype in ("FUT", "OPT"):
            segment = "NRML" if product_raw == "NRML" else product_raw or "NRML"
        else:
            segment = detect_equity_segment(product_raw)

        lot_size = guess_lot_size(sym, itype)

        # Estimate num_lots + sell / buy values from LTP.
        # Convention: gross position size ≈ LTP × lot_size × 1 lot.
        # For fully-closed positions (qty=0), we assume roundtrip of 1 lot at
        # approx LTP and back out buy/sell from P&L.
        num_lots = 1
        if itype in ("FUT", "OPT"):
            base_size = ltp * lot_size * num_lots
            # Assume avg buy price ≈ LTP on entry, sell price = entry + P&L/(lot_size*num_lots)
            if base_size > 0:
                buy_value = base_size
                sell_value = base_size + pnl
            else:
                buy_value = sell_value = 0.0
        else:
            # Equity — if qty=0 and P&L is given, assume roundtrip of at
            # some estimated quantity. If avg is given, use it; else LTP.
            shares = max(1.0, abs(qty) if qty else 100.0)
            px = avg if avg > 0 else ltp
            buy_value = shares * px
            sell_value = buy_value + pnl
            num_lots = shares  # reuse field to mean "shares" for EQ

        # Enforce non-negative on sell_value if pnl is extreme
        sell_value = max(0.0, sell_value)
        buy_value = max(0.0, buy_value)

        rows.append({
            "Instrument":  sym,
            "Type":        itype,
            "Segment":     segment,
            "Lot Size":    int(lot_size) if itype != "EQ" else 1,
            "Qty/Lots":    int(num_lots) if itype != "EQ" else int(num_lots),
            "Buy Value":   round(buy_value, 2),
            "Sell Value":  round(sell_value, 2),
            "P&L (Gross)": round(pnl, 2),
            "LTP":         round(ltp, 2),
            "Include":     True,
        })
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
#  APP STATE
# ══════════════════════════════════════════════════════════════════════

if "positions_df" not in st.session_state:
    st.session_state.positions_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None

# ══════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════

col_h1, col_h2 = st.columns([5, 2])
with col_h1:
    st.markdown('<div class="hemrek-brand">अर्थगवन</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hemrek-tagline">ARTHGAVANA · NET P&L RECKONING ENGINE · '
        'HEMREK CAPITAL</div>',
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown(
        '<div style="text-align:right; padding-top:12px;">'
        '<div class="caption">INDIAN MARKETS · NSE / BSE</div>'
        '<div class="caption" style="margin-top:4px;">'
        'FY 2025-26 / FY 2026-27 RATES</div>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  SIDEBAR — Configuration
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div style="font-family:Outfit; font-size:1.35rem; font-weight:700; '
        'color:var(--accent-gold); margin-bottom:4px;">Configuration</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="caption" style="margin-bottom:1.5rem;">'
        'BROKER · TAX · REGIME</div>',
        unsafe_allow_html=True,
    )

    # Broker selection
    st.markdown('<div class="hemrek-section-title">Broker</div>', unsafe_allow_html=True)
    broker_name = st.selectbox(
        "Select your broker",
        list(BROKERS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    broker = BROKERS[broker_name]

    if broker_name == "Custom":
        with st.expander("Custom broker rates", expanded=True):
            broker.fut_brok_pct = st.number_input(
                "Futures brokerage %", 0.0, 1.0, 0.0003, 0.00005, format="%.5f",
            )
            broker.fut_brok_max = st.number_input(
                "Futures brokerage cap (₹)", 0.0, 10000.0, 20.0, 1.0,
            )
            broker.opt_brok_flat = st.number_input(
                "Options brokerage per leg (₹)", 0.0, 500.0, 20.0, 1.0,
            )
            broker.eq_del_brok_pct = st.number_input(
                "Equity delivery brokerage %", 0.0, 1.0, 0.0, 0.00005, format="%.5f",
            )
            broker.eq_intra_brok_pct = st.number_input(
                "Equity intraday brokerage %", 0.0, 1.0, 0.0003, 0.00005, format="%.5f",
            )

    # Tax regime
    st.markdown('<div class="hemrek-section-title">Income Tax</div>', unsafe_allow_html=True)
    tax_regime = st.radio(
        "Tax regime",
        ["New", "Old"],
        index=0,
        horizontal=True,
        help="New regime (FY 2025-26): ₹4L-12L exempt/5-10%, rising to 30% >₹24L.",
    )
    existing_income = st.number_input(
        "Existing annual income (₹)", 0.0, 100000000.0, 1500000.0, 50000.0,
        help="Salary + other income excluding trading P&L. Used for marginal slab.",
    )
    include_cess = st.checkbox("Include 4% Health & Education Cess", value=True)
    cess_rate = 0.04 if include_cess else 0.0

    # Financial Year
    st.markdown('<div class="hemrek-section-title">Period</div>', unsafe_allow_html=True)
    fy_label = st.selectbox(
        "Financial Year",
        ["FY 2026-27 (AY 2027-28)", "FY 2025-26 (AY 2026-27)"],
        index=0,
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        '<div class="caption" style="line-height:1.8;">'
        "RATE SOURCES<br>"
        "· SEBI ₹10/crore<br>"
        "· STT per CBDT<br>"
        "· Exchange per NSE circular<br>"
        "· Stamp duty post 2020 reforms<br>"
        "· GST @ 18%"
        "</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════
#  STEP 1 — UPLOAD
# ══════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="hemrek-section-title">01 · Positions Upload</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hemrek-subtitle">'
    "Upload your broker positions CSV — Zerodha Kite, Upstox, or any "
    "broker with columns for Instrument, Qty, LTP, and P&L. The system "
    "auto-detects futures, options, and equity segments."
    "</div>",
    unsafe_allow_html=True,
)

upload_col1, upload_col2 = st.columns([3, 1])
with upload_col1:
    up = st.file_uploader(
        "Drop positions.csv here",
        type=["csv"],
        label_visibility="collapsed",
    )
with upload_col2:
    use_demo = st.button("Use sample data", width='stretch')

if up is not None:
    try:
        raw = up.read()
        raw_df = parse_positions_csv(raw)
        st.session_state.raw_df = raw_df
        st.session_state.positions_df = build_editable_positions(raw_df)
    except Exception as exc:
        st.error(f"Could not parse CSV — {exc}")

if use_demo:
    demo_csv = (
        '"Product","Instrument","Qty.","Avg.","LTP","P&L","Chg.",""\n'
        '"NRML","BHARTIARTL26MAYFUT",0,0,1862.5,-5082.5,0,""\n'
        '"NRML","EICHERMOT26MAYFUT",0,0,7245.5,1350,0,""\n'
        '"NRML","HEROMOTOCO26MAYFUT",0,0,5308.5,-3000,0,""\n'
        '"NRML","ICICIPRULI26MAYFUT",0,0,560.05,1618.75,0,""\n'
        '"NRML","IOC26MAYFUT",0,0,146.44,1950,0,""\n'
        '"NRML","MANAPPURAM26MAYFUT",0,0,273.5,4500,0,""\n'
        '"NRML","NIFTY26MAYFUT",0,0,24570,8105.5,0,""\n'
        '"NRML","ONGC26MAYFUT",0,0,285.65,3487.5,0,""\n'
        '"NRML","SUPREMEIND26MAYFUT",0,0,3737.9,0,0,""\n'
    ).encode()
    raw_df = parse_positions_csv(demo_csv)
    st.session_state.raw_df = raw_df
    st.session_state.positions_df = build_editable_positions(raw_df)


# ══════════════════════════════════════════════════════════════════════
#  STEP 2 — POSITIONS TABLE (editable)
# ══════════════════════════════════════════════════════════════════════

if st.session_state.positions_df is None:
    st.markdown(
        '<div class="hk-note">'
        "<strong>No positions loaded yet.</strong><br>"
        "Upload a CSV above or click <em>Use sample data</em> to begin. "
        "The supported format is the standard Zerodha Kite Positions export "
        "(columns: Product, Instrument, Qty., Avg., LTP, P&L, Chg.). "
        "Once loaded, you can refine Buy Value / Sell Value per position "
        "before the engine computes all charges and taxes."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown(
    '<div class="hemrek-section-title">02 · Verify Position Economics</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="hemrek-subtitle">'
    "Estimates are computed from LTP × lot size. For precise charge "
    "computation, override <b>Buy Value</b> and <b>Sell Value</b> with "
    "your actual traded amounts. The P&L (Gross) column is auto-derived "
    "from Sell − Buy."
    "</div>",
    unsafe_allow_html=True,
)

edited = st.data_editor(
    st.session_state.positions_df,
    width='stretch',
    num_rows="dynamic",
    key="pos_editor",
    column_config={
        "Instrument":  st.column_config.TextColumn("Instrument", width="medium"),
        "Type":        st.column_config.SelectboxColumn(
            "Type", options=["FUT", "OPT", "EQ"], width="small",
        ),
        "Segment":     st.column_config.SelectboxColumn(
            "Segment", options=["NRML", "MIS", "CNC", "DELIVERY", "INTRADAY"],
            width="small",
        ),
        "Lot Size":    st.column_config.NumberColumn("Lot Size", min_value=1, width="small"),
        "Qty/Lots":    st.column_config.NumberColumn("Qty/Lots", min_value=0, width="small"),
        "Buy Value":   st.column_config.NumberColumn("Buy Value (₹)", format="%.2f"),
        "Sell Value":  st.column_config.NumberColumn("Sell Value (₹)", format="%.2f"),
        "P&L (Gross)": st.column_config.NumberColumn("P&L Gross (₹)", format="%.2f", disabled=True),
        "LTP":         st.column_config.NumberColumn("LTP", format="%.2f", disabled=True),
        "Include":     st.column_config.CheckboxColumn("Include", width="small"),
    },
)

# Recompute P&L from buy/sell and update state
edited = edited.copy()
edited["P&L (Gross)"] = edited["Sell Value"] - edited["Buy Value"]
st.session_state.positions_df = edited


# ══════════════════════════════════════════════════════════════════════
#  STEP 3 — COMPUTE CHARGES
# ══════════════════════════════════════════════════════════════════════

df = edited[edited["Include"]].reset_index(drop=True).copy()

if len(df) == 0:
    st.warning("No positions selected.")
    st.stop()

# Map segment → product for charge engine
def _segment_to_product(segment: str, inst_type: str) -> str:
    seg = (segment or "").upper()
    if inst_type in ("FUT", "OPT"):
        return "FO"
    if seg in ("MIS", "INTRADAY"):
        return "INTRADAY"
    return "DELIVERY"

rows_charges = []
for _, r in df.iterrows():
    prod = _segment_to_product(r["Segment"], r["Type"])
    cr = compute_charges_for_leg(
        buy_value=float(r["Buy Value"]),
        sell_value=float(r["Sell Value"]),
        inst_type=r["Type"],
        product=prod,
        broker=broker,
    )
    rows_charges.append({
        "Instrument": r["Instrument"],
        "Type":       r["Type"],
        "Turnover":   float(r["Buy Value"]) + float(r["Sell Value"]),
        **cr.as_dict(),
        "Net P&L":    float(r["P&L (Gross)"]) - cr.total,
        "P&L Gross":  float(r["P&L (Gross)"]),
    })

charges_df = pd.DataFrame(rows_charges)

# Totals / aggregates
gross_pnl    = float(charges_df["P&L Gross"].sum())
total_brok   = float(charges_df["Brokerage"].sum())
total_stt    = float(charges_df["STT"].sum())
total_exch   = float(charges_df["Exchange Txn"].sum())
total_sebi   = float(charges_df["SEBI"].sum())
total_stamp  = float(charges_df["Stamp Duty"].sum())
total_gst    = float(charges_df["GST"].sum())
total_ipft   = float(charges_df["IPFT"].sum())
total_charges = float(charges_df["Total Charges"].sum())
net_pretax   = gross_pnl - total_charges
total_turnover = float(charges_df["Turnover"].sum())

# Split by segment for taxation
fo_net       = float(charges_df[charges_df["Type"].isin(["FUT", "OPT"])]["Net P&L"].sum())
eq_df        = df[df["Type"] == "EQ"].copy()
eq_charges_df = charges_df[charges_df["Type"] == "EQ"].copy()
intraday_net = float(
    eq_charges_df[
        df.reset_index(drop=True).loc[eq_charges_df.index, "Segment"].isin(["MIS", "INTRADAY"])
    ]["Net P&L"].sum()
) if len(eq_charges_df) else 0.0

# STCG / LTCG for delivery equity — the app lets user tag holding period below
delivery_idx = df.index[(df["Type"] == "EQ") & (df["Segment"].isin(["CNC", "DELIVERY"]))]
delivery_charges = charges_df.loc[delivery_idx].copy() if len(delivery_idx) else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════
#  HEADLINE METRICS (4 cards)
# ══════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="hemrek-section-title">03 · Headline Reckoning</div>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)


def metric_card(label: str, value_html: str, sub: str, cls: str = "neutral") -> str:
    return (
        '<div class="hk-metric">'
        f'<div class="hk-metric-label">{label}</div>'
        f'<div class="hk-metric-value {cls}">{value_html}</div>'
        f'<div class="hk-metric-sub">{sub}</div>'
        '</div>'
    )


with m1:
    st.markdown(
        metric_card(
            "GROSS P&L",
            fmt_inr(gross_pnl),
            "before charges & tax",
            "green" if gross_pnl >= 0 else "red",
        ),
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        metric_card(
            "TOTAL CHARGES",
            fmt_inr(total_charges),
            f"{total_charges/total_turnover*100:.4f}% of turnover" if total_turnover > 0 else "—",
            "red",
        ),
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        metric_card(
            "NET P&L (PRE-TAX)",
            fmt_inr(net_pretax),
            "after brokerage, STT, GST, etc.",
            "green" if net_pretax >= 0 else "red",
        ),
        unsafe_allow_html=True,
    )
with m4:
    # Compute post-tax using defaults (detailed breakdown in the tab)
    tax_pkg = income_tax_on_pnl(
        fo_net=fo_net,
        intraday_net=intraday_net,
        stcg=0.0, ltcg=0.0,  # configurable in tab
        existing_income=existing_income,
        regime=tax_regime,
        cess_rate=cess_rate,
    )
    tax_headline = tax_pkg["grand_total"]
    net_post = net_pretax - tax_headline
    st.markdown(
        metric_card(
            "NET P&L (POST-TAX)",
            fmt_inr(net_post),
            f"after {fmt_inr_compact(tax_headline)} tax",
            "gold",
        ),
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════
#  TABS — the deep view
# ══════════════════════════════════════════════════════════════════════

tabs = st.tabs([
    "Waterfall",
    "Per-Position",
    "Charge Anatomy",
    "Tax Computation",
    "Export",
])

# ── TAB 1: Waterfall ──────────────────────────────────────────────────

with tabs[0]:
    st.markdown(
        '<div class="hemrek-section-title">P&L Waterfall · Gross → Net Post-Tax</div>',
        unsafe_allow_html=True,
    )

    # Build waterfall data
    wf_labels = [
        "Gross P&L", "Brokerage", "STT", "Exchange",
        "SEBI", "Stamp Duty", "GST", "IPFT",
        "Net Pre-Tax", "Income Tax", "Cess", "Net Post-Tax",
    ]
    wf_values = [
        gross_pnl, -total_brok, -total_stt, -total_exch,
        -total_sebi, -total_stamp, -total_gst, -total_ipft,
        None, -tax_pkg["total_tax"], -tax_pkg["total_cess"], None,
    ]
    wf_measure = [
        "absolute", "relative", "relative", "relative",
        "relative", "relative", "relative", "relative",
        "total", "relative", "relative", "total",
    ]

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=wf_measure,
        x=wf_labels,
        y=wf_values,
        textposition="outside",
        text=[fmt_inr_compact(v) if v is not None else "" for v in wf_values],
        connector={"line": {"color": "rgba(148,163,184,0.3)"}},
        increasing={"marker": {"color": "#10b981"}},
        decreasing={"marker": {"color": "#ef4444"}},
        totals={"marker": {"color": "#d4af37"}},
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#94a3b8"),
        height=480,
        margin=dict(t=30, b=50, l=30, r=30),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.15)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig, width='stretch')

    st.markdown(
        '<div class="hemrek-section-title">Ledger</div>',
        unsafe_allow_html=True,
    )

    ledger = [
        ("Gross P&L",              gross_pnl,           "positive" if gross_pnl >= 0 else "negative"),
        ("  Brokerage",           -total_brok,          "negative"),
        ("  STT",                 -total_stt,           "negative"),
        ("  Exchange Transaction",-total_exch,          "negative"),
        ("  SEBI Turnover Fee",   -total_sebi,          "negative"),
        ("  Stamp Duty",          -total_stamp,         "negative"),
        ("  GST @ 18%",           -total_gst,           "negative"),
        ("  IPFT",                -total_ipft,          "negative"),
        ("Net P&L (Pre-Tax)",      net_pretax,          "total"),
        ("  Slab Tax",            -tax_pkg["slab_tax"], "negative"),
        ("  STCG Tax",            -tax_pkg["stcg_tax"], "negative"),
        ("  LTCG Tax",            -tax_pkg["ltcg_tax"], "negative"),
        ("  Health & Edu Cess",   -tax_pkg["total_cess"],"negative"),
        ("Net P&L (Post-Tax)",     net_pretax - tax_pkg["grand_total"], "total"),
    ]
    for label, val, cls in ledger:
        st.markdown(
            f'<div class="hk-row {cls}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{fmt_inr(val)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="hk-note">'
        "<strong>Read the waterfall:</strong> each red step shows how a "
        "statutory or broker charge carves into the gross P&L. Green steps "
        "represent gains. The gold totals mark the two critical anchors "
        "— your pre-tax net (after all trade frictions) and post-tax net "
        "(your actual take-home). The gap between them is the cost of "
        "doing business in Indian markets."
        "</div>",
        unsafe_allow_html=True,
    )


# ── TAB 2: Per-Position ───────────────────────────────────────────────

with tabs[1]:
    st.markdown(
        '<div class="hemrek-section-title">Per-Position Breakdown</div>',
        unsafe_allow_html=True,
    )

    display_df = charges_df.copy()
    display_df["P&L Net %"] = (display_df["Net P&L"] / display_df["Turnover"].replace(0, np.nan) * 100).fillna(0)

    format_dict = {
        "Turnover":     lambda x: fmt_inr(x, 0),
        "Brokerage":    lambda x: fmt_inr(x),
        "STT":          lambda x: fmt_inr(x),
        "Exchange Txn": lambda x: fmt_inr(x),
        "SEBI":         lambda x: fmt_inr(x),
        "Stamp Duty":   lambda x: fmt_inr(x),
        "GST":          lambda x: fmt_inr(x),
        "IPFT":         lambda x: fmt_inr(x),
        "Total Charges":lambda x: fmt_inr(x),
        "P&L Gross":    lambda x: fmt_inr(x),
        "Net P&L":      lambda x: fmt_inr(x),
        "P&L Net %":    lambda x: f"{x:.3f}%",
    }
    styled = display_df.style.format(format_dict).set_properties(**{
        "background-color": "#15151f",
        "color": "#f8fafc",
        "border-color": "rgba(255,255,255,0.06)",
    }).apply(
        lambda col: [
            "color:#10b981" if isinstance(v, (int, float)) and v > 0 else
            ("color:#ef4444" if isinstance(v, (int, float)) and v < 0 else "")
            for v in col
        ],
        subset=["P&L Gross", "Net P&L"],
    )
    st.dataframe(styled, width='stretch', hide_index=True)

    # Contribution chart
    st.markdown(
        '<div class="hemrek-section-title">P&L Contribution by Position</div>',
        unsafe_allow_html=True,
    )
    sorted_df = charges_df.sort_values("Net P&L", ascending=True)
    fig2 = go.Figure(go.Bar(
        x=sorted_df["Net P&L"],
        y=sorted_df["Instrument"],
        orientation="h",
        marker_color=[
            "#10b981" if v >= 0 else "#ef4444" for v in sorted_df["Net P&L"]
        ],
        text=[fmt_inr_compact(v) for v in sorted_df["Net P&L"]],
        textposition="outside",
    ))
    fig2.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#94a3b8"),
        height=max(320, 38 * len(sorted_df)),
        margin=dict(t=20, b=40, l=20, r=60),
        xaxis=dict(
            title="Net P&L (₹)",
            gridcolor="rgba(255,255,255,0.05)",
            zerolinecolor="rgba(255,255,255,0.2)",
        ),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig2, width='stretch')


# ── TAB 3: Charge Anatomy ─────────────────────────────────────────────

with tabs[2]:
    st.markdown(
        '<div class="hemrek-section-title">Charge Anatomy · Composition</div>',
        unsafe_allow_html=True,
    )

    col_pie, col_bar = st.columns([1, 1])

    charge_buckets = {
        "Brokerage":       total_brok,
        "STT":             total_stt,
        "Exchange Txn":    total_exch,
        "SEBI":            total_sebi,
        "Stamp Duty":      total_stamp,
        "GST":             total_gst,
        "IPFT":            total_ipft,
    }
    charge_buckets = {k: v for k, v in charge_buckets.items() if v > 0}

    palette = ["#d4af37", "#ef4444", "#3b82f6", "#10b981", "#8b5cf6", "#f4d03f", "#64748b"]

    with col_pie:
        fig3 = go.Figure(go.Pie(
            labels=list(charge_buckets.keys()),
            values=list(charge_buckets.values()),
            hole=0.62,
            marker=dict(colors=palette[:len(charge_buckets)],
                        line=dict(color="#0a0a0f", width=2)),
            textinfo="label+percent",
            textfont=dict(family="JetBrains Mono, monospace", size=11, color="#f8fafc"),
            hovertemplate="<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        fig3.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono, monospace", color="#94a3b8"),
            height=400,
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=False,
            annotations=[dict(
                text=f"<b>₹{total_charges:,.0f}</b><br><span style='font-size:10px;color:#64748b'>TOTAL</span>",
                x=0.5, y=0.5, font_size=18, showarrow=False,
                font=dict(family="JetBrains Mono, monospace", color="#d4af37"),
            )],
        )
        st.plotly_chart(fig3, width='stretch')

    with col_bar:
        sorted_buckets = sorted(charge_buckets.items(), key=lambda x: x[1], reverse=True)
        fig4 = go.Figure(go.Bar(
            x=[v for _, v in sorted_buckets],
            y=[k for k, _ in sorted_buckets],
            orientation="h",
            marker_color="#d4af37",
            text=[fmt_inr_compact(v) for _, v in sorted_buckets],
            textposition="outside",
        ))
        fig4.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono, monospace", size=11, color="#94a3b8"),
            height=400,
            margin=dict(t=20, b=40, l=20, r=80),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig4, width='stretch')

    st.markdown(
        '<div class="hemrek-section-title">Rate Card Applied</div>',
        unsafe_allow_html=True,
    )

    rate_md = """
| Charge | Equity Delivery | Equity Intraday | Futures | Options |
|--------|----------------|-----------------|---------|---------|
| Brokerage | Free (Zerodha etc.) | ₹20 / 0.03% (min) | ₹20 / 0.03% (min) | ₹20 flat / leg |
| STT | 0.10% both sides | 0.025% sell | 0.05% sell | 0.15% sell premium |
| Exchange Txn (NSE) | 0.00307% | 0.00307% | 0.00183% | 0.03553% of premium |
| SEBI | 0.0001% (₹10/cr) | 0.0001% | 0.0001% | 0.0001% |
| Stamp Duty (buy) | 0.015% | 0.003% | 0.002% | 0.003% |
| GST | 18% on (brokerage + exch + SEBI) | same | same | same |

*F&O STT rates reflect the Budget 2026 hike effective 1 April 2026 (futures 0.02% → 0.05%, options 0.10% → 0.15%).*
"""
    st.markdown(rate_md)

    st.markdown(
        '<div class="hk-note">'
        "<strong>Note on options:</strong> On Zerodha/Upstox flat-fee models, "
        "brokerage is a fixed ₹20 per executed order regardless of premium "
        "size, which is why option trades can absorb relatively more charge "
        "drag on small-premium trades. ICICI Direct and HDFC Securities apply "
        "percentage-based rates."
        "</div>",
        unsafe_allow_html=True,
    )


# ── TAB 4: Tax Computation ────────────────────────────────────────────

with tabs[3]:
    st.markdown(
        '<div class="hemrek-section-title">Income Tax Reckoning</div>',
        unsafe_allow_html=True,
    )

    # Allow capital gains adjustment
    adj1, adj2, adj3 = st.columns(3)
    with adj1:
        st.markdown('<div class="caption" style="margin-bottom:6px;">F&O BUSINESS INCOME</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:JetBrains Mono; font-size:1.3rem; color:var(--accent-gold); font-weight:700;">{fmt_inr(fo_net)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="caption">Non-speculative · taxed at slab</div>', unsafe_allow_html=True)

    with adj2:
        st.markdown('<div class="caption" style="margin-bottom:6px;">INTRADAY (SPECULATIVE)</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-family:JetBrains Mono; font-size:1.3rem; color:var(--accent-gold); font-weight:700;">{fmt_inr(intraday_net)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="caption">Separate head · taxed at slab</div>', unsafe_allow_html=True)

    with adj3:
        st.markdown('<div class="caption" style="margin-bottom:6px;">DELIVERY EQUITY NET</div>', unsafe_allow_html=True)
        delivery_net = float(delivery_charges["Net P&L"].sum()) if len(delivery_charges) > 0 else 0.0
        st.markdown(f'<div style="font-family:JetBrains Mono; font-size:1.3rem; color:var(--accent-gold); font-weight:700;">{fmt_inr(delivery_net)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="caption">Split into STCG/LTCG below</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="hemrek-section-title">Delivery Equity · STCG vs LTCG Split</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="hemrek-subtitle">'
        "The CSV alone can't tell how long you held each delivery trade. "
        "Enter the split below; the engine applies Section 111A (STCG @ 20%) "
        "and Section 112A (LTCG @ 12.5% above ₹1.25L exemption)."
        "</div>",
        unsafe_allow_html=True,
    )

    split_c1, split_c2 = st.columns(2)
    with split_c1:
        stcg = st.number_input(
            "STCG (held ≤ 12 months) ₹", value=max(0.0, delivery_net), step=1000.0,
        )
    with split_c2:
        ltcg = st.number_input(
            "LTCG (held > 12 months) ₹", value=0.0, step=1000.0,
        )

    # Recompute with user inputs
    tax_detail = income_tax_on_pnl(
        fo_net=fo_net,
        intraday_net=intraday_net,
        stcg=stcg,
        ltcg=ltcg,
        existing_income=existing_income,
        regime=tax_regime,
        cess_rate=cess_rate,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="hemrek-section-title">Tax Ledger</div>',
        unsafe_allow_html=True,
    )

    tax_ledger = [
        ("Existing Annual Income",            existing_income, ""),
        ("+ F&O Business Income (taxable)",   max(0.0, fo_net), ""),
        ("+ Intraday Speculative Income",     max(0.0, intraday_net), ""),
        ("Total Slab-taxed Income",           existing_income + max(0.0, fo_net) + max(0.0, intraday_net), "total"),
        ("  Slab Tax (marginal on F&O+Intra)", tax_detail["slab_tax"], ""),
        ("  Cess @ 4%",                        tax_detail["slab_cess"], ""),
        ("STCG (Sec 111A @ 20%)",              tax_detail["stcg_tax"], ""),
        ("  Cess @ 4%",                        tax_detail["stcg_cess"], ""),
        ("LTCG (Sec 112A @ 12.5%, >₹1.25L)",   tax_detail["ltcg_tax"], ""),
        ("  Cess @ 4%",                        tax_detail["ltcg_cess"], ""),
        ("TOTAL TAX PAYABLE",                  tax_detail["grand_total"], "total"),
    ]
    for label, val, cls in tax_ledger:
        st.markdown(
            f'<div class="hk-row {cls}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{fmt_inr(val)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Final post-tax net
    final_net_post = net_pretax - tax_detail["grand_total"]

    st.markdown("<br>", unsafe_allow_html=True)
    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        st.markdown(
            metric_card(
                "NET PRE-TAX",
                fmt_inr(net_pretax),
                "after all market charges",
                "green" if net_pretax >= 0 else "red",
            ),
            unsafe_allow_html=True,
        )
    with nc2:
        st.markdown(
            metric_card(
                "TOTAL TAX",
                fmt_inr(tax_detail["grand_total"]),
                f"slab+STCG+LTCG + {cess_rate*100:.0f}% cess",
                "red",
            ),
            unsafe_allow_html=True,
        )
    with nc3:
        st.markdown(
            metric_card(
                "NET POST-TAX",
                fmt_inr(final_net_post),
                "actual take-home",
                "gold",
            ),
            unsafe_allow_html=True,
        )

    # Effective rates
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="hemrek-section-title">Effective Rates</div>',
        unsafe_allow_html=True,
    )

    eff1, eff2, eff3 = st.columns(3)
    with eff1:
        charge_drag = (total_charges / max(abs(gross_pnl), 1)) * 100 if gross_pnl != 0 else 0
        st.markdown(
            f'<div class="hk-metric">'
            f'<div class="hk-metric-label">CHARGE DRAG</div>'
            f'<div class="hk-metric-value red">{charge_drag:.2f}%</div>'
            f'<div class="hk-metric-sub">of |gross P&L|</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with eff2:
        eff_tax_rate = (tax_detail["grand_total"] / max(net_pretax, 1)) * 100 if net_pretax > 0 else 0
        st.markdown(
            f'<div class="hk-metric">'
            f'<div class="hk-metric-label">EFFECTIVE TAX RATE</div>'
            f'<div class="hk-metric-value red">{eff_tax_rate:.2f}%</div>'
            f'<div class="hk-metric-sub">on pre-tax net</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with eff3:
        if gross_pnl != 0:
            retention = (final_net_post / gross_pnl) * 100
        else:
            retention = 0
        st.markdown(
            f'<div class="hk-metric">'
            f'<div class="hk-metric-label">RETENTION</div>'
            f'<div class="hk-metric-value gold">{retention:.2f}%</div>'
            f'<div class="hk-metric-sub">of gross P&L kept</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="hk-warn">'
        "<strong>Compliance note:</strong> F&O income is <em>non-speculative "
        "business income</em> under Section 28; intraday equity is "
        "<em>speculative business income</em> under Section 43(5). Both are "
        "taxed at your slab but are reported under different heads in ITR-3. "
        "Losses in these heads can be set off against other business/non-salary "
        "income (with specific restrictions — speculative losses only against "
        "speculative profits, carry-forward 4 years). This engine is an "
        "estimator. Consult a CA for filing."
        "</div>",
        unsafe_allow_html=True,
    )


# ── TAB 5: Export ─────────────────────────────────────────────────────

with tabs[4]:
    st.markdown(
        '<div class="hemrek-section-title">Export Reports</div>',
        unsafe_allow_html=True,
    )

    # Build export dataframe with everything
    export_positions = charges_df.copy()
    export_positions["Effective Charge %"] = (export_positions["Total Charges"] / export_positions["Turnover"].replace(0, np.nan) * 100).fillna(0).round(4)

    summary_rows = [
        ("Gross P&L",                    gross_pnl),
        ("Total Turnover",               total_turnover),
        ("Brokerage",                   -total_brok),
        ("STT",                         -total_stt),
        ("Exchange Transaction",        -total_exch),
        ("SEBI Turnover Fee",           -total_sebi),
        ("Stamp Duty",                  -total_stamp),
        ("GST @ 18%",                   -total_gst),
        ("IPFT",                        -total_ipft),
        ("Total Charges",               -total_charges),
        ("Net P&L (Pre-Tax)",            net_pretax),
        ("Slab Tax (F&O + Intraday)",   -tax_detail["slab_tax"]),
        ("STCG Tax (20%)",              -tax_detail["stcg_tax"]),
        ("LTCG Tax (12.5%)",            -tax_detail["ltcg_tax"]),
        ("Health & Edu Cess (4%)",      -tax_detail["total_cess"]),
        ("Total Tax",                   -tax_detail["grand_total"]),
        ("Net P&L (Post-Tax)",           final_net_post),
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["Line Item", "Amount (₹)"])

    # CSV downloads
    exp_c1, exp_c2 = st.columns(2)
    with exp_c1:
        pos_csv = export_positions.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Per-Position CSV",
            data=pos_csv,
            file_name="arthgavana_positions.csv",
            mime="text/csv",
            width='stretch',
        )
    with exp_c2:
        sum_csv = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Summary CSV",
            data=sum_csv,
            file_name="arthgavana_summary.csv",
            mime="text/csv",
            width='stretch',
        )

    # Excel with both sheets
    try:
        import xlsxwriter  # noqa: F401
        engine_available = "xlsxwriter"
    except ImportError:
        engine_available = "openpyxl"

    xlsx_buf = io.BytesIO()
    with pd.ExcelWriter(xlsx_buf, engine=engine_available) as writer:
        export_positions.to_excel(writer, sheet_name="Positions", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        meta = pd.DataFrame({
            "Setting": [
                "Broker", "Tax Regime", "Existing Income",
                "Include Cess", "Financial Year",
                "Gross P&L", "Net Pre-Tax", "Total Tax", "Net Post-Tax",
            ],
            "Value": [
                broker_name, tax_regime, existing_income,
                "Yes" if include_cess else "No", fy_label,
                gross_pnl, net_pretax, tax_detail["grand_total"], final_net_post,
            ],
        })
        meta.to_excel(writer, sheet_name="Metadata", index=False)

    st.download_button(
        "Download Full Excel Report (.xlsx)",
        data=xlsx_buf.getvalue(),
        file_name="arthgavana_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="hemrek-section-title">Summary Preview</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        summary_df.style.format({"Amount (₹)": lambda x: fmt_inr(x)})
        .apply(
            lambda col: [
                "color:#10b981" if isinstance(v, (int, float)) and v > 0 else
                ("color:#ef4444" if isinstance(v, (int, float)) and v < 0 else "")
                for v in col
            ],
            subset=["Amount (₹)"],
        ),
        width='stretch',
        hide_index=True,
    )


# ══════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center; padding:24px; '
    'border-top:1px solid var(--border-subtle);">'
    '<div class="caption">'
    "अर्थगवन · ARTHGAVANA · HEMREK CAPITAL · NIRNAY DESIGN SYSTEM · "
    "FY 2025-26 / FY 2026-27 · RATES CURRENT AS OF APR 2026"
    "</div></div>",
    unsafe_allow_html=True,
)
