"""Run the test sets described in HYPOTHESES.md.

  python3 run_tests.py design     # everything that uses data up to 10 Nov 2023 only
  python3 run_tests.py holdout    # final check; loads data after 10 Nov 2023

Writes data/results_<set>.pkl (one row per trial x variant x cost level).
"""
import hashlib, math, os, pickle, sys
from multiprocessing import Pool
import numpy as np, pandas as pd
import engine as E

T = int(os.environ.get("WINDOW", 756))
D = None
A = {}


def setup(holdout):
    global D
    D = E.load(holdout)
    A["px"] = D["px"].values
    A["cols"] = np.array(D["px"].columns)
    A["dates"] = D["px"].index
    A["rf"] = D["rf"].values
    A["sp"] = D["spread"].values
    A["idx"] = {k: D["idx"][k].ffill().values for k in D["idx"]}
    us = [t for t in D["U"]["us"] if t in D["px"].columns]
    half = lambda t: int(hashlib.md5(t.encode()).hexdigest(), 16) % 2
    A["pool"] = {
        "A": np.array([D["px"].columns.get_loc(t) for t in us if half(t) == 0]),
        "B": np.array([D["px"].columns.get_loc(t) for t in us if half(t) == 1]),
        "US": np.array([D["px"].columns.get_loc(t) for t in us]),
        "INTL": np.array([D["px"].columns.get_loc(t) for t in D["U"]["intl"] if t in D["px"].columns]),
    }


def loc(date):
    return int(A["dates"].searchsorted(pd.Timestamp(date)))


def pick(rng, s, pool, hist=300):
    px = A["px"]
    ok = ~np.isnan(px[s, pool]) & ~np.isnan(px[s - hist, pool])
    cand = pool[ok]
    if len(cand) < 18:
        return None
    r = np.diff(np.log(px[s - 252:s + 1, cand]), axis=0)
    sg = np.nanstd(r, axis=0)
    top = cand[np.argsort(-sg)[:len(cand) // 2]]
    return rng.choice(top, 9, replace=False)


def mini(s, chosen, look=E.LOOK):
    lo = max(0, s - look)
    sl = slice(lo, s + T + 1)
    cols = A["cols"][chosen]
    Pm = pd.DataFrame(A["px"][sl][:, chosen], columns=cols)
    Pm.iloc[s - lo:] = Pm.iloc[s - lo:].ffill()          # stock that stops trading: frozen at last price
    Mm = pd.DataFrame({c: A["idx"][E.local_index(c)][sl] for c in cols})
    return Pm, Mm, s - lo, A["rf"][s:s + T + 1], A["sp"][sl]


def rebuild(P0, r):
    return pd.DataFrame(np.exp(np.vstack([np.zeros(r.shape[1]), np.cumsum(r, axis=0)])) * P0, columns=None)


def transform(kind, rng, Pm, Mm, o):
    cols = Pm.columns
    if kind in ("shuffle", "bootstrap"):
        rp, rm = np.diff(np.log(Pm.values), axis=0), np.diff(np.log(Mm.values), axis=0)
        n = len(rp)
        if kind == "shuffle":
            ix = rng.permutation(n)
        else:
            ix = np.concatenate([np.arange(b, b + 63) % n for b in rng.integers(0, n, n // 63 + 1)])[:n]
        P2 = rebuild(Pm.values[0], rp[ix]); P2.columns = cols
        M2 = rebuild(Mm.values[0], rm[ix]); M2.columns = cols
        return P2, M2
    if kind == "ruin":
        j = rng.integers(0, Pm.shape[1]); u = o + int(rng.integers(0, 500))
        r = np.diff(np.log(Pm.values), axis=0)
        seg = slice(u, u + 250)                           # r[u] is the return into day u+1
        gap = rng.random() < 0.5
        tot = math.log(0.2) if gap else math.log(0.1)
        r[seg, j] = r[seg, j] - np.nanmean(r[seg, j]) + tot / 250
        if gap:
            r[u, j] += math.log(0.5)
        # rebuild from the window start so stocks with short pre-window history keep their real past
        lev = np.vstack([np.zeros(r.shape[1]), np.cumsum(np.nan_to_num(r), axis=0)])
        P2 = pd.DataFrame(np.exp(lev - lev[o]) * Pm.values[o], columns=cols).where(~Pm.isna().values)
        return P2, Mm
    raise ValueError(kind)


def one(args):
    name, trial, seed, pool, s, kind, fixed, w = args
    rng = np.random.default_rng(seed)
    synth = kind in ("shuffle", "bootstrap")
    if fixed is None:
        chosen = pick(rng, s, A["pool"][pool], hist=600 if synth else 300)
        if chosen is None:
            return []
        w = rng.permutation(E.W)
    else:
        chosen = np.array(fixed)
    Pm, Mm, o, rf, sp = mini(s, chosen, look=600 if synth else E.LOOK)
    if kind:
        Pm, Mm = transform(kind, rng, Pm, Mm, o)
    c = E.Ctx(Pm, Mm, o, T, w, rf, sp)
    return [(name, trial, A["dates"][s]) + r for r in E.evaluate(c)]


def run_set(name, n, pool, starts, kind=None, seed0=0, fixed=None, w=None):
    rng = np.random.default_rng(abs(hash(name)) % 2**32 if False else int(hashlib.md5(name.encode()).hexdigest(), 16) % 2**32)
    jobs = [(name, i, seed0 + 1000003 * i + int(hashlib.md5(name.encode()).hexdigest(), 16) % 10**6, pool,
             int(rng.choice(starts)), kind, fixed, w) for i in range(n)]
    with Pool(os.cpu_count()) as p:
        out = p.map(one, jobs, chunksize=8)
    rows = [r for o in out for r in o]
    df = pd.DataFrame(rows, columns=["set", "trial", "start"] + E.COLS)
    sfx = "" if T == 756 else f"_T{T}"
    df.to_pickle(os.path.join(E.DATA, f"results_{name}{sfx}.pkl"))
    print(name, "trials", df.trial.nunique(), "rows", len(df), flush=True)
    return df


if __name__ == "__main__":
    mode = sys.argv[1]
    only = sys.argv[2:]
    if mode == "design":
        setup(False)
        last = len(A["dates"]) - T - 1
        rng_d = np.arange(loc("1995-01-03"), last + 1)
        sets = [
            ("designA", 2000, "A", rng_d, None),
            ("designB", 2000, "B", rng_d, None),
            ("intl", 1500, "INTL", np.arange(loc("2000-01-03"), last + 1), None),
            ("w2000jan", 300, "US", [loc("2000-01-03")], None),
            ("w2000mar", 300, "US", [loc("2000-03-10")], None),
            ("w2007oct", 300, "US", [loc("2007-10-09")], None),
            ("shuffle", 1000, "US", rng_d, "shuffle"),
            ("bootstrap", 1000, "US", rng_d, "bootstrap"),
            ("ruin", 1500, "US", rng_d, "ruin"),
        ]
        for name, n, pool, starts, kind in sets:
            if only and name not in only:
                continue
            run_set(name, n, pool, starts, kind)
    elif mode == "holdout":
        setup(True)
        last = len(A["dates"]) - T - 1
        ic = loc(E.CUTOFF)
        run_set("holdout", 1500, "US", np.arange(ic - T + 1, last + 1))
        run_set("w2021dec", 300, "US", [loc("2021-12-01")])
        # the client's actual book, as if inherited 756 trading days ago at today's weights
        # Aduro (ADUR) has no Yahoo history before Aug 2024, so it is left out (4.4% weight) and
        # the other eight weights are rescaled.
        names = ["AAOI", "NOW", "OSCR", "ASTS", "AMZN", "GOOG", "TE", "AMPG"]
        wts = np.array([.198, .194, .192, .129, .110, .096, .024, .013]); wts = wts / wts.sum()
        cols = list(D["px"].columns)
        run_set("actual", 1, "US", [last], fixed=[cols.index(t) for t in names], w=wts)
