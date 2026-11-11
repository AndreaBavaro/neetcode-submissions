"""Signal state of each current holding and a few market gauges, as of the last data date.
Uses the full panel (holdout included). Run after `run_tests.py holdout`."""
import math, numpy as np, pandas as pd
import engine as E
import run_tests as R

R.setup(True)
px, dates = R.D["px"], R.A["dates"]
names = ["AAOI", "NOW", "OSCR", "ASTS", "AMZN", "GOOG", "ADUR", "TE", "AMPG"]
P = px[names].iloc[-1200:]
M = pd.DataFrame({c: R.D["idx"]["^GSPC"].iloc[-1200:].values for c in names}, index=P.index)
S = E.Sig(P, M)
last = P.iloc[-1]
sg = S.sigma()[-1]
rows = []
for i, t in enumerate(names):
    g = S.gap(20, .5)[:, i]; r = S.r[t]
    sd = r.rolling(60).std().shift(1)
    ev = (r < -3 * sd) & (np.exp(r) - 1 <= -0.08)
    recent = ev.iloc[-21:]
    rows.append(dict(
        ticker=t, last=round(last[t], 2), date=P[t].last_valid_index().date(),
        sigma=round(sg[i], 2) if not np.isnan(sg[i]) else None,
        vs_sma200=round(last[t] / S.sma(200)[-1, i] - 1, 2),
        pos_in_52w_range=round(S.pr()[-1, i], 2),
        resid_weak_O1=bool(S.resid_weak(200)[-1, i]),
        O2_initial_stop_pct=round(math.exp(-1.0 * sg[i] * math.sqrt(3)) - 1, 2) if not np.isnan(sg[i]) else None,
        gap_event_last_21d=str(recent[recent].index[-1].date()) if recent.any() else "",
        gap_fail_signal_last_63d=bool(g[-63:].any())))
df = pd.DataFrame(rows)
print(df.to_string(index=False))
df.to_csv("results/current_state.csv", index=False)

print("\nMarket gauges from the downloaded data, as of", dates[-1].date())
sp = R.D["spread"]
print("Baa-10y spread now %.2f, 63 days ago %.2f, change %.2f (O4 fires at +0.50)" % (sp.iloc[-1], sp.iloc[-64], sp.iloc[-1] - sp.iloc[-64]))
us = px[[t for t in R.D["U"]["us"] if t in px.columns]]
a200 = (us.iloc[-1] > us.rolling(200).mean().iloc[-1]).mean(); a50 = (us.iloc[-1] > us.rolling(50).mean().iloc[-1]).mean()
print("Sampled US universe (%d names, large/mid/small): %.0f%% above 200-day, %.0f%% above 50-day" % (us.shape[1], 100 * a200, 100 * a50))
for t in ["^GSPC", "^NDX", "RSP", "IWM", "XLE", "XLK", "IGV", "SMH", "XLV", "XLU", "XLF", "MTUM"]:
    s = E._read_px(t)
    print("%-6s last %10.2f  1m %+6.1f%%  3m %+6.1f%%  6m %+6.1f%%  12m %+6.1f%%  from 52w high %+6.1f%%  vs 200d %+6.1f%%" % (
        t, s.iloc[-1], *(100 * (s.iloc[-1] / s.iloc[-1 - k] - 1) for k in (21, 63, 126, 252)),
        100 * (s.iloc[-1] / s.iloc[-252:].max() - 1), 100 * (s.iloc[-1] / s.iloc[-200:].mean() - 1)))
v = E._read_px("^VIX"); v3 = E._read_px("^VIX3M")
print("VIX %.1f (1y range %.1f-%.1f), VIX3M %.1f" % (v.iloc[-1], v.iloc[-252:].min(), v.iloc[-252:].max(), v3.iloc[-1]))
g = np.log(E._read_px("^GSPC")).diff()
print("S&P 500 realised vol: 21d %.1f%%, 63d %.1f%%, 252d %.1f%%" % tuple(100 * g.iloc[-k:].std() * math.sqrt(252) for k in (21, 63, 252)))
