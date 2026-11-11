"""Download SEC EDGAR XBRL company facts for the US sample and keep the few series needed.

Sources: https://www.sec.gov/files/company_tickers.json (ticker -> CIK),
         https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json,
         Wikipedia S&P 500/400/600 tables (GICS sector and sub-industry).
Writes data/fundamentals.pkl and data/gics.csv.
"""
import io, json, os, pickle, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "ResearchScript admin@example.com"}   # SEC requires a contact-style agent string
WUA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-script"}
TAGS = {
    "rev": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet", "SalesRevenueGoodsNet", "RevenuesNetOfInterestExpense", "InterestAndDividendIncomeOperating"],
    "ni": ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"],
    "ocf": ["NetCashProvidedByUsedInOperatingActivities", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
    "cash": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash"],
    "sti": ["ShortTermInvestments", "MarketableSecuritiesCurrent", "AvailableForSaleSecuritiesCurrent",
            "AvailableForSaleSecuritiesDebtSecuritiesCurrent"],
}


def gics():
    out = []
    for u in ["List_of_S%26P_500_companies", "List_of_S%26P_400_companies", "List_of_S%26P_600_companies"]:
        for t in pd.read_html(io.StringIO(requests.get("https://en.wikipedia.org/wiki/" + u, headers=WUA, timeout=30).text)):
            if "GICS Sector" in [str(c) for c in t.columns]:
                sym = [c for c in t.columns if str(c) in ("Symbol", "Ticker symbol", "Ticker")][0]
                out.append(pd.DataFrame({"ticker": t[sym].astype(str).str.replace(".", "-", regex=False),
                                         "sector": t["GICS Sector"], "sub": t["GICS Sub-Industry"]}))
                break
    return pd.concat(out).drop_duplicates("ticker")


def facts(args):
    t, cik = args
    for a in range(4):
        try:
            r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", headers=UA, timeout=60)
            if r.status_code == 404:
                return t, None
            r.raise_for_status()
            g = r.json()["facts"].get("us-gaap", {})
            rec = {}
            for k, tags in TAGS.items():
                rows = []
                for pri, tag in enumerate(tags):
                    for x in g.get(tag, {}).get("units", {}).get("USD", []):
                        rows.append((x.get("start"), x["end"], x["val"], x["filed"], pri))
                rec[k] = rows
            time.sleep(0.15)
            return t, rec
        except Exception:
            time.sleep(2 ** a)
    return t, None


if __name__ == "__main__":
    U = json.load(open(os.path.join(DATA, "universe.json")))
    gics().to_csv(os.path.join(DATA, "gics.csv"), index=False)
    m = requests.get("https://www.sec.gov/files/company_tickers.json", headers=UA, timeout=60).json()
    cik = {v["ticker"].replace(".", "-"): v["cik_str"] for v in m.values()}
    jobs = [(t, cik[t]) for t in U["us"] if t in cik]
    print("tickers with CIK", len(jobs), "of", len(U["us"]))
    with ThreadPoolExecutor(4) as ex:
        res = dict(ex.map(facts, jobs))
    ok = {t: r for t, r in res.items() if r}
    pickle.dump(ok, open(os.path.join(DATA, "fundamentals.pkl"), "wb"))
    print("got", len(ok), "missing", [t for t in res if not res[t]])
