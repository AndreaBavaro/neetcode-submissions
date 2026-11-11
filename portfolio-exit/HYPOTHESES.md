# Pre-registered hypotheses and test plan

Written and committed **before** any backtest code was run. The git history of
this file is the evidence. Rules are not to be changed after results are seen;
any later change must be listed in `REPORT.md` as a deviation.

## Mandate

A concentrated, high-beta book of nine stocks (weights roughly
20/19/19/13/11/10/4/2/1 %) must be fully in cash within 36 months. Account is
tax-free (TFSA), so tax is zero; costs are commission plus a possible 1.5%
currency fee on USD names. Success is judged by the **bad tail of the 36-month
outcome** (5th percentile and worst), with median return second.

## Common mechanics

- Window: 756 trading days. Review every 21 trading days ("monthly review").
  A decision made on a review day's close is executed at the **next** day's
  close. On day 756 everything left is sold.
- Sales proceeds earn the 3-month T-bill rate (FRED `DTB3`).
- Cost per trade value: low = 0.1%, high = 1.6% (0.1% + 1.5% FX). Both reported.
- Tax: 0 (TFSA).
- sigma = annualised stdev of daily log returns over the trailing 252 days.

## Baselines

- **B1 Hold**: sell everything on day 756.
- **B2 Installments**: sell 1/36 of the initial shares at each review.

## Ideas

Textbook ideas are marked (T), my own constructions (O). Parameter in **bold**
is the pre-registered setting; the bracketed list is the perturbation set.

### T1 — Single-stock trend rule (T)
- Why: trend persistence; the other side is the anchored holder who averages down.
- Rule: at each review, if close < **200**-day SMA, sell the whole position; if
  out and close > SMA, rebuy with that stock's proceeds. [100, 150, 250, 300]
- Fails when: sideways, gappy stocks (whipsaw); costs are high (1.6% each way).

### T2 — Drawdown budget, sell-only TIPP (T)
- Why: client has a 30% drawdown limit; forces selling as the cushion shrinks.
  Other side: nobody in particular; this is insurance paid for in whipsaw.
- Rule: floor F = **0.70** x highest portfolio value so far. At each review,
  cushion C = (V - F)/V, allowed equity share E = min(1, 4C). If the equity
  share exceeds E, sell down to E, most volatile names first. Never rebuy.
  [0.60, 0.65, 0.75, 0.80]
- Fails when: V-shaped falls (sells the low, never rebuys).

### T3 — Volatility-ordered liquidation (T)
- Why: volatility clusters and the most volatile names carry the ruin risk.
- Rule: rank names by sigma at the start (0 = most volatile, n-1 = least).
  Name j is sold in equal monthly lots over **L = 12** reviews, starting at
  review 1 + (36 - L) * j/(n-1) (rounded). [6, 9, 18, 24]
- Fails when: the most volatile names are the ones that go on to multiply.

### O1 — Residual-trend exit: "fire the stock, not the market" (O)
- Why: the client rebuys equities after the exit, so a market-wide fall is
  largely hedged; a stock-specific collapse is not. Sell only on
  stock-specific weakness. Other side: panic sellers who dump on market beta,
  and dip buyers who treat a company-specific decline as a market one.
  Stock-specific return is known to trend more cleanly than raw return.
- Rule: beta = trailing 252-day OLS beta to the index, lagged one day.
  Residual log return e = r - beta * r_index; X = cumulative sum of e.
  At a review, if X < its **200**-day SMA **and** X is lower than it was
  **100** days ago (half the SMA length), sell the whole position. Never
  rebuy. [SMA 100, 150, 250, 300; second leg always half]
- Fails when: residual weakness mean-reverts (oversold bounces); in a pure
  market crash it deliberately does nothing, so absolute drawdown is large.

### O2 — Deadline-scaled ratchet stop (O)
- Why: how much drawdown you can tolerate depends on how much time is left to
  recover. A fixed stop ignores the deadline. Other side: holders with no
  deadline, who can rationally wait. The stop tightens to zero at the deadline,
  so it becomes its own glide path.
- Rule: H = highest close since the window start; tau = years remaining.
  At a review, sell the whole position if
  close < H * exp(-**k** * sigma * sqrt(tau)), k = **1.0**. Never rebuy.
  [0.5, 0.75, 1.25, 1.5]
- Fails when: stocks dip and recover late in the window; in steady declines
  that never breach a wide early stop.

### O3 — Strength-harvest installments (O)
- Why: a forced seller should sell to buyers who are eager. Sell more when the
  stock is near its 12-month high, nothing when near its low. Other side:
  momentum chasers at highs.
- Rule: lot = initial shares / 36. pr = (close - 252d low)/(252d high - 252d
  low). At each review sell **2** lots if pr >= **0.8**, 0 lots if
  pr <= **0.2**, else 1 lot. Catch-up: holdings may not exceed
  initial shares x (36 - review number)/**12**.
  [thresholds 0.9/0.1; thresholds 0.7/0.3; 3 lots at strength; catch-up 18]
- Fails when: momentum dominates. It keeps losers and sells winners early. I
  expect a worse bad tail than B2; included as a deliberate test of the
  contrarian instinct.

### O4 — Credit canary on fragile names (O)
- Why: the weakest names here live on equity issuance (ATMs, converts).
  Credit markets price the closing of that window before equity does.
  Other side: equity holders who do not watch credit.
- Rule: spread = Moody's Baa yield minus 10-year Treasury (FRED `BAA10Y`).
  At a review, if the spread has risen by >= **0.50** points over the last 63
  trading days, sell entirely the most volatile half (rounded up) of the names
  still held. Never rebuy. [0.25, 0.375, 0.75, 1.00]
- Fails when: credit widens late (2020: sells the low); idiosyncratic
  collapses in calm credit markets, which it cannot see.

### O5 — Gap-and-fail (O)
- Why: after a bad-news gap, prices keep drifting (under-reaction). A gap that
  cannot retrace half its size in a month is being confirmed by informed
  sellers. Other side: dip buyers anchored on the pre-gap price.
- Rule: event = one-day log return < -3 x trailing 60-day daily stdev (lagged)
  **and** simple return <= -8%. Let P_pre be the prior close, P_gap the event
  close. **20** trading days later, if close < P_gap + **0.5** x (P_pre -
  P_gap), sell the whole position at the next close. Never rebuy. Events in
  the 20 days before the window start count. [wait 10, 40; retrace 0.25, 0.75]
- Fails when: gaps are over-reactions that recover after day 20; slow declines
  with no gap.

## Test plan

Data: Yahoo Finance daily adjusted closes; FRED for T-bills and Baa spread.

1. **Random books, random start dates.** Universe: a seeded random sample of
   current S&P 500/400/600 members. For each trial pick a start date, take
   stocks with at least 300 days of history, keep the more volatile half,
   draw nine at random, assign the mandate's weights at random.
   Universe is split in two halves (A and B) by ticker hash.
2. **Design period**: windows ending on or before 10 Nov 2023.
   **Holdout**: no data after 10 Nov 2023 is loaded until every design-period
   result is saved. Final check = windows that end inside the holdout, plus
   the client's actual nine names from Nov 2023 to Nov 2026.
3. **Worst windows**: starts at Jan 2000, Mar 2000, Oct 2007 (design) and
   Dec 2021 (holdout).
4. **Out-of-universe**: the same rules, unchanged, on non-US stocks
   (Canada, Germany, UK, Japan) with their local index.
5. **Shuffled paths (placebo)**: permute each window's daily returns in time
   (same permutation for all stocks, so cross-section survives, all trend
   and gap-drift structure dies). A rule that still beats B2 here is only
   lowering exposure, not reading a signal.
6. **Block bootstrap**: resample 63-day blocks of the joint return panel.
7. **Parameter perturbation**: the four perturbations listed per idea.
8. **Injected ruin (survivorship correction)**: Yahoo has almost no delisted
   stocks, which flatters B1. In each trial one random name is replaced by a
   synthetic failure: from a random day, it loses 90% over 250 trading days
   with its own historical noise, half the trials as a slow bleed, half
   including a single -50% gap.

## Decision rule (fixed in advance)

Compare terminal 36-month return distributions against B2 at high cost.
An idea **survives** only if, in each of design-A, design-B, non-US and
holdout, and for at least 4 of its 5 parameter settings in design, either

- (a) 5th percentile >= B2's 5th percentile - 2 points **and** median >= B2's
  median + 3 points, or
- (b) 5th percentile >= B2's 5th percentile + 5 points **and** median >= B2's
  median - 2 points.

Against B1 it must also improve the 5th percentile. Total variants tried will
be counted and reported: 8 ideas x 5 settings = 40, plus two baselines.
