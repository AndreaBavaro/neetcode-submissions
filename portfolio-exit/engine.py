"""Backtest engine for the exit-strategy study. Rules are those in HYPOTHESES.md.

Everything is simulated on a "mini panel": LOOK days of history before the
window start plus the window itself, for the nine chosen stocks. Signals are
computed on that mini panel only, so the same code runs on real, shuffled,
bootstrapped and ruin-injected paths.
"""
import json, math, os, pickle
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CUTOFF = pd.Timestamp("2023-11-10")   # nothing after this is loaded unless holdout=True
STEP = 21
LOOK = 900
W = np.array([.198, .194, .192, .129, .110, .096, .044, .024, .013])
W = W / W.sum()
COSTS = {"low": 0.001, "high": 0.016}

# first entry of each idea is the pre-registered setting, the rest are perturbations
VARIANTS = (
    [("B1", None), ("B2", None)]
    + [("T1", p) for p in (200, 100, 150, 250, 300)]
    + [("T2", p) for p in (0.70, 0.60, 0.65, 0.75, 0.80)]
    + [("T3", p) for p in (12, 6, 9, 18, 24)]
    + [("O1", p) for p in (200, 100, 150, 250, 300)]
    + [("O2", p) for p in (1.0, 0.5, 0.75, 1.25, 1.5)]
    + [("O3", p) for p in ((.8, .2, 2, 12), (.9, .1, 2, 12), (.7, .3, 2, 12), (.8, .2, 3, 12), (.8, .2, 2, 18))]
    + [("O4", p) for p in (0.50, 0.25, 0.375, 0.75, 1.00)]
    + [("O5", p) for p in ((20, .5), (10, .5), (40, .5), (20, .25), (20, .75))]
)
BASE = {}
for s, p in VARIANTS:
    BASE.setdefault(s, p)


# ----------------------------------------------------------------------------- data
def _read_px(t):
    fn = os.path.join(DATA, "px_" + t.replace("^", "_") + ".csv")
    if not os.path.exists(fn):
        return None
    s = pd.read_csv(fn, index_col=0, parse_dates=True)["adj"]
    s = s[s > 0]
    return s[~s.index.duplicated(keep="last")]


def local_index(t):
    if t.endswith(".TO"):
        return "^GSPTSE"
    if t.endswith(".DE"):
        return "^GDAXI"
    if t.endswith(".L"):
        return "^FTSE"
    return "^GSPC"


def load(holdout=False):
    """Return dict(px, idx, rf, spread, U). Truncated at CUTOFF unless holdout=True."""
    cache = os.path.join(DATA, "panel_full.pkl" if holdout else "panel_design.pkl")
    if os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    U = json.load(open(os.path.join(DATA, "universe.json")))
    cal = _read_px("^GSPC").loc["1990-01-01":].index
    if not holdout:
        cal = cal[cal <= CUTOFF]
    cols = {}
    for t in U["us"] + U["intl"] + U["holdings"] + ["ACT.CN"]:
        s = _read_px(t)
        if s is None or len(s) < 400:
            continue
        s = s.reindex(cal.union(s.index)).ffill(limit=5).reindex(cal)
        # last valid observation onwards stays NaN (stock stopped trading)
        r = np.log(s).diff().abs()
        if (r > 2).any():        # single-day x7.4 move = bad data, drop ticker
            continue
        cols[t] = s
    px = pd.DataFrame(cols).astype("float64")
    idx = pd.DataFrame({t: _read_px(t).reindex(cal.union(_read_px(t).index)).ffill(limit=5).reindex(cal)
                        for t in ["^GSPC", "^GSPTSE", "^GDAXI", "^FTSE", "^NDX"]})
    rf = pd.read_csv(os.path.join(DATA, "fred_DTB3.csv"), index_col=0, parse_dates=True, na_values=".").iloc[:, 0]
    rf = rf.reindex(cal.union(rf.index)).ffill().reindex(cal).fillna(0) / 100 / 252
    sp = pd.read_csv(os.path.join(DATA, "fred_BAA10Y.csv"), index_col=0, parse_dates=True, na_values=".").iloc[:, 0]
    sp = sp.reindex(cal.union(sp.index)).ffill().reindex(cal)
    out = dict(px=px, idx=idx, rf=rf, spread=sp, U=U)
    pickle.dump(out, open(cache, "wb"))
    return out


# ----------------------------------------------------------------------------- signals
class Sig:
    """Signals on a mini panel. P, M: DataFrames (days x n) of stock and index prices."""

    def __init__(self, P, M):
        self.P = P
        self.r = np.log(P).diff()
        self.rm = np.log(M).diff()
        self._c = {}

    def _get(self, k, f):
        if k not in self._c:
            self._c[k] = f()
        return self._c[k]

    def sigma(self):
        return self._get("sig", lambda: (self.r.rolling(252, min_periods=252).std() * math.sqrt(252)).values)

    def sma(self, n):
        return self._get(("sma", n), lambda: self.P.rolling(n, min_periods=n).mean().values)

    def X(self):
        def f():
            cov = self.r.rolling(252, min_periods=252).cov(self.rm)
            var = self.rm.rolling(252, min_periods=252).var()
            beta = (cov / var).shift(1)
            e = self.r - beta * self.rm
            return e.cumsum()
        return self._get("X", f)

    def resid_weak(self, n):
        def f():
            X = self.X()
            return ((X < X.rolling(n, min_periods=n).mean()) & (X < X.shift(n // 2))).values
        return self._get(("rw", n), f)

    def pr(self):
        def f():
            hi = self.P.rolling(252, min_periods=120).max()
            lo = self.P.rolling(252, min_periods=120).min()
            return ((self.P - lo) / (hi - lo)).values
        return self._get("pr", f)

    def gap(self, wait, frac):
        def f():
            sd = self.r.rolling(60, min_periods=60).std().shift(1)
            ev = (self.r < -3 * sd) & (np.exp(self.r) - 1 <= -0.08)
            pre, gp = self.P.shift(1), self.P
            lvl = gp + frac * (pre - gp)
            return (ev.shift(wait).fillna(False).astype(bool) & (self.P < lvl.shift(wait))).values
        return self._get(("gap", wait, frac), f)


# ----------------------------------------------------------------------------- engine
def run(h, P, R, c):
    """h: shares held after trading on each day (T+1 x n). P: prices. R: cash index."""
    tv = np.diff(h, axis=0) * P[1:]
    cf = -tv.sum(1) - c * np.abs(tv).sum(1)
    cash = R[1:] * np.cumsum(cf / R[1:])
    V = np.concatenate([[(h[0] * P[0]).sum()], (h[1:] * P[1:]).sum(1) + cash])
    return V, np.abs(tv).sum()


class Ctx:
    """One trial. Pm/Mm: mini-panel DataFrames; o: row of window day 0; T: window length."""

    def __init__(self, Pm, Mm, o, T, w, rf, spread):
        Pm = Pm / Pm.iloc[o]
        self.sig = Sig(Pm, Mm)
        self.o, self.T, self.w = o, T, np.asarray(w, float)
        self.N = T // STEP
        self.P = Pm.values[o:o + T + 1]
        self.R = np.concatenate([[1.0], np.cumprod(1 + rf[1:T + 1])])
        self.spread = spread            # aligned with mini panel rows
        self.n = len(w)

    def h0(self):
        return np.tile(self.w, (self.T + 1, 1))

    def reviews(self):
        return [(k, STEP * k) for k in range(1, self.N)]


def s_B1(c, p, cost):
    h = c.h0(); h[c.T] = 0
    return h


def s_B2(c, p, cost):
    h = c.h0()
    for k, d in c.reviews():
        h[d + 1:] = c.w * (1 - k / c.N)
    h[c.T] = 0
    return h


def s_T1(c, n, cost):
    h = c.h0(); sma = c.sig.sma(n)
    for i in range(c.n):
        cur, cash, tc = c.w[i], 0.0, 0
        for k, d in c.reviews():
            p, s = c.P[d, i], sma[c.o + d, i]
            if cur > 0 and p < s:
                cash, tc, cur = cur * c.P[d + 1, i] * (1 - cost), d + 1, 0.0
                h[d + 1:, i] = 0
            elif cur == 0 and p > s:
                cur = cash * c.R[d + 1] / c.R[tc] / (c.P[d + 1, i] * (1 + cost))
                h[d + 1:, i] = cur
    h[c.T] = 0
    return h


def s_T2(c, floor, cost):
    h = c.h0(); sg = c.sig.sigma()
    for k, d in c.reviews():
        V, _ = run(h[:d + 1], c.P[:d + 1], c.R[:d + 1], cost)
        F = floor * V.max()
        C = (V[d] - F) / V[d]
        E = min(1.0, max(0.0, 4 * C))
        val = h[d] * c.P[d]
        need = val.sum() - E * V[d]
        if need > 1e-9:
            for i in np.argsort(-np.nan_to_num(sg[c.o + d], nan=0.0)):
                if need <= 1e-9:
                    break
                x = min(val[i], need)
                if x > 0:
                    h[d + 1:, i] = h[d, i] * (1 - x / val[i])
                    need -= x
    h[c.T] = 0
    return h


def s_T3(c, L, cost):
    h = c.h0()
    rank = np.argsort(np.argsort(-np.nan_to_num(c.sig.sigma()[c.o], nan=0.0)))
    for i in range(c.n):
        k0 = int(round(1 + (c.N - L) * rank[i] / (c.n - 1)))
        for m in range(L):
            k = k0 + m
            if k < c.N:
                h[STEP * k + 1:, i] = c.w[i] * (1 - (m + 1) / L)
    h[c.T] = 0
    return h


def _first_exit(c, cond_rows):
    """cond_rows(d) -> bool array per stock at review day d. Sell all at first True."""
    h = c.h0(); held = np.ones(c.n, bool)
    for k, d in c.reviews():
        hit = held & cond_rows(d)
        if hit.any():
            h[d + 1:, hit] = 0
            held &= ~hit
    h[c.T] = 0
    return h


def s_O1(c, n, cost):
    rw = c.sig.resid_weak(n)
    return _first_exit(c, lambda d: rw[c.o + d])


def s_O2(c, kk, cost):
    H = np.maximum.accumulate(c.P, axis=0); sg = c.sig.sigma()

    def cond(d):
        tau = (c.T - d) / 252
        with np.errstate(invalid="ignore"):
            return c.P[d] < H[d] * np.exp(-kk * sg[c.o + d] * math.sqrt(tau))
    return _first_exit(c, cond)


def s_O3(c, p, cost):
    hi, lo, mult, catch = p
    h = c.h0(); pr = c.sig.pr(); f = np.ones(c.n)
    for k, d in c.reviews():
        x = pr[c.o + d]
        lots = np.where(x >= hi, mult, np.where(x <= lo, 0, 1)).astype(float)
        f = np.maximum(f - lots / c.N, 0)
        f = np.minimum(f, (c.N - k) / catch)
        h[d + 1:] = c.w * f
    h[c.T] = 0
    return h


def s_O4(c, thr, cost):
    h = c.h0(); held = np.ones(c.n, bool); sg = c.sig.sigma(); sp = c.spread
    for k, d in c.reviews():
        j = c.o + d
        if held.any() and j >= 63 and sp[j] - sp[j - 63] >= thr:
            ids = np.where(held)[0]
            order = ids[np.argsort(-np.nan_to_num(sg[j, ids], nan=0.0))]
            sell = order[:math.ceil(len(ids) / 2)]
            h[d + 1:, sell] = 0
            held[sell] = False
    h[c.T] = 0
    return h


def s_O5(c, p, cost):
    g = c.sig.gap(*p)[c.o:c.o + c.T]
    h = c.h0()
    for i in range(c.n):
        s = np.flatnonzero(g[:, i])
        if len(s) and s[0] + 1 < c.T:
            h[s[0] + 1:, i] = 0
    h[c.T] = 0
    return h


FUN = dict(B1=s_B1, B2=s_B2, T1=s_T1, T2=s_T2, T3=s_T3, O1=s_O1, O2=s_O2, O3=s_O3, O4=s_O4, O5=s_O5)


def evaluate(c, variants=VARIANTS, costs=COSTS):
    rows = []
    rfd = np.diff(c.R) / c.R[:-1]
    for name, p in variants:
        hc = None
        for cl, cost in costs.items():
            if name in ("T1", "T2") or hc is None:
                hc = FUN[name](c, p, cost)
            V, to = run(hc, c.P, c.R, cost)
            ret = np.diff(V) / V[:-1]
            ex = ret - rfd
            dd = (V / np.maximum.accumulate(V) - 1).min()
            sd = ex.std()
            rows.append((name, str(p), cl, V[-1] / V[0] - 1, dd, to, ret.std() * math.sqrt(252),
                         ex.mean() / sd * math.sqrt(252) if sd > 0 else 0.0,
                         (V / V[0]).min() - 1))
    return rows


COLS = ["strategy", "param", "cost", "ret", "mdd", "turnover", "vol", "sharpe", "worst_vs_start"]
