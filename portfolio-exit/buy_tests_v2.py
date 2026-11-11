"""Round-2 tests (workstreams B, C, D, E). Definitions are those in HYPOTHESES_V2.md.

  python3 buy_tests_v2.py        # writes results/round2.md and results/round2_events.csv
"""
import json, os, pickle, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
DESIGN_END = pd.Timestamp("2022-10-31")
rng = np.random.default_rng(11)
day = lambda s: pd.Timestamp(s).toordinal()
pc = lambda v: "n/a" if v != v else f"{100*v:+.1f}%"
OUT = []


def pr(s=""):
    print(s, flush=True); OUT.append(s)


# ------------------------------------------------------------------ load
def read(fn, col):
    return pd.read_csv(os.path.join(DATA, fn), index_col=0, parse_dates=True)[col]


U1 = json.load(open(os.path.join(DATA, "universe.json")))["us"]
U2 = json.load(open(os.path.join(DATA, "universe2.json")))
IDX = read("px__GSPC.csv", "adj"); IDX = IDX[IDX.index >= "2005-01-01"]
CAL = IDX.index
F = pickle.load(open(os.path.join(DATA, "fundamentals2.pkl"), "rb"))
EH = pickle.load(open(os.path.join(DATA, "earnings.pkl"), "rb"))
SPL = json.load(open(os.path.join(DATA, "splits.json")))
SCR = pd.read_csv(os.path.join(DATA, "screener.csv")).drop_duplicates("symbol").set_index("symbol")
adj, cls = {}, {}
for t in U1 + U2:
    fn = os.path.join(DATA, f"px2_{t}.csv")
    if not os.path.exists(fn) or t not in F or t not in SCR.index or not isinstance(SCR.at[t, "sector"], str):
        continue
    d = pd.read_csv(fn, index_col=0, parse_dates=True)
    d = d[(d.close > 0) & (d.adj > 0)]
    if len(d) < 400:
        continue
    a = d.adj.reindex(CAL.union(d.index)).ffill(limit=5).reindex(CAL)
    if (np.log(a).diff().abs() > 2).any():
        continue
    adj[t] = a; cls[t] = d.close.reindex(CAL.union(d.index)).ffill(limit=5).reindex(CAL)
ADJ, CLS = pd.DataFrame(adj), pd.DataFrame(cls)
TICK = list(ADJ.columns); SECT = SCR.loc[TICK, "sector"]
IN_U1 = pd.Series([t in set(U1) for t in TICK], index=TICK)
pos = {d: i for i, d in enumerate(CAL)}


# ------------------------------------------------------------------ fundamentals as known
def flows(rows):
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
    fy = {}
    for e, c in by_end.items():
        c = [x for x in c if 350 <= x[0] <= 380]
        if c:
            fy[e] = max(c)[2:]
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
    df = pd.DataFrame(out, columns=["end", "known", "ttm"]).sort_values("end").reset_index(drop=True)
    ends = df.end.values; prev = np.full(len(df), np.nan)
    for i, e in enumerate(ends):
        j = np.where((ends >= e - 385) & (ends <= e - 345))[0]
        if len(j):
            prev[i] = df.ttm.values[j[-1]]
    df["prev"] = prev; df["known"] = pd.to_datetime(df.known)
    return df


def instants(rows, t=None, shares=False):
    best = {}
    for s, e, v, f, p in rows:
        k = day(e); dur = (k - day(s)) if s else 0
        key = (dur if shares else 0, f, p)          # shares: prefer the shortest (quarterly) period
        if k not in best or key < best[k][1]:
            best[k] = (v, key, f)
    rows2 = []
    for e, (v, key, f) in best.items():
        if shares:
            for sd, ratio in SPL.get(t, []):
                if sd > f:
                    v = v * ratio
        rows2.append((e, f, v))
    df = pd.DataFrame(rows2, columns=["end", "known", "val"]).sort_values("end").reset_index(drop=True)
    if shares and len(df):
        ends = df.end.values; prev = np.full(len(df), np.nan)
        for i, e in enumerate(ends):
            j = np.where((ends >= e - 385) & (ends <= e - 345))[0]
            if len(j):
                prev[i] = df.val.values[j[-1]]
        df["prev"] = prev
    df["known"] = pd.to_datetime(df.known)
    return df


def asof(df, dates, cols, pre):
    """latest filed row on each date -> columns prefixed with pre"""
    x = df.sort_values("known")[["known", "end"] + cols]
    m = pd.merge_asof(pd.DataFrame({"date": dates}), x, left_on="date", right_on="known")
    m = m.rename(columns={c: pre + c for c in ["end"] + cols}).drop(columns=["known"])
    return m.set_index("date")


ME = pd.Series(CAL, index=CAL).groupby(CAL.to_period("M")).last().values
ME = pd.DatetimeIndex(ME)
MON = {}
for t in TICK:
    f = F[t]
    parts = [asof(flows(f["rev"]), ME, ["ttm", "prev"], "rev_"), asof(flows(f["ni"]), ME, ["ttm", "prev"], "ni_"),
             asof(flows(f["ocf"]), ME, ["ttm"], "ocf_"), asof(instants(f["cash"]), ME, ["val"], "cash_"),
             asof(instants(f["sti"]), ME, ["val"], "sti_")]
    sh = instants(f.get("shares", []), t, shares=True)
    parts.append(asof(sh, ME, ["val", "prev"], "sh_") if len(sh) else pd.DataFrame(index=ME, columns=["sh_end", "sh_val", "sh_prev"], dtype=float))
    m = pd.concat(parts, axis=1)
    o = np.array([d.toordinal() for d in ME])
    for p, lim in (("rev_", 200), ("ni_", 200), ("ocf_", 200), ("cash_", 400), ("sti_", 400), ("sh_", 200)):
        stale = ~((o - m[p + "end"].astype(float)) <= lim)
        for c in [c for c in m.columns if c.startswith(p)]:
            m.loc[stale.values, c] = np.nan
    m["ps"] = CLS[t].reindex(ME).values * m.sh_val.astype(float) / m.rev_ttm.where(m.rev_ttm > 0)
    m["ps_med"] = m.ps.shift(1).rolling(60, min_periods=36).median()
    m["ps_q25"] = m.ps.shift(1).rolling(60, min_periods=36).quantile(.25)
    MON[t] = m

# ------------------------------------------------------------------ earnings reactions
REP = {}
hours = []
for t in TICK:
    e = EH.get(t)
    if e is None or len(e) == 0:
        continue
    e = e.dropna(subset=["dt"]).copy()
    dt = pd.DatetimeIndex(e.dt).tz_convert("America/New_York")
    hours += list(dt.hour)
    d0 = dt.tz_localize(None).normalize()
    rows = []
    for d, h, est, act in zip(d0, dt.hour, e.est.values, e.act.values):
        i = CAL.searchsorted(d + pd.Timedelta(days=1) if h >= 16 else d)
        if i <= 0 or i >= len(CAL):
            continue
        a = ADJ[t].values
        r1 = a[i] / a[i - 1] - 1
        r2 = a[min(i + 1, len(a) - 1)] / a[i - 1] - 1 if h < 16 else np.nan     # for the timing check only
        rows.append((i, d, est, act, r1, r2))
    REP[t] = pd.DataFrame(rows, columns=["i", "date", "est", "act", "react", "react2"]).sort_values("i").reset_index(drop=True)


# ------------------------------------------------------------------ events
def events(thr=0.30):
    dd = ADJ / ADJ.rolling(252, min_periods=200).max() - 1
    sma = ADJ.rolling(200, min_periods=200).mean()
    r126 = ADJ / ADJ.shift(126) - 1
    f252 = ADJ.shift(-252) / ADJ - 1; f504 = ADJ.shift(-504) / ADJ - 1
    i252 = IDX.shift(-252) / IDX - 1; i504 = IDX.shift(-504) / IDX - 1
    me = ME[(ME >= "2010-06-30") & (ME <= CAL[-253])]
    mask = ((dd <= -thr) & (ADJ < sma)).loc[me]
    rows = []
    for t in TICK:
        last = None; m = MON[t]; rep = REP.get(t)
        for dt in mask.index[mask[t].values]:
            if last is not None and (dt - last).days < 360:
                continue
            last = dt
            fu = m.loc[dt]
            if not (fu.rev_ttm == fu.rev_ttm and fu.ni_ttm == fu.ni_ttm):
                continue
            i = pos[dt]
            peers = SECT.index[(SECT == SECT[t]) & (SECT.index != t)]
            row = dict(ticker=t, date=dt, u1=bool(IN_U1[t]), sector=SECT[t], peer126=np.nanmedian(r126.loc[dt, peers].values),
                       f252=f252.at[dt, t], f504=f504.at[dt, t], x252=f252.at[dt, t] - i252[dt], x504=f504.at[dt, t] - i504[dt],
                       rev=fu.rev_ttm, rev0=fu.rev_prev, ni=fu.ni_ttm, ni0=fu.ni_prev, ocf=fu.ocf_ttm,
                       cashsti=(fu.cash_val if fu.cash_val == fu.cash_val else np.nan) + (fu.sti_val if fu.sti_val == fu.sti_val else 0.0),
                       sh=fu.sh_val, sh0=fu.sh_prev, ps=fu.ps, ps_med=fu.ps_med, ps_q25=fu.ps_q25, i=i)
            row.update(est=np.nan, act=np.nan, act_yago=np.nan, est_next=np.nan, act_next_yago=np.nan, minreact=np.nan, has_rep=False)
            if rep is not None and len(rep):
                past = rep[(rep.i <= i) & rep.act.notna()]
                if len(past):
                    L = past.iloc[-1]; row.update(est=L.est, act=L.act, has_rep=True)
                    ya = rep[(rep.date >= L.date - pd.Timedelta(days=390)) & (rep.date <= L.date - pd.Timedelta(days=340)) & rep.act.notna()]
                    if len(ya):
                        row["act_yago"] = ya.iloc[-1].act
                    rec = past[past.i > i - 126]
                    row["minreact"] = rec.react.min() if len(rec) else 0.0
                nxt = rep[(rep.i > i) & rep.est.notna()]
                if len(nxt):
                    Nn = nxt.iloc[0]; row["est_next"] = Nn.est
                    ya = rep[(rep.date >= Nn.date - pd.Timedelta(days=390)) & (rep.date <= Nn.date - pd.Timedelta(days=340)) & rep.act.notna()]
                    if len(ya):
                        row["act_next_yago"] = ya.iloc[-1].act
            rows.append(row)
    return pd.DataFrame(rows).dropna(subset=["f252"]).reset_index(drop=True)


def flag(e, name, cond, valid):
    e[name] = np.where(valid, cond, np.nan)


def tests(e, mult=2.0, dil=0.10):
    e = e.copy()
    flag(e, "T1b", e.act >= e.est, e.act.notna() & e.est.notna())
    flag(e, "T1c", e.est >= e.act_yago, e.est.notna() & e.act_yago.notna())
    flag(e, "T1d", e.est_next >= e.act_next_yago, e.est_next.notna() & e.act_next_yago.notna())
    flag(e, "T3c", ~(e.minreact <= -0.08), e.has_rep)
    flag(e, "T3b", ~((e.minreact <= -0.08) & (e.peer126 > -0.10)), e.has_rep)
    burn = np.where(e.ocf < 0, -e.ocf, 0.0)
    t2 = (e.ni > 0) | (e.ocf >= 0) | (e.cashsti >= mult * burn)
    flag(e, "T2", t2, (e.ni > 0) | e.ocf.notna())
    flag(e, "T2p", e.ni > 0, e.ni.notna())
    imp_ok = e.rev0.notna() & e.ni0.notna() & (e.rev0 > 0) & (e.rev > 0)
    margin_up = (e.ni / e.rev) >= (e.ni0 / e.rev0)
    flag(e, "improving", (e.rev >= e.rev0) & margin_up, imp_ok)
    flag(e, "improving_m", margin_up, imp_ok)
    flag(e, "cheap", e.ps < e.ps_med, e.ps.notna() & e.ps_med.notna())
    flag(e, "cheap25", e.ps < e.ps_q25, e.ps.notna() & e.ps_q25.notna())
    ratio = e.sh / e.sh0
    flag(e, "nodilute", ratio <= 1 + dil, ratio.between(0.5, 3))
    return e


def desc(x):
    v = x.x252.dropna()
    if len(v) < 5:
        return None
    return (len(v), v.median(), v.mean(), v.quantile(.05), (v > 0).mean(), (x.loc[v.index, "f252"] < -0.5).mean(),
            x.x504.dropna().median() if x.x504.notna().sum() > 5 else np.nan)


def diff_ci(e, f, B=1500):
    e = e[e[f].notna()]
    a, b = e[e[f] == 1], e[e[f] == 0]
    if len(a) < 30 or len(b) < 30:
        return None
    obs = a.x252.median() - b.x252.median()
    groups = [g for _, g in e.groupby(e.date.dt.to_period("M"))]
    bs = []
    for _ in range(B):
        s = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        bs.append(s[s[f] == 1].x252.median() - s[s[f] == 0].x252.median())
    return obs, np.nanquantile(bs, .05), np.nanquantile(bs, .95), len(a), len(b)


def compare(e, f, label):
    """one row: design and holdout pass-minus-fail, tail stats, verdict"""
    d, h = e[e.date <= DESIGN_END], e[e.date > DESIGN_END]
    cd, ch = diff_ci(d, f), diff_ci(h, f, B=600)
    def tail(x):
        a, b = x[x[f] == 1], x[x[f] == 0]
        if len(a) < 30 or len(b) < 30:
            return "n/a", "n/a"
        return (f"{pc(a.x252.quantile(.05))} / {pc(b.x252.quantile(.05))}",
                f"{100*(a.f252 < -.5).mean():.1f}% / {100*(b.f252 < -.5).mean():.1f}%")
    if cd is None:
        pr(f"| {label} | not testable (a group has under 30 design events) | | | | | |"); return
    works = cd[0] >= 0.03 and cd[1] > 0 and ch is not None and ch[0] > 0
    t5, lh = tail(d)
    pr(f"| {label} | {cd[3]} / {cd[4]} | {pc(cd[0])} ({pc(cd[1])} to {pc(cd[2])}) | {t5} | {lh} | "
       f"{'n/a' if ch is None else pc(ch[0]) + f' ({ch[3]}/{ch[4]})'} | {'works' if works else 'fails'} |")


HDR = ("| Test | Design events pass / fail | Median 12m vs index, pass minus fail (90% interval) | Worst 5% pass / fail | Lost over half pass / fail | Holdout pass minus fail (events) | Verdict |\n"
       "|---|---|---|---|---|---|---|")

if __name__ == "__main__":
    pr("# Round 2 results\n")
    pr(f"Stocks with prices, filings and a sector label: {len(TICK)} ({int(IN_U1.sum())} index members, {int((~IN_U1).sum())} others). "
       f"Stocks with earnings history: {len(REP)}.")
    hh = pd.Series(hours).value_counts(normalize=True).sort_index()
    pr("Report-time hours (New York) in the earnings data: " + ", ".join(f"{int(h)}h {100*v:.0f}%" for h, v in hh.items() if v >= 0.02))
    ev = tests(events(0.30))
    ev.drop(columns=["i"]).to_csv(os.path.join(HERE, "results", "round2_events.csv"), index=False, float_format="%.5f")
    for lab, e in (("index members (U1)", ev[ev.u1]), ("all stocks (U1+U2)", ev)):
        d = e[e.date <= DESIGN_END]; h = e[e.date > DESIGN_END]
        a, b = desc(d), desc(h)
        pr(f"\nDown events, {lab}: design {a[0]} (median 12m vs index {pc(a[1])}, worst 5% {pc(a[3])}, lost over half {100*a[5]:.1f}%); "
           f"holdout {b[0]} (median {pc(b[1])}, worst 5% {pc(b[3])}, lost over half {100*b[5]:.1f}%).")
    pr("\n## B. Buy-tests 1 and 3 with earnings data\n"); pr(HDR)
    for f, lab in (("T1b", "T1b met expectations"), ("T1c", "T1c growth expected"), ("T1d", "T1d forward growth expected (look-ahead)"),
                   ("T3b", "T3b no company-specific earnings shock"), ("T3c", "T3c no earnings-day drop of 8%+")):
        compare(ev[ev.u1], f, lab + ", U1"); compare(ev, f, lab + ", U1+U2")
    pr("\n## C. Buy-test 2 on the wider universe (U1+U2)\n"); pr(HDR)
    compare(ev, "T2", "T2 profitable or funded 2x"); compare(tests(events(0.30), mult=1), "T2", "T2 funded 1x")
    compare(tests(events(0.30), mult=3), "T2", "T2 funded 3x"); compare(ev, "T2p", "T2p profitable only")
    pr("\n## D. Cheap plus improving, and dilution (U1+U2)\n"); pr(HDR)
    ch = ev[ev.cheap == 1]
    compare(ch, "improving", "D1 among cheap: improving vs not"); compare(ch, "improving_m", "D1 variant: margin-only improving")
    compare(ev[ev.cheap25 == 1], "improving", "D1 variant: among bottom-quartile P/S")
    compare(ev, "nodilute", "D2 not diluting (<=10%) vs diluting")
    compare(tests(events(0.30), dil=.05), "nodilute", "D2 variant: threshold 5%"); compare(tests(events(0.30), dil=.20), "nodilute", "D2 variant: threshold 20%")
    compare(ev, "cheap", "D3 cheap vs own history vs not")

    # ---------------- E1
    pr("\n## E1. Half now, half on confirmation (U1 down events, 24 months, undeployed half in the S&P 500)\n")
    sma = ADJ.rolling(200, min_periods=200).mean(); mepos = np.array([pos[d] for d in ME])
    res = []
    for r in ev[ev.u1 & ev.f504.notna()].itertuples():
        a = ADJ[r.ticker].values; i = r.i; S = lambda k: a[i + k] / a[i]; I = lambda k: IDX.values[i + k] / IDX.values[i]
        rep = REP.get(r.ticker); k_rep = k_tr = None
        if rep is not None:
            ok = rep[(rep.i > i) & (rep.act >= rep.est) & (rep.react > -0.05)]
            if len(ok):
                k_rep = int(ok.iloc[0].i) - i + 1
        for m in mepos[(mepos > i) & (mepos < i + 504)]:
            if a[m] > sma[r.ticker].values[m]:
                k_tr = m - i + 1; break
        def half(k):
            if k is None or k >= 504 or not np.isfinite(S(k)):
                return 0.5 * S(504) + 0.5 * I(504)
            return 0.5 * S(504) + 0.5 * I(k) * S(504) / S(k)
        ks = [k for k in (k_rep, k_tr) if k is not None]
        res.append(dict(date=r.date, Full=S(504) - 1, Half_report=half(k_rep) - 1, Half_trend=half(k_tr) - 1,
                        Half_either=half(min(ks) if ks else None) - 1, Half_only=half(None) - 1, Index=I(504) - 1))
    R1 = pd.DataFrame(res)
    R1.to_csv(os.path.join(HERE, "results", "round2_e1.csv"), index=False, float_format="%.5f")
    pr("| Rule | Design median | Design mean | Design worst 5% | Holdout median | Holdout worst 5% | Verdict vs Full |"); pr("|---|---|---|---|---|---|---|")
    d, h = R1[R1.date <= DESIGN_END], R1[R1.date > DESIGN_END]
    for c in ["Full", "Half_report", "Half_trend", "Half_either", "Half_only", "Index"]:
        v = ""
        if c not in ("Full", "Index"):
            v = "works" if (d[c].quantile(.05) - d.Full.quantile(.05) >= .03 and d[c].median() - d.Full.median() >= -.03
                            and h[c].quantile(.05) >= h.Full.quantile(.05)) else "fails"
        pr(f"| {c.replace('_', ' + ')} | {pc(d[c].median())} | {pc(d[c].mean())} | {pc(d[c].quantile(.05))} | {pc(h[c].median())} | {pc(h[c].quantile(.05))} | {v} |")
    pr(f"\nEvents: design {len(d)}, holdout {len(h)}. Trading costs ignored.")

    # ---------------- E2
    pr("\n## E2. Deploying new money: invest each month, or hold cash and wait (36 monthly contributions)\n")
    rf = pd.read_csv(os.path.join(DATA, "fred_DTB3.csv"), index_col=0, parse_dates=True, na_values=".").iloc[:, 0]
    pr("| Fund | Rule | Windows | Median value per 1 contributed | Worst 5% | Windows where waiting beats investing at once | Median share of time in cash |"); pr("|---|---|---|---|---|---|---|")
    spx = read("px__GSPC.csv", "adj")
    for fund in ("SPY", "QQQ"):
        p = read(f"px_{fund}.csv", "adj"); c = p.index
        r = (rf.reindex(c.union(rf.index)).ffill().reindex(c).fillna(0) / 100 / 252).values
        pv = p.values; hi = p.rolling(252, min_periods=120).max().values
        sr = spx.reindex(c).pct_change().values
        me_i = np.array([np.where(c == d)[0][0] for d in pd.Series(c, index=c).groupby(c.to_period("M")).last().values])
        me_i = me_i[me_i >= 252]
        def sim(s, rule):
            """contributions at month-ends s..s+35, valued at month-end s+36"""
            cash = units = 0.0; contrib = set(me_i[s:s + 36]); cash_days = 0
            for j in range(me_i[s], me_i[s + 36] + 1):
                cash *= 1 + r[j]
                if j in contrib:
                    cash += 1.0
                if cash > 0:
                    if rule == "now": go = True
                    elif rule[0] == "dip": go = j in contrib and pv[j] <= (1 - rule[1]) * hi[j]
                    else: go = sr[j] <= -rule[1]
                    if go:
                        units += cash / pv[j]; cash = 0.0
                cash_days += cash > 0
            return (units * pv[me_i[s + 36]] + cash) / 36, cash_days / (me_i[s + 36] - me_i[s] + 1)
        S = range(len(me_i) - 36)
        base = np.array([sim(s, "now")[0] for s in S])
        pr(f"| {fund} | Invest each month | {len(base)} | {base.mean() and np.median(base):.2f} | {np.quantile(base, .05):.2f} | | 0% |")
        for rule, lab in ((("dip", .10), "Wait for 10% below high (pre-registered)"), (("dip", .05), "Wait for 5% below high"), (("dip", .20), "Wait for 20% below high"),
                          (("day", .02), "Buy on S&P one-day drop of 2%+ (added at client's request, not pre-registered)"),
                          (("day", .03), "Buy on S&P one-day drop of 3%+ (added, not pre-registered)")):
            x = np.array([sim(s, rule) for s in S])
            pr(f"| {fund} | {lab} | {len(x)} | {np.median(x[:, 0]):.2f} | {np.quantile(x[:, 0], .05):.2f} | {100*(x[:, 0] > base).mean():.0f}% | {100*np.median(x[:, 1]):.0f}% |")
    open(os.path.join(HERE, "results", "round2.md"), "w").write("\n".join(OUT) + "\n")
