# Portfolio exit-strategy study

- `HYPOTHESES.md` — rules and decision criteria, committed before testing.
- `REPORT.md` — market read, results, recommendation.
- `results/` — summary tables (`tables.md`, `summary_all.csv`, `perturbation.csv`, `survival.csv`, `current_state.csv`).

Rerun (Python 3 with pandas, numpy, requests, lxml; needs access to Yahoo Finance, FRED, Wikipedia):

```bash
python3 fetch_data.py          # downloads ~650 price series into data/ (not committed)
python3 run_tests.py design    # data up to 10 Nov 2023 only
python3 summarize.py
python3 run_tests.py holdout   # opens Nov 2023 - Nov 2026
WINDOW=504 python3 run_tests.py design designA designB
python3 summarize.py && python3 summarize.py _T504 && python3 make_tables.py
python3 current_state.py
```

The stock universe is a seeded random sample of today's index members, so a rerun
on a later date draws a slightly different universe unless `data/universe.json` is kept.
