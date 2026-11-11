"""Summarise results_*.pkl into results/*.csv and apply the pre-registered decision rule.

  python3 summarize.py            # all result sets present in data/
"""
import glob, os, sys
import numpy as np, pandas as pd
import engine as E

OUT = os.path.join(E.HERE, "results")
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)


def stats(g):
    cagr = (1 + g.ret) ** (252 / T) - 1
    return pd.Series(dict(
        n=len(g), med_ret=g.ret.median(), p5_ret=g.ret.quantile(.05), worst_ret=g.ret.min(), mean_ret=g.ret.mean(),
        med_cagr=cagr.median(), vol=g.vol.median(), sharpe=g.sharpe.median(),
        med_mdd=g.mdd.median(), p5_mdd=g.mdd.quantile(.05), worst_mdd=g.mdd.min(), turnover=g.turnover.mean()))


def verdict(s, b2):
    a = s.p5_ret >= b2.p5_ret - .02 and s.med_ret >= b2.med_ret + .03
    b = s.p5_ret >= b2.p5_ret + .05 and s.med_ret >= b2.med_ret - .02
    return "a" if a else ("b" if b else "-")


if __name__ == "__main__":
    sfx = sys.argv[1] if len(sys.argv) > 1 else ""
    T = int(sfx[2:]) if sfx else 756
    files = sorted(glob.glob(os.path.join(E.DATA, f"results_*{sfx}.pkl")))
    if not sfx:
        files = [f for f in files if "_T" not in os.path.basename(f)]
    allsum = []
    for f in files:
        df = pd.read_pickle(f)
        name = df.set.iloc[0]
        s = df.groupby(["strategy", "param", "cost"], sort=False).apply(stats, include_groups=False).reset_index()
        s.insert(0, "set", name)
        s["base"] = [str(E.BASE[a]) == b for a, b in zip(s.strategy, s.param)]
        out = []
        for cl in E.COSTS:
            x = s[s.cost == cl].copy()
            b1 = x[x.strategy == "B1"].iloc[0]; b2 = x[x.strategy == "B2"].iloc[0]
            x["rule_vs_B2"] = [verdict(r, b2) for r in x.itertuples()]
            x["p5_beats_B1"] = x.p5_ret > b1.p5_ret
            out.append(x)
        allsum.append(pd.concat(out))
    S = pd.concat(allsum)
    S.to_csv(os.path.join(OUT, f"summary_all{sfx}.csv"), index=False, float_format="%.4f")
    show = ["strategy", "param", "med_ret", "p5_ret", "worst_ret", "med_cagr", "vol", "sharpe", "med_mdd", "p5_mdd",
            "turnover", "rule_vs_B2", "p5_beats_B1"]
    for name in S.set.unique():
        for cl in ["high"]:
            x = S[(S.set == name) & (S.cost == cl) & S.base]
            print(f"\n=== {name} | cost={cl} | base settings | n={int(x.n.iloc[0])}")
            print(x[show].to_string(index=False, float_format=lambda v: f"{v:7.3f}"))
    # survival table: base rule per set, and number of parameter settings passing in design sets
    H = S[S.cost == "high"]
    piv = H[H.base].pivot(index="strategy", columns="set", values="rule_vs_B2")
    H2 = H[H.set.isin(["designA", "designB"]) & (H.strategy.str[0] != "B")].copy()
    H2["pass"] = (H2.rule_vs_B2 != "-") & H2.p5_beats_B1
    cnt = H2.groupby(["strategy", "set"])["pass"].sum().unstack()
    cnt.columns = [c + "_params_passing_of_5" for c in cnt.columns]
    piv = piv.join(cnt)
    piv.to_csv(os.path.join(OUT, f"survival{sfx}.csv"))
    print("\n=== decision rule vs B2 at high cost (a/b = passes clause a/b, - = fails)")
    print(piv.to_string())
    P = H[H.set.isin(["designA", "designB"])][["set", "strategy", "param", "med_ret", "p5_ret", "worst_ret", "p5_mdd", "turnover", "rule_vs_B2"]]
    P.to_csv(os.path.join(OUT, f"perturbation{sfx}.csv"), index=False, float_format="%.4f")
