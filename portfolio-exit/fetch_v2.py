"""Round-2 data. Writes into data/:
  screener.csv            Nasdaq screener list (symbol, market cap, country, sector, industry)
  universe2.json          seeded sample of 400 non-index US stocks (U2)
  px2_<T>.csv             close (split-adjusted), adjclose, for U1+U2
  splits.json             split events per ticker
  fundamentals2.pkl       EDGAR series incl. share counts for U1+U2
  earnings.pkl            Yahoo earnings history per ticker (date, estimate, reported)
Sources: api.nasdaq.com/api/screener/stocks, query1.finance.yahoo.com chart API, yfinance earnings dates, data.sec.gov.
Usage: python3 fetch_v2.py [list|prices|edgar|earnings]
"""
import json, os, pickle, random, sys, time, warnings
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests
import fetch_fundamentals as FF
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-script", "Accept": "application/json"}
FF.TAGS["shares"] = ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"]


def tickers():
    U = json.load(open(os.path.join(DATA, "universe.json")))
    return U["us"] + json.load(open(os.path.join(DATA, "universe2.json")))


def do_list():
    r = requests.get("https://api.nasdaq.com/api/screener/stocks", params={"tableonly": "true", "download": "true"}, headers=UA, timeout=60)
    df = pd.DataFrame(r.json()["data"]["rows"])
    df["mcap"] = pd.to_numeric(df.marketCap, errors="coerce")
    df["symbol"] = df.symbol.str.strip().str.replace("/", "-", regex=False)
    df[["symbol", "name", "mcap", "country", "sector", "industry", "ipoyear"]].to_csv(os.path.join(DATA, "screener.csv"), index=False)
    U1 = set(json.load(open(os.path.join(DATA, "universe.json")))["us"])
    c = df[(df.country == "United States") & (df.mcap > 3e8) & ~df.symbol.isin(U1) & df.symbol.str.fullmatch(r"[A-Z]{1,5}")
           & df.name.str.contains("Common Stock|Class A", na=False) & ~df.name.str.contains("Warrant|Unit|Right|Preferred|Depositary|ETF|Fund|Trust", na=False)
           & df.sector.notna() & (df.sector != "")]
    names = sorted(c.symbol.unique()); random.Random(43).shuffle(names)
    json.dump(names[:400], open(os.path.join(DATA, "universe2.json"), "w"))
    print("screener rows", len(df), "candidates", len(names), "sampled", 400)


def px(t):
    fn = os.path.join(DATA, f"px2_{t}.csv")
    if os.path.exists(fn):
        return t, None
    for a in range(4):
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}", params={"period1": 0, "period2": int(time.time()),
                             "interval": "1d", "events": "div,split"}, headers=UA, timeout=40)
            if r.status_code == 404:
                return t, "404"
            r.raise_for_status()
            res = r.json()["chart"]["result"][0]
            ts = pd.to_datetime(res["timestamp"], unit="s").normalize()
            q = res["indicators"]
            df = pd.DataFrame({"close": q["quote"][0]["close"], "adj": q["adjclose"][0]["adjclose"]}, index=ts).dropna()
            df[~df.index.duplicated(keep="last")].to_csv(fn)
            sp = [(pd.to_datetime(v["date"], unit="s").strftime("%Y-%m-%d"), v["numerator"] / v["denominator"])
                  for v in res.get("events", {}).get("splits", {}).values()]
            return t, sp
        except Exception as e:
            time.sleep(2 ** a)
    return t, "fail"


def do_prices():
    sf = os.path.join(DATA, "splits.json")
    S = json.load(open(sf)) if os.path.exists(sf) else {}
    with ThreadPoolExecutor(5) as ex:
        for t, sp in ex.map(px, tickers()):
            if isinstance(sp, list):
                S[t] = sp
    json.dump(S, open(sf, "w"))
    print("prices", sum(os.path.exists(os.path.join(DATA, f"px2_{t}.csv")) for t in tickers()), "of", len(tickers()), "splits for", len(S))


def do_edgar():
    m = requests.get("https://www.sec.gov/files/company_tickers.json", headers=FF.UA, timeout=60).json()
    cik = {v["ticker"].replace(".", "-"): v["cik_str"] for v in m.values()}
    jobs = [(t, cik[t]) for t in tickers() if t in cik]

    def f(a):
        t, rec = FF.facts(a)
        if rec is None:
            return t, None
        # share counts are in units "shares", not USD: fetch separately
        try:
            g = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{a[1]:010d}.json", headers=FF.UA, timeout=60).json()["facts"].get("us-gaap", {})
            rows = []
            for pri, tag in enumerate(FF.TAGS["shares"]):
                for x in g.get(tag, {}).get("units", {}).get("shares", []):
                    rows.append((x.get("start"), x["end"], x["val"], x["filed"], pri))
            rec["shares"] = rows
        except Exception:
            rec["shares"] = []
        time.sleep(0.15)
        return t, rec
    with ThreadPoolExecutor(3) as ex:
        res = dict(ex.map(f, jobs))
    ok = {t: r for t, r in res.items() if r}
    pickle.dump(ok, open(os.path.join(DATA, "fundamentals2.pkl"), "wb"))
    print("edgar", len(ok), "of", len(tickers()))


def do_earnings():
    import yfinance as yf
    fn = os.path.join(DATA, "earnings.pkl")
    Eh = pickle.load(open(fn, "rb")) if os.path.exists(fn) else {}
    todo = [t for t in tickers() if t not in Eh]
    for i, t in enumerate(todo):
        for a in range(3):
            try:
                d = yf.Ticker(t).get_earnings_dates(limit=100)
                Eh[t] = None if d is None else d.reset_index().rename(columns={"Earnings Date": "dt", "EPS Estimate": "est", "Reported EPS": "act"})[["dt", "est", "act"]]
                break
            except Exception as e:
                time.sleep(5 * (a + 1))
        else:
            Eh[t] = None
        time.sleep(0.6)
        if i % 50 == 49:
            pickle.dump(Eh, open(fn, "wb")); print("earnings", i + 1, "of", len(todo), flush=True)
    pickle.dump(Eh, open(fn, "wb"))
    print("earnings done", sum(v is not None and len(v) > 0 for v in Eh.values()), "of", len(Eh))


if __name__ == "__main__":
    for step in (sys.argv[1:] or ["list", "prices", "edgar", "earnings"]):
        {"list": do_list, "prices": do_prices, "edgar": do_edgar, "earnings": do_earnings}[step]()
