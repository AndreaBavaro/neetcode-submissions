# Exit-strategy study — 11 Nov 2026

Analysis, not regulated advice. Every backtest number below was produced by the
code in this folder; nothing is estimated. Full tables: `results/tables.md`,
`results/summary_all.csv`.

## Verdict

**None of the eight ideas beat the plain baselines under the rule fixed in
advance.** 40 rule variants were tried (8 ideas x 5 settings). Zero of 40
passed in either half of the design universe, and none of the eight
pre-registered settings passed in the non-US test or the holdout.

The recommendation is therefore the plain one: sell the single-stock book in
equal installments. The only tilt that never damaged the bad tail (selling a
little more into strength) is noted as optional, not as a proven edge.

## 1. Market read

Sources: two web-research passes on 11 Nov 2026 (links in the session notes)
and `current_state.py` on the downloaded data. Where only secondary sources
were found, that is said.

- **Index vs leaders.** S&P 500 at 7,580 is 3% below its 6 Oct record and 3%
  above its 200-day average. The Nasdaq-100 is 10% off its high, semis (SMH)
  25% off, the momentum factor ETF 20% off. Equal-weight S&P is within 1% of
  its high. Health care +29% and energy +44% over 12 months lead; software
  is -9%.
- **Breadth.** 57% of my 411-stock US sample is above its 200-day average.
  Reported S&P breadth was only 46% at the October index record against 74%
  at the August high.
- **Volatility.** VIX 18 with the curve back in contango, after 28 on 5 Nov
  (S&P -4.4% in a day). Implied correlation stayed near 22% on that day: the
  damage is stock-specific, not market-wide. ServiceNow -27%, Alphabet -12%,
  Fortinet -22% on results.
- **Rates.** Fed funds 3.75–4.00% after a September hike, a further hike
  priced for December; 10-year about 4.9% after 5.35% in October, the highest
  since 2002. Core PCE 3.1%, payrolls and ISM strong.
- **Credit.** Baa spread 1.51 points, 0.16 lower than three months ago, so
  broad credit is calm. The stress is concentrated: CoreWeave CDS above
  1,100bp, Oracle near 300bp, hyperscaler bond supply of about USD 296bn this
  year (secondary source).
- **Positioning.** Hedge-fund net leverage reported at a five-year low after
  the momentum unwind; AAII bears 48%. Margin debt growth has rolled over
  from a record.
- **Valuation.** Forward P/E 17.7 (lowest since Nov 2023) because forward
  earnings are up a third; Shiller CAPE about 41. The market is paying less
  for earnings it does not trust to last.

**What it resembles.** Mostly mid-2000: the index near its high while the
leaders break, equal-weight and defensives rising, capex funded by debt, a
central bank still tightening. It also carries 2022's rate shock. It is unlike
2007: broad credit is tight and banks are not the problem. In 2000–02 the
damage was a slow, stock-specific grind in the former leaders; that is the
risk this book carries (60% AI/big tech, four unprofitable names).

## 2. Ideas

Exact rules, reasons and expected failure conditions are in `HYPOTHESES.md`,
committed before any test ran (commit `ba44d30`).

| Code | Idea | Origin |
|---|---|---|
| B1 | Hold, sell all at month 36 | baseline |
| B2 | Sell 1/36 each month | baseline |
| T1 | 200-day trend rule per stock, with re-entry | textbook |
| T2 | Drawdown budget (sell-only TIPP, 30% floor) | textbook |
| T3 | Sell the most volatile names first | textbook |
| O1 | Residual-trend exit: sell on stock-specific weakness only | mine |
| O2 | Stop that tightens as the deadline approaches | mine |
| O3 | Installments, larger near 12-month highs, skipped near lows | mine |
| O4 | Credit-spread widening sells the most fragile names | mine |
| O5 | Gap-and-fail: sell if a bad-news gap is not half retraced in 20 days | mine |

## 3. Tests

- **Random books.** Nine stocks drawn from the more volatile half of a
  411-stock US sample (large, mid and small cap), the mandate's weights
  assigned at random, random start dates from 1995. 2,000 books in each of
  two disjoint halves of the universe (A and B).
- **Worst windows.** 300 books each from Jan 2000, Mar 2000, Oct 2007.
- **Out of universe.** 1,500 books of Canadian, German and UK stocks.
- **Placebo.** 1,000 books with daily returns shuffled in time, which kills
  any trend or drift a rule could read.
- **Block bootstrap.** 1,000 books from resampled 63-day blocks.
- **Injected ruin.** 1,500 books where one name is made to lose 90% in a year.
- **Perturbation.** Four alternative settings per idea.
- **Holdout.** 1,500 books whose windows end between Nov 2023 and Nov 2026,
  300 books from Dec 2021, and the client's own book replayed from Nov 2023.
  Opened only after the design results were committed (commit `949a06d`).

Costs: 0.1% per trade (low) and 1.6% (high, with the 1.5% currency fee).
Tax is zero in a TFSA. Tables below use the high cost.

## 4. Results

Decision rule: against B2, either the same bad tail with 3 points more median,
or 5 points better tail with no more than 2 points less median.

### Design half A (2,000 books, cost 1.6%)

| Idea | Median 3y | Worst 5% | Worst | Median CAGR | Vol | Sharpe | Median max DD | Worst-5% max DD | Turnover | Rule vs B2 |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 | +55% | -15% | -54% | +15.7% | 29% | 0.60 | -35% | -62% | 1.7x |  |
| B2 | +32% | -12% | -38% | +9.6% | 17% | 0.53 | -22% | -45% | 1.4x |  |
| T1 | +22% | -21% | -49% | +6.7% | 19% | 0.35 | -26% | -44% | 7.0x | fail |
| T2 | +23% | -27% | -52% | +7.3% | 18% | 0.36 | -25% | -37% | 1.3x | fail |
| T3 | +29% | -16% | -47% | +8.8% | 17% | 0.50 | -21% | -48% | 1.3x | fail |
| O1 | +8% | -18% | -49% | +2.6% | 9% | 0.13 | -13% | -33% | 1.1x | fail |
| O2 | +40% | -25% | -58% | +12.0% | 23% | 0.52 | -30% | -53% | 1.6x | fail |
| O3 | +29% | -8% | -35% | +8.8% | 15% | 0.53 | -19% | -46% | 1.3x | fail |
| O4 | +26% | -23% | -46% | +8.0% | 19% | 0.40 | -26% | -44% | 1.4x | fail |
| O5 | +27% | -23% | -51% | +8.2% | 16% | 0.44 | -22% | -39% | 1.3x | fail |

Half B is within two points of half A on almost every figure
(`results/tables.md`). At 0.1% cost medians rise by one to two points for most
ideas and by about eleven for T1; no verdict changes.

### Worst-5% 36-month return across all test sets (cost 1.6%)

| Idea | A | B | Non-US | Ruin | Jan 2000 | Mar 2000 | Oct 2007 | Shuffled | Bootstrap | Holdout | Dec 2021 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | -15% | -16% | -19% | -25% | -27% | -27% | -37% | -22% | -36% | -1% | +6% |
| B2 | -12% | -11% | -15% | -20% | -10% | -15% | -39% | -13% | -19% | -3% | -9% |
| T1 | -21% | -20% | -24% | -22% | -33% | -31% | -43% | -30% | -33% | -22% | -17% |
| T2 | -27% | -27% | -27% | -28% | -12% | -16% | -33% | -19% | -24% | -10% | -10% |
| T3 | -16% | -15% | -19% | -24% | -14% | -15% | -44% | -17% | -21% | -8% | -11% |
| O1 | -18% | -13% | -15% | -16% | -10% | -14% | -26% | -15% | -13% | -3% | -1% |
| O2 | -25% | -23% | -26% | -31% | -24% | -21% | -56% | -28% | -31% | -11% | -17% |
| O3 | -8% | -8% | -13% | -17% | -4% | -12% | -37% | -10% | -20% | -4% | -8% |
| O4 | -23% | -22% | -27% | -27% | -7% | -9% | -27% | -18% | -22% | -8% | -10% |
| O5 | -23% | -24% | -26% | -27% | -23% | -24% | -42% | -19% | -25% | -7% | -7% |

### Median 36-month return across all test sets (cost 1.6%)

| Idea | A | B | Non-US | Ruin | Jan 2000 | Mar 2000 | Oct 2007 | Shuffled | Bootstrap | Holdout | Dec 2021 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | +55% | +55% | +34% | +39% | +11% | +11% | -17% | +61% | +62% | +52% | +52% |
| B2 | +32% | +32% | +19% | +23% | +15% | +15% | -27% | +34% | +33% | +29% | +18% |
| T1 | +22% | +22% | +13% | +17% | -1% | +0% | -15% | +21% | +25% | +16% | +16% |
| T2 | +23% | +22% | +14% | +15% | +16% | +10% | -29% | +31% | +30% | +27% | +22% |
| T3 | +29% | +29% | +18% | +20% | +19% | +19% | -30% | +33% | +32% | +26% | +16% |
| O1 | +8% | +10% | +7% | +8% | +4% | +1% | -17% | +9% | +10% | +14% | +13% |
| O2 | +40% | +41% | +24% | +31% | +12% | +15% | -43% | +39% | +47% | +33% | +28% |
| O3 | +29% | +30% | +17% | +20% | +23% | +21% | -23% | +35% | +29% | +28% | +17% |
| O4 | +26% | +26% | +17% | +17% | +16% | +13% | -18% | +35% | +33% | +41% | +20% |
| O5 | +27% | +21% | +17% | +17% | +8% | +5% | -27% | +20% | +30% | +25% | +22% |

### The client's own book replayed from Nov 2023 (one path, eight names)

B1 +306%, B2 +280%, O3 +299%, O2 +475%, O4 +306% (never fired), T3 +154%,
T1 +108%, T2 +97%, O5 +81%, O1 +67%. Worst drawdown on the way: B1 -61%,
B2 -26%. One path dominated by AAOI, ASTS and OSCR multiplying; every rule that
sold on weakness sold them before the rise. Treat it as an anecdote.

### What each idea did

- **T1 trend rule: killed.** Worse median and worse tail than B2 in every
  test set. Seven times the turnover. The index-level trend result in the
  earlier review does not carry over to single stocks.
- **T2 drawdown budget: killed.** It does cap the path (worst-5% drawdown
  -37% against -62% for holding) but locks the loss in: worst-5% outcome -27%
  against -15% for holding.
- **T3 most volatile first: killed.** Indistinguishable from B2, slightly
  worse.
- **O1 residual-trend exit: killed.** Smallest drawdowns of all, but it sells
  nearly everything within months and earns about the T-bill rate. It is
  "go to cash" with extra steps.
- **O2 deadline-scaled stop: killed.** Keeps most of the upside, but the tail
  is worse than holding in every design test. Failed as predicted in steady
  declines (Oct 2007: -56%).
- **O3 strength harvest: killed by the rule, closest miss.** Tail better than
  B2 in 9 of 11 test sets, by 1 to 6 points; median lower by 1 to 3 points in
  design. It misses clause (b) on both counts. It looks the same on shuffled
  prices, so it is not reading a signal: it reshapes the payoff by selling
  rallies. I predicted it would fail through a worse tail; it failed through a
  lower median instead.
- **O4 credit canary: killed.** Good in 2000 and 2007, worse than B2
  elsewhere. A crisis-only rule that is wrong most of the time.
- **O5 gap-and-fail: killed.** Worse tail than B2 almost everywhere; gaps
  recover often enough after day 20 to defeat it.

### Hold versus installments

- In ordinary periods installments improve the worst-5% outcome by only 3 to
  5 points and give up about 23 points of median.
- From the 2000 starts they improve it by 12 to 17 points and have the higher
  median. From Oct 2007 they are slightly worse.
- In the holdout, holding won on both median and tail.
- Worst-5% drawdown on the way is about -45% for installments and -62% for
  holding. Neither respects a 30% limit.

### Discount for what was tried

- 42 variants x 2 cost levels, 12 test sets, plus one 24-month rerun that was
  not pre-registered (same ranking; `results/tables.md`).
- The overlapping windows hold roughly nine independent three-year periods.
- With 40 variants, one or two would be expected to pass by luck. None did,
  so no discount is needed for a claimed winner; O3's near-miss should be
  read with that in mind.

### Limits

- **Survivorship.** The universe is today's index members. Stocks that
  failed are missing, which flatters holding and penalises every rule that
  sells weakness. The ruin test corrects this only crudely.
- Monthly reviews cannot avoid one-day gaps.
- US-centred history; the non-US set is large caps only.
- Aduro has no price history before Aug 2024 and is left out of the replay.

### Deviations from the pre-registered plan

1. The first ruin run returned NaN for 60% of trials (stocks with short
   history). Fixed and rerun before any conclusion was drawn.
2. Shuffled and bootstrap tests need 600 days of history per stock, not 300.
3. Tickers with a single-day move above x7.4 were dropped as bad data.
4. O5 and the T2 peak are monitored daily; all other rules monthly, as written.
5. A stock that stops trading mid-window is frozen at its last price.
6. The 24-month rerun was added afterwards.

## 5. Recommendation

1. **Use plain installments on the single-stock book.** Each month sell an
   equal share count of every remaining stock so the last lot goes in late
   2029. Judgment: the present market resembles 2000 more than any other test
   window, and that is where installments earned their keep.
2. **Do not add a trend, stop, credit or gap rule.** Each made the bad tail
   worse. This includes the "sell half if the S&P is below its 10-month
   average" rule proposed for 2029 in the earlier review, as far as it rests
   on single-stock behaviour; its index-level form was not retested here.
3. **Optional tilt (O3), unproven.** At a review, sell two lots of a name in
   the top fifth of its 12-month range and none of a name in the bottom fifth,
   with the catch-up schedule in the final 12 months. Expect a slightly better
   bad tail and a slightly lower median.
4. **Fundamental sells from the earlier review stand apart from this study.**
   Nothing here tests company-specific judgment. Note the conflict: today O3
   would sell OSCR and AMZN (range position 0.90 and 0.82) and defer TE, AMPG,
   ASTS, AAOI, GOOG, NOW and ADUR (0.01 to 0.20). Where the earlier review
   found a broken business (TE, AMPG), its sell overrides the tilt.

### Per holding (signals as of 11 Nov 2026, `results/current_state.csv`)

| Holding | 12-month range position | Plain installments | With optional tilt this month |
|---|---|---|---|
| OSCR | 0.90 | 1 lot | 2 lots |
| AMZN | 0.82 | 1 lot | 2 lots |
| NOWS | 0.20 | 1 lot | 0 lots |
| AAOI | 0.17 | 1 lot | 0 lots |
| GOOG | 0.13 | 1 lot | 0 lots |
| ACT (ADUR) | 0.19 | 1 lot | 0 lots |
| ASTS | 0.05 | 1 lot | 0 lots |
| TE | 0.01 | sell per earlier review | sell per earlier review |
| AMPG | 0.10 | sell per earlier review | sell per earlier review |

### Signs to abandon

- You skip two scheduled lots in a row. The schedule only works if it is
  mechanical.
- Realised cost per sale exceeds 1.6%.
- Under the tilt, a name sits in the bottom fifth of its range for six
  straight reviews. The tilt is then only deferring a loser; return that name
  to plain lots.
- The departure date moves. Re-cut the lots to the new date.
