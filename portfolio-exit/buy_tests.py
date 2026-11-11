"""Test the three buy-tests on "down" stocks. Definitions are those in HYPOTHESES_BUYTESTS.md."""
import os, pickle, sys
import numpy as np, pandas as pd
import engine as E

D = E.load(True)
F = pickle.load(open(os.path.join(E.DATA, "fundamentals.pkl"), "rb"))
G = pd.read_csv(os.path.join(E.DATA, "gics.csv")).set_index("ticker")
US = [t for t in D["U"]["us"] if t in D["px"].columns and t in F and t in G.index]
PX = D["px"][US]; IDX = D["idx"]["^GSPC"].ffill()
DESIGN_END = pd.Timestamp("2022-10-31")
rng = np.random.default_rng(11)
day = lambda s: pd.Timestamp(s).toordinal()


def flows(rows):
    """rows of (start,end,val,filed,pri) -> DataFrame(end, known, ttm), first-filed values only."""
    best = {}
    for s, e, v, f, p in rows:
        if s is None:
            continue
        k = (day(s), day(e))
        if k not in best or (f, p) < best[k][1:]:
            best[k] = (v, f, p)
    by_end = {}
    for (s, e), (v, f, p) in best.items():
        by_end.setdefault(e, []).append((e - s, s, v, f))
    fy = {e: max(c)[2:] for e, c in ((e, [x for x in c if 350 <= x[0] <= 380]) for e, c in by_end.items()) if c}
    out = []
    for e, c in by_end.items():
        if e in fy:
            out.append((e, fy[e][1], fy[e][0])); continue
        c = [x for x in c if x[0] < 290]
        if not c:
            continue
        d, s, v, f = max(c)
        pf = next((fy[x] for x in range(s - 8, s + 7) if x in fy), None)
        py = next((best[(a, b)] for a in range(s - 375, s - 354) for b in range(e - 375, e - 354) if (a, b) in best), None)
        if pf is None or py is None:
            continue
        out.append((e, max(f, pf[1], py[1]), v + pf[0] - py[0]))
    df = pd.DataFrame(out, columns=["end", "known", "ttm"]).sort_values("end")
    df["known"] = pd.to_datetime(df.known)
    return df


def instants(rows):
    best = {}
    for s, e, v, f, p in rows:
        k = day(e)
        if k not in best or (f, p) < best[k][1:]:
            best[k] = (v, f, p)
    df = pd.DataFrame([(e, v[1], v[0]) for e, v in best.items()], columns=["end", "known", "val"]).sort_values("end")
    df["known"] = pd.to_datetime(df.known)
    return df


FUND = {}
for t in US:
    FUND[t] = {k: flows(F[t][k]) for k in ("rev", "ni", "ocf")} | {k: instants(F[t][k]) for k in ("cash", "sti")}


def at(df, date, col):
    """latest row known on `date` (by period end); returns (end, value) or None"""
    x = df[df.known <= date]
    if x.empty:
        return None
    r = x.iloc[-1]
    return int(r.end), float(r[col])


def year_ago(df, date, end):
    x = df[(df.known <= date) & (df.end >= end - 385) & (df.end <= end - 345)]
    return None if x.empty else float(x.iloc[-1].ttm)


def fundamentals(t, date):
    f = FUND[t]; d0 = date.toordinal()
    rev, ni, ocf = at(f["rev"], date, "ttm"), at(f["ni"], date, "ttm"), at(f["ocf"], date, "ttm")
    if rev is None or ni is None or d0 - ni[0] > 200 or d0 - rev[0] > 200:
        return None
    rev0, ni0 = year_ago(f["rev"], date, rev[0]), year_ago(f["ni"], date, ni[0])
    if rev0 is None or ni0 is None:
        return None
    cash = at(f["cash"], date, "val"); sti = at(f["sti"], date, "val")
    c = (cash[1] if cash and d0 - cash[0] < 400 else np.nan) + (sti[1] if sti and d0 - sti[0] < 400 else 0.0)
    return dict(rev=rev[1], rev0=rev0, ni=ni[1], ni0=ni0, ocf=ocf[1] if ocf and d0 - ocf[0] < 200 else np.nan, cashsti=c)


def build(thr=0.30):
    P = PX
    dd = P / P.rolling(252, min_periods=200).max() - 1
    sma = P.rolling(200, min_periods=200).mean()
    r = np.log(P).diff()
    sd = r.rolling(60, min_periods=60).std().shift(1)
    gap = ((r < -3 * sd) & (np.exp(r) - 1 <= -0.08)).rolling(126, min_periods=1).max().astype(bool)
    r126 = P / P.shift(126) - 1
    f252 = P.shift(-252) / P - 1; f504 = P.shift(-504) / P - 1
    i252 = IDX.shift(-252) / IDX - 1; i504 = IDX.shift(-504) / IDX - 1
    me = pd.Series(P.index, index=P.index).groupby(P.index.to_period("M")).last()
    me = me[(me >= "2010-06-30") & (me <= P.index[-253])]
    sect = G.loc[US, "sector"]
    rows = []
    for kind, mask in (("down", (dd <= -thr) & (P < sma)), ("strong", (dd >= -0.10) & (P > sma))):
        m = mask.loc[me.values]
        for t in US:
            last = None
            for dt in m.index[m[t].values]:
                if last is not None and (dt - last).days < 360:
                    continue
                last = dt
                fu = fundamentals(t, dt)
                if fu is None:
                    continue
                peers = [p for p in sect.index[sect == sect[t]] if p != t]
                rows.append(dict(kind=kind, ticker=t, date=dt, sector=sect[t], gap=bool(gap.at[dt, t]),
                                 peer126=np.nanmedian(r126.loc[dt, peers].values), dd=dd.at[dt, t],
                                 f252=f252.at[dt, t], f504=f504.at[dt, t], x252=f252.at[dt, t] - i252[dt],
                                 x504=f504.at[dt, t] - i504[dt], **fu))
    return pd.DataFrame(rows).dropna(subset=["f252"])


def tests(e, peer=-0.10, mult=2.0):
    e = e.copy()
    e["t1"] = (e.rev >= e.rev0) & (e.ni >= e.ni0)
    burn = np.where(e.ocf < 0, -e.ocf, 0.0)
    e["t2"] = (e.ni > 0) | (e.ocf >= 0) | (e.cashsti >= mult * burn)
    e.loc[(e.ni <= 0) & e.ocf.isna(), "t2"] = False
    e["t3"] = ~(e.gap & (e.peer126 > peer))
    e["all3"] = e.t1 & e.t2 & e.t3
    return e


def desc(x, col="x252"):
    v = x[col].dropna()
    return dict(n=len(v), median=v.median(), mean=v.mean(), worst5=v.quantile(.05), beat_index=(v > 0).mean(),
                lose_half=(x.loc[v.index, col.replace("x", "f")] < -0.5).mean())


def diff_ci(e, flag, col="x252", B=2000):
    """median(pass) - median(fail), with a month-cluster bootstrap 90% interval"""
    e = e.dropna(subset=[col])
    obs = e[e[flag]][col].median() - e[~e[flag]][col].median()
    months = e.date.dt.to_period("M"); groups = [g for _, g in e.groupby(months)]
    bs = []
    for _ in range(B):
        s = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        a, b = s[s[flag]][col], s[~s[flag]][col]
        if len(a) > 5 and len(b) > 5:
            bs.append(a.median() - b.median())
    return obs, np.quantile(bs, .05), np.quantile(bs, .95)


if __name__ == "__main__":
    out = []; pr = lambda s="": (print(s), out.append(s))
    pc = lambda v: f"{100*v:+.1f}%"
    ev = tests(build(0.30))
    ev.to_csv("results/buytest_events.csv", index=False, float_format="%.5f")
    for name, e in (("Design (events to Oct 2022)", ev[ev.date <= DESIGN_END]), ("Holdout (events Nov 2022 to Nov 2025)", ev[ev.date > DESIGN_END])):
        dn = e[e.kind == "down"]; st = e[e.kind == "strong"]
        pr(f"\n### {name}\n")
        pr("| Group | Events | Median 12m vs index | Mean | Worst 5% | Beat index | Lost over half | Median 24m vs index |")
        pr("|---|---|---|---|---|---|---|---|")
        groups = [("All down stocks", dn), ("Down, passes all three", dn[dn.all3]), ("Down, fails at least one", dn[~dn.all3]),
                  ("Down, passes test 1", dn[dn.t1]), ("Down, fails test 1", dn[~dn.t1]),
                  ("Down, passes test 2", dn[dn.t2]), ("Down, fails test 2", dn[~dn.t2]),
                  ("Down, passes test 3", dn[dn.t3]), ("Down, fails test 3", dn[~dn.t3]),
                  ("Strong stocks", st), ("Strong, passes tests 1 and 2", st[st.t1 & st.t2])]
        for g, x in groups:
            d = desc(x); d2 = x.x504.dropna().median() if x.x504.notna().sum() > 5 else np.nan
            pr(f"| {g} | {d['n']} | {pc(d['median'])} | {pc(d['mean'])} | {pc(d['worst5'])} | {100*d['beat_index']:.0f}% | {100*d['lose_half']:.1f}% | {pc(d2) if d2 == d2 else 'n/a'} |")
        pr("\n| Comparison (median 12m vs index, pass minus fail) | Difference | 90% interval |"); pr("|---|---|---|")
        for flag, lab in (("all3", "All three"), ("t1", "Test 1"), ("t2", "Test 2"), ("t3", "Test 3")):
            if dn[flag].sum() > 5 and (~dn[flag]).sum() > 5:
                o, lo, hi = diff_ci(dn, flag)
                pr(f"| {lab} | {pc(o)} | {pc(lo)} to {pc(hi)} |")
            else:
                pr(f"| {lab} | too few events in one group | |")
    pr("\n### Perturbations (design sample, down stocks, median 12m vs index, pass minus fail)\n")
    pr("| Setting | All three | Test 1 | Test 2 | Test 3 |"); pr("|---|---|---|---|---|")
    for lab, thr, peer, mult in (("pre-registered", .30, -.10, 2), ("drawdown 20%", .20, -.10, 2), ("drawdown 40%", .40, -.10, 2),
                                 ("peer threshold -5%", .30, -.05, 2), ("peer threshold -15%", .30, -.15, 2),
                                 ("funding 1x", .30, -.10, 1), ("funding 3x", .30, -.10, 3)):
        e = tests(build(thr) if thr != .30 else ev, peer, mult); e = e[(e.kind == "down") & (e.date <= DESIGN_END)]
        cells = []
        for flag in ("all3", "t1", "t2", "t3"):
            a, b = e[e[flag]].x252, e[~e[flag]].x252
            cells.append(f"{pc(a.median() - b.median())} ({len(a)}/{len(b)})" if len(b) > 5 and len(a) > 5 else "n/a")
        pr(f"| {lab} | " + " | ".join(cells) + " |")
    open("results/buytests.md", "w").write("\n".join(out) + "\n")
