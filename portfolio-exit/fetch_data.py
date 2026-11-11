"""Download all data used by the backtests.

Sources
- Yahoo Finance chart API (daily adjusted closes): query1.finance.yahoo.com/v8/finance/chart/<ticker>
- FRED CSV: DTB3 (3-month T-bill), BAA10Y (Moody's Baa minus 10y Treasury), VIXCLS, DGS10, DGS2
- Wikipedia constituent tables (current members only -> survivorship bias, see REPORT.md)

Usage: python3 fetch_data.py   (writes ./data/*.csv)
"""
import io, json, os, random, sys, time, hashlib
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-script"}
SEED = 42

HOLDINGS = ["AAOI", "NOW", "OSCR", "ASTS", "AMZN", "GOOG", "ADUR", "ACT.CN", "TE", "AMPG"]
INDICES = ["^GSPC", "^NDX", "^GSPTSE", "^GDAXI", "^FTSE", "^N225", "RSP", "SPY", "QQQ",
           "IWM", "XLE", "XLK", "XLF", "XLV", "XLU", "XLI", "XLY", "XLP", "IGV", "SMH", "MTUM", "^VIX", "^VIX3M"]


def wiki_table(url, col_candidates, suffix=""):
    html = requests.get(url, headers=UA, timeout=30).text
    out = []
    for t in pd.read_html(io.StringIO(html)):
        for c in t.columns:
            if str(c) in col_candidates:
                vals = [str(v).strip() for v in t[c].dropna()]
                if len(vals) >= 25:
                    out = vals
                    break
        if out:
            break
    return [v.replace(".", "-") + suffix if suffix == "" else v + suffix for v in out]


def universe():
    us = []
    for u in ["https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
              "https://en.wikipedia.org/wiki/List_of_S%26P_400_companies",
              "https://en.wikipedia.org/wiki/List_of_S%26P_600_companies"]:
        got = wiki_table(u, {"Symbol", "Ticker symbol", "Ticker"})
        print(u.split("/")[-1], len(got))
        us += got
    us = sorted(set(us))
    random.Random(SEED).shuffle(us)
    us = us[:420]
    intl = []
    for u, cols, suf in [
        ("https://en.wikipedia.org/wiki/S%26P/TSX_60", {"Symbol", "Ticker"}, ".TO"),
        ("https://en.wikipedia.org/wiki/DAX", {"Ticker", "Ticker symbol", "Symbol"}, ""),
        ("https://en.wikipedia.org/wiki/FTSE_100_Index", {"Ticker", "EPIC"}, ".L"),
    ]:
        try:
            got = wiki_table(u, cols, suf)
            if suf == ".TO":
                got = [g.replace(".", "-", g.count(".") - 1) for g in got]
            if suf == "" and "DAX" in u:
                got = [g.replace("-DE", "").replace(".DE", "") + ".DE" for g in got]
            print(u.split("/")[-1], len(got))
            intl += got
        except Exception as e:
            print("FAILED", u, e)
    return us, sorted(set(intl))


def yahoo(t):
    fn = os.path.join(DATA, "px_" + t.replace("^", "_") + ".csv")
    if os.path.exists(fn):
        return t, True
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}"
    for attempt in range(4):
        try:
            r = requests.get(url, params={"period1": 0, "period2": int(time.time()), "interval": "1d",
                                          "events": "div,split"}, headers=UA, timeout=40)
            if r.status_code == 404:
                return t, False
            r.raise_for_status()
            res = r.json()["chart"]["result"][0]
            ts = pd.to_datetime(res["timestamp"], unit="s").normalize()
            adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose") or res["indicators"]["quote"][0]["close"]
            s = pd.Series(adj, index=ts, name="adj").dropna()
            s = s[~s.index.duplicated(keep="last")]
            s.to_csv(fn)
            return t, True
        except Exception as e:
            time.sleep(2 ** attempt)
    return t, False


def fred(sid):
    # FRED drops python-requests connections behind some proxies; curl is reliable.
    import subprocess
    subprocess.run(["curl", "-sS", "-m", "60", "--retry", "3", "-o", os.path.join(DATA, f"fred_{sid}.csv"),
                    f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"], check=True)


if __name__ == "__main__":
    ufile = os.path.join(DATA, "universe.json")
    if os.path.exists(ufile):
        U = json.load(open(ufile))
    else:
        us, intl = universe()
        U = {"us": us, "intl": intl, "holdings": HOLDINGS, "indices": INDICES}
        json.dump(U, open(ufile, "w"))
    for sid in ["DTB3", "BAA10Y", "VIXCLS", "DGS10", "DGS2", "T10Y2Y"]:
        fred(sid)
    allt = U["us"] + U["intl"] + U["holdings"] + U["indices"]
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(yahoo, allt))
    bad = [t for t, ok in res if not ok]
    print("downloaded", len(res) - len(bad), "failed", bad)
