# अर्थगवन · Arthgavana

**Indian Market Net P&L Intelligence System** — Hemrek Capital

A comprehensive post-charges, post-tax P&L reconciliation engine for Indian cash +
F&O markets. Takes a broker positions CSV (Zerodha Kite format native) and returns
the exact net P&L after every statutory charge and income-tax treatment.

## Run

```bash
pip install -r requirements.txt
streamlit run arthgavana.py
```

## What it computes

**Charges stack** (per-leg, Indian FY 2025-26 rates):

| Charge          | Equity Delivery       | Equity Intraday     | Futures          | Options             |
|-----------------|-----------------------|---------------------|------------------|---------------------|
| Brokerage       | Free / % (broker)     | ₹20 or 0.03% (min)  | ₹20 or 0.03%     | ₹20 flat / leg      |
| STT             | 0.10% both sides      | 0.025% sell         | 0.02% sell       | 0.10% sell premium  |
| Exchange (NSE)  | 0.00297%              | 0.00297%            | 0.00173%         | 0.03503% premium    |
| SEBI            | ₹10 / crore           | same                | same             | same                |
| Stamp Duty (buy)| 0.015%                | 0.003%              | 0.002%           | 0.003%              |
| GST             | 18% on (brok+exch+SEBI) each                                             |

**Income tax** (New Regime FY 2025-26 slabs, marginal on existing income):
- F&O → Non-speculative business income @ slab
- Intraday → Speculative business income @ slab
- STCG equity (Sec 111A) → 20% flat
- LTCG equity (Sec 112A) → 12.5% above ₹1.25L exemption
- 4% Health & Education Cess on all

## Brokers supported

Zerodha · Upstox · Groww · Angel One · Dhan · Fyers · ICICI Direct · HDFC Securities · Custom

## UI

Nirnay design system — dark (`#0a0a0f`) with gold accents (`#d4af37`), JetBrains Mono
for numerics, Outfit for typography, full Indian number formatting throughout
(`₹12,34,567.89`).
