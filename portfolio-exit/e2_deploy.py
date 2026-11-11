"""E2 from HYPOTHESES_V2.md: invest each monthly contribution at once, or hold cash and wait for a dip.
36 monthly contributions of 1 into SPY (from 1993) or QQQ (from 1999); cash earns the 3-month T-bill.
The two "one-day drop" rules were added at the client's request and were not pre-registered."""
import os, numpy as np, pandas as pd
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
rd = lambda f: pd.read_csv(os.path.join(D, f), index_col=0, parse_dates=True)["adj"]
rf = pd.read_csv(os.path.join(D, "fred_DTB3.csv"), index_col=0, parse_dates=True, na_values=".").iloc[:, 0]
spx = rd("px__GSPC.csv"); out = []
print("| Fund | Rule | Windows | Median value per 1 contributed | Worst 5% | Windows where waiting wins | Median share of days holding cash |"); print("|---|---|---|---|---|---|---|")
for fund in ("SPY", "QQQ"):
    p = rd(f"px_{fund}.csv"); c = p.index
    r = (rf.reindex(c.union(rf.index)).ffill().reindex(c).fillna(0) / 100 / 252).values
    pv = p.values; hi = p.rolling(252, min_periods=120).max().values; sr = spx.reindex(c).pct_change().values
    me = pd.Series(np.arange(len(c)), index=c).groupby(c.to_period("M")).last().values; me = me[me >= 252]
    def sim(s, rule):
        cash = units = 0.0; contrib = set(me[s:s + 36]); cd = 0
        for j in range(me[s], me[s + 36] + 1):
            cash *= 1 + r[j]
            if j in contrib: cash += 1.0
            if cash > 0:
                go = True if rule == "now" else (j in contrib and pv[j] <= (1 - rule[1]) * hi[j]) if rule[0] == "dip" else sr[j] <= -rule[1]
                if go: units += cash / pv[j]; cash = 0.0
            cd += cash > 0
        return (units * pv[me[s + 36]] + cash) / 36, cd / (me[s + 36] - me[s] + 1)
    S = range(len(me) - 36); base = np.array([sim(s, "now")[0] for s in S])
    print(f"| {fund} | Invest each month | {len(base)} | {np.median(base):.2f} | {np.quantile(base, .05):.2f} | | 0% |")
    for rule, lab in ((("dip", .10), "Wait for 10% below high (pre-registered)"), (("dip", .05), "Wait for 5% below high"), (("dip", .20), "Wait for 20% below high"),
                      (("day", .02), "Buy only on an S&P one-day drop of 2%+ (added)"), (("day", .03), "Buy only on an S&P one-day drop of 3%+ (added)")):
        x = np.array([sim(s, rule) for s in S])
        print(f"| {fund} | {lab} | {len(x)} | {np.median(x[:, 0]):.2f} | {np.quantile(x[:, 0], .05):.2f} | {100*(x[:, 0] > base).mean():.0f}% | {100*np.median(x[:, 1]):.0f}% |")
