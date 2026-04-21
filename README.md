# अर्थगवन · Arthgavana

**Indian Market Net P&L Intelligence System** — Hemrek Capital

A comprehensive post-charges, post-tax P&L reconciliation engine for Indian cash +
F&O markets. Takes a broker positions CSV (Zerodha Kite format native) and returns
the exact net P&L after every statutory charge and income-tax treatment.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- **CSV Upload** — Parse broker positions (Zerodha Kite, Upstox, or generic CSV)
- **Dynamic Lot Sizes** — Fetches live from NSE API, editable fallback dictionary
- **WRCI Indicator** — Wave-Regime Composite Index for multi-symbol scanning
- **Net P&L** — Post-charges, post-tax reconciliation
- **Tax Planning** — Marginal slab calculator with New/Old regime support

## What it computes

**Charges stack** (per-leg, Indian FY 2026-27 rates):

| Charge          | Equity Delivery       | Equity Intraday     | Futures          | Options             |
|-----------------|-----------------------|---------------------|------------------|---------------------|
| Brokerage       | Free / % (broker)     | ₹20 or 0.03% (min)  | ₹20 or 0.03%     | ₹20 flat / leg      |
| STT             | 0.10% both sides      | 0.025% sell         | 0.05% sell       | 0.15% sell premium  |
| Exchange (NSE)  | 0.00307%              | 0.00307%            | 0.00183%         | 0.03553% premium    |
| SEBI            | ₹10 / crore           | same                | same             | same                |
| Stamp Duty (buy)| 0.015%                | 0.003%              | 0.002%           | 0.003%              |
| GST             | 18% on (brok+exch+SEBI) each                                             |

**Income tax** (New Regime FY 2026-27 slabs, marginal on existing income):
- F&O → Non-speculative business income @ slab
- Intraday → Speculative business income @ slab
- STCG equity (Sec 111A) → 20% flat
- LTCG equity (Sec 112A) → 12.5% above ₹1.25L exemption
- 4% Health & Education Cess on all

## Lot Sizes

The app maintains a dictionary of NSE F&O lot sizes. On first load, it attempts to fetch live from NSE API via NseKit. Falls back to pre-populated dictionary with 218 symbols. You can:
- Click **Refresh from NSE** to re-fetch
- Click **Edit** to manually add/modify lot sizes

## WRCI Indicator

Wave-Regime Composite Index — combines:
- Hull Moving Average (HMA) of HLC3
- Channel Index (CI) with Ehlers smoothing
- Volume-normalized trend

Scan Nifty 50 symbols for long/short signals with configurable parameters.

## Brokers supported

Zerodha · Upstox · Groww · Angel One · Dhan · Fyers · ICICI Direct · HDFC Securities · Custom

## UI

Nirnay design system — dark (`#0a0a0f`) with gold accents (`#d4af37`), JetBrains Mono
for numerics, Outfit for typography, full Indian number formatting throughout
(`₹12,34,567.89`).