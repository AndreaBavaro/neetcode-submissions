"""Live screen for "down but intact" stocks using current analyst-estimate revisions.

Universe: Nasdaq screener list (data/screener.csv), one sector, market value above a floor.
Data: Yahoo Finance via yfinance (.info and .eps_trend: consensus EPS now vs 7/30/60/90 days ago).
Rules (fixed before running):
  down      = price at least 25% below the 52-week high
  T1        = next-fiscal-year consensus EPS now >= 90 days ago, and current-year too
  T2        = trailing EPS > 0 or free cash flow > 0
  sane      = forward P/E between 0 and 25
T3 (is the bad news company-specific?) cannot be screened and needs reading.

Usage: python3 screen_live.py "Health Care" 3e9
"""
import os, sys, time, warnings
import pandas as pd, yfinance as yf
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sector, floor = sys.argv[1], float(sys.argv[2])
S = pd.read_csv(os.path.join(HERE, "data", "screener.csv")).drop_duplicates("symbol")
U = S[(S.sector == sector) & (S.mcap > floor) & S.symbol.str.fullmatch(r"[A-Z]{1,5}")]
rows = []
for i, r in enumerate(U.itertuples()):
    for a in range(3):
        try:
            t = yf.Ticker(r.symbol); inf = t.info; tr = t.eps_trend
            g = lambda p, c: float(tr.loc[p, c]) if tr is not None and p in tr.index else float("nan")
            px, hi = inf.get("currentPrice"), inf.get("fiftyTwoWeekHigh")
            rows.append(dict(symbol=r.symbol, name=inf.get("shortName"), industry=r.industry, country=r.country, mcap_bn=round(r.mcap / 1e9, 1),
                             price=px, off_high=(px / hi - 1) if px and hi else None, fwd_pe=inf.get("forwardPE"),
                             trailing_eps=inf.get("trailingEps"), fcf_bn=(inf.get("freeCashflow") or 0) / 1e9,
                             rev_growth=inf.get("revenueGrowth"), eps_ny_now=g("+1y", "current"), eps_ny_90d=g("+1y", "90daysAgo"),
                             eps_cy_now=g("0y", "current"), eps_cy_90d=g("0y", "90daysAgo"), eps_ny_30d=g("+1y", "30daysAgo"),
                             cash_bn=(inf.get("totalCash") or 0) / 1e9, debt_bn=(inf.get("totalDebt") or 0) / 1e9,
                             vs_200d=(px / inf["twoHundredDayAverage"] - 1) if px and inf.get("twoHundredDayAverage") else None))
            break
        except Exception as e:
            time.sleep(4 * (a + 1))
    time.sleep(0.8)
df = pd.DataFrame(rows)
rev = lambda now, old: (df[now] - df[old]) / df[old].abs()
df["rev_ny_90d"] = rev("eps_ny_now", "eps_ny_90d"); df["rev_cy_90d"] = rev("eps_cy_now", "eps_cy_90d")
df["down"] = df.off_high <= -0.25
df["T1"] = (df.eps_ny_now >= df.eps_ny_90d) & (df.eps_cy_now >= df.eps_cy_90d)
df["T2"] = (df.trailing_eps > 0) | (df.fcf_bn > 0)
df["sane"] = df.fwd_pe.between(0, 25)
tag = sector.lower().replace(" ", "_")
df.to_csv(os.path.join(HERE, "results", f"screen_{tag}.csv"), index=False, float_format="%.4f")
print(f"{sector}: {len(df)} of {len(U)} fetched; down {int(df.down.sum())}; down+T1+T2 {int((df.down & df.T1 & df.T2).sum())}; also sane {int((df.down & df.T1 & df.T2 & df.sane).sum())}")
pd.set_option("display.width", 250)
show = ["symbol", "name", "industry", "mcap_bn", "price", "off_high", "vs_200d", "fwd_pe", "rev_growth", "rev_ny_90d", "rev_cy_90d", "trailing_eps", "fcf_bn", "sane"]
print(df[df.down & df.T1 & df.T2].sort_values("fwd_pe")[show].round(3).to_string(index=False))
