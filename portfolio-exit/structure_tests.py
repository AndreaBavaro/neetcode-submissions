"""Exploratory (NOT pre-registered) tests of the client's own structure rules.
Uses the full panel, random books as in run_tests.py, cost 1.6% per trade.

Structures: current concentrated weights; nine equal picks; 25% S&P 500 + nine equal picks;
            the same with the "above 15% -> trim to 12%" rule (proceeds into the index).
Exit timing: all on the last day; three lots over the last four months; monthly over the last 12 months;
             monthly over all 36 months.
The index sleeve is the S&P 500 price index (no dividends), which understates it slightly.
"""
import math, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
import engine as E, run_tests as R

T, C = 756, 0.016


def exits(h, kind):
    h = h.copy(); base = h[-1].copy() if False else None
    if kind == "end":
        pass
    elif kind == "3lots":
        for j, d in enumerate([T - 84, T - 42]):
            h[d + 1:] *= (2 - j) / (3 - j)
    elif kind == "last12":
        for j in range(12):
            d = T - 252 + 21 * j
            h[d + 1:] *= (11 - j) / (12 - j)
    elif kind == "all36":
        for k in range(1, 36):
            h[21 * k + 1:] *= (36 - k) / (36 - k + 1)
    h[T] = 0
    return h


def trim(P, w):
    """Monthly: any pick above 15% of the book is cut to 12%, proceeds into the index (last column)."""
    h = np.tile(w, (T + 1, 1)); n = len(w) - 1
    for k in range(1, 36):
        d = 21 * k
        val = h[d] * P[d]; tot = val.sum()
        for i in range(n):
            if val[i] / tot > 0.15:
                x = val[i] - 0.12 * tot
                h[d + 1:, i] = h[d, i] * (1 - x / val[i])
                h[d + 1:, n] = h[d + 1, n] + x * (1 - C) / (1 + C) / P[d, n]
    return h


def one(a):
    trial, seed, s = a
    rng = np.random.default_rng(seed)
    ch = R.pick(rng, s, R.A["pool"]["US"])
    if ch is None:
        return []
    Pm, Mm, o, rf, sp = R.mini(s, ch)
    P = (Pm / Pm.iloc[o]).values[o:o + T + 1]
    ix = R.A["idx"]["^GSPC"][s:s + T + 1]; ix = ix / ix[0]
    P10 = np.column_stack([P, ix])
    Rr = np.concatenate([[1.0], np.cumprod(1 + rf[1:T + 1])])
    wc = np.append(rng.permutation(E.W), 0.0)
    we = np.append(np.full(9, 1 / 9), 0.0)
    wb = np.append(np.full(9, 0.75 / 9), 0.25)
    out = []
    for sname, h0 in [("current weights", np.tile(wc, (T + 1, 1))), ("9 equal picks", np.tile(we, (T + 1, 1))),
                      ("25% index + 9 equal picks", np.tile(wb, (T + 1, 1))), ("25% index + picks + trim rule", trim(P10, wb)),
                      ("current weights + trim rule", trim(P10, wc))]:
        for ex in ["end", "3lots", "last12", "all36"]:
            V, to = E.run(exits(h0, ex), P10, Rr, C)
            dd = (V / np.maximum.accumulate(V) - 1).min()
            out.append((trial, sname, ex, V[-1] - 1, dd))
    return out


if __name__ == "__main__":
    R.setup(True)
    starts = np.arange(R.loc("1995-01-03"), len(R.A["dates"]) - T - 1)
    rng = np.random.default_rng(7)
    jobs = [(i, 5000 + i, int(rng.choice(starts))) for i in range(3000)]
    with Pool(4) as p:
        rows = [r for o in p.map(one, jobs, chunksize=16) for r in o]
    df = pd.DataFrame(rows, columns=["trial", "structure", "exit", "ret", "mdd"])
    g = df.groupby(["structure", "exit"], sort=False).agg(
        median_ret=("ret", "median"), worst5_ret=("ret", lambda x: x.quantile(.05)), worst_ret=("ret", "min"),
        median_maxdd=("mdd", "median"), worst5_maxdd=("mdd", lambda x: x.quantile(.05)),
        share_dd_over_30=("mdd", lambda x: (x < -0.30).mean()))
    g.to_csv("results/structure_tests.csv", float_format="%.4f")
    pd.set_option("display.width", 200)
    print((100 * g).round(0).to_string())
