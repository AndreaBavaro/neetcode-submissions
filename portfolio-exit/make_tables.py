"""Write results/tables.md from results/summary_all.csv (and the 24-month run)."""
import pandas as pd
S = pd.read_csv("results/summary_all.csv")
order = ["B1", "B2", "T1", "T2", "T3", "O1", "O2", "O3", "O4", "O5"]
sets = ["designA", "designB", "intl", "ruin", "w2000jan", "w2000mar", "w2007oct", "shuffle", "bootstrap", "holdout", "w2021dec", "actual"]
pc = lambda v: f"{100*v:+.0f}%"
out = []
def full(name, cost):
    x = S[(S.set == name) & (S.cost == cost) & S.base].set_index("strategy").loc[order]
    out.append(f"\n### {name}, cost = {cost}, n = {int(x.n.iloc[0])}\n")
    out.append("| Idea | Median 3y | Worst 5% | Worst | Median CAGR | Vol | Sharpe | Median max DD | Worst-5% max DD | Turnover | Rule vs B2 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for s, r in x.iterrows():
        out.append(f"| {s} | {pc(r.med_ret)} | {pc(r.p5_ret)} | {pc(r.worst_ret)} | {100*r.med_cagr:+.1f}% | {100*r.vol:.0f}% | {r.sharpe:.2f} | {pc(r.med_mdd)} | {pc(r.p5_mdd)} | {r.turnover:.1f}x | {'pass ('+r.rule_vs_B2+')' if r.rule_vs_B2 != '-' and s[0] != 'B' else ('' if s[0]=='B' else 'fail')} |")
for n in ["designA", "designB"]:
    full(n, "high"); full(n, "low")
full("holdout", "high")
for col, title in [("p5_ret", "Worst-5% 36-month return"), ("med_ret", "Median 36-month return"), ("p5_mdd", "Worst-5% in-window drawdown")]:
    out.append(f"\n### {title} by test set, cost = high, pre-registered settings\n")
    out.append("| Idea | " + " | ".join(sets) + " |"); out.append("|---|" + "---|" * len(sets))
    p = S[(S.cost == "high") & S.base].pivot(index="strategy", columns="set", values=col).loc[order, sets]
    for s, r in p.iterrows():
        out.append(f"| {s} | " + " | ".join(pc(v) for v in r) + " |")
P = S[(S.cost == "high") & S.set.isin(["designA", "designB"]) & ~S.strategy.isin(["B1", "B2"])]
out.append("\n### Parameter perturbation, cost = high (median / worst-5%, designA then designB)\n")
out.append("| Idea | Setting | A median | A worst 5% | B median | B worst 5% | Passes rule (A/B) |"); out.append("|---|---|---|---|---|---|---|")
for (s, p), g in P.groupby(["strategy", "param"], sort=False):
    a, b = g[g.set == "designA"].iloc[0], g[g.set == "designB"].iloc[0]
    out.append(f"| {s} | {p}{' (pre-registered)' if a.base else ''} | {pc(a.med_ret)} | {pc(a.p5_ret)} | {pc(b.med_ret)} | {pc(b.p5_ret)} | {a.rule_vs_B2}/{b.rule_vs_B2} |")
T = pd.read_csv("results/summary_all_T504.csv")
out.append("\n### 24-month window (not pre-registered, robustness only), cost = high\n")
out.append("| Idea | A median | A worst 5% | B median | B worst 5% |"); out.append("|---|---|---|---|---|")
x = T[(T.cost == "high") & T.base]
for s in order:
    a, b = x[(x.set == "designA") & (x.strategy == s)].iloc[0], x[(x.set == "designB") & (x.strategy == s)].iloc[0]
    out.append(f"| {s} | {pc(a.med_ret)} | {pc(a.p5_ret)} | {pc(b.med_ret)} | {pc(b.p5_ret)} |")
open("results/tables.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
