# Pre-registered tests, round 2 (workstreams B, C, D, E)

Written and committed before any of the new data was downloaded or analysed.
Each workstream has one question, a fixed list of variants and a stop rule.
Anything that fails is dropped, not re-tuned.

## Data

- Prices: Yahoo Finance daily closes (split-adjusted) and adjusted closes, plus split events.
- Earnings history: Yahoo Finance (via the `yfinance` package): for each past
  report, the date and time, the consensus EPS estimate and the reported EPS.
  This is the consensus as it stood at the report, not its revision path.
- Fundamentals: SEC EDGAR XBRL company facts, first-filed values, ~2010 on.
- Universe U1: the 411-stock sample of S&P 500/400/600 members used so far.
- Universe U2 (workstream C): a seeded random sample of 400 US-domiciled
  common stocks from the Nasdaq screener list with market value above
  USD 300M that are not in U1. Sector labels for all stocks come from that
  same list.
- Survivorship: both universes are today's listings. Failed companies are
  missing, more so in U2. Absolute "buy the dip" returns are flattered;
  pass-versus-fail comparisons less so.

## Common definitions

- **Down event**: month-end close >= 30% below the 252-day high and below the
  200-day average; first month only, then none for that stock for 12 months.
- **Reaction day** of a report: the same trading day if the report time is
  before 16:00 New York, else the next trading day. Reaction = that day's
  close-to-close return.
- **Outcome**: return over the next 252 trading days minus the S&P 500;
  24-month figure also reported.
- **Design** = events to 31 Oct 2022; **holdout** = events after.
- **A test works only if** pass beats fail on median 12-month excess return
  by >= 3 points, the month-cluster bootstrap 90% interval excludes zero in
  design, and the sign holds in the holdout.

## B. Buy-tests 1 and 3 with earnings data (U1 and U1+U2)

- **T1b, met expectations**: at the latest report before the event, reported
  EPS >= consensus.
- **T1c, growth expected**: at that report, consensus EPS >= reported EPS of
  the same quarter one year earlier.
- **T1d, forward growth expected (look-ahead, upper bound)**: consensus for
  the first report *after* the event >= reported EPS of the same quarter a
  year earlier. This uses revisions made after the event date, so it
  overstates what was knowable. If even this shows no edge, test 1 is dead on
  this data; if it shows an edge, it is suggestive only.
- **T3b, no company-specific earnings shock**: fails if any reaction in the
  last 126 trading days was <= -8% and sector peers are not down (median peer
  126-day return > -10%). Otherwise passes.
- **T3c**: fails if any reaction in the last 126 days was <= -8%, regardless
  of peers.
- Hypotheses: each "pass" group beats its "fail" group. I expect T3b/T3c to
  help (post-announcement drift) and T1b/T1c to be weak.
- Variants: 5 tests x 2 universes = 10. Stop: no re-definitions.

## C. Buy-test 2 on a wider universe (U1+U2)

- **T2, profitable or funded**: TTM net income > 0, or operating cash flow
  >= 0, or cash plus short-term investments >= 2 x TTM operating cash burn.
- **T2p, profitable only**: TTM net income > 0.
- Hypothesis: pass beats fail, mainly through a better bad tail (worst 5%,
  share losing more than half).
- Variants: 2 tests, funding multiple 1x and 3x for T2 = 4. Stop: if the
  fail group has fewer than 50 design events, report "not testable".

## D. "Cheap plus improving" and dilution (U1+U2)

- **Cheap**: price-to-sales (market value / TTM revenue) below the stock's own
  median over the previous five years (at least three years of history).
  Market value = split-adjusted close x split-adjusted diluted share count
  from the latest filing.
- **Improving**: TTM revenue >= a year earlier and TTM net margin >= a year
  earlier.
- **Diluting**: split-adjusted diluted share count up more than 10% on a year
  earlier.
- Hypotheses: among down events, cheap-and-improving beats cheap-not-improving
  (D1); non-diluting beats diluting (D2); cheap beats not-cheap (D3). Given
  the first round, I expect D1 to fail.
- Variants: 3 comparisons; one perturbation each (margin-only improving;
  dilution threshold 5% and 20%; P/S below the 25th percentile) = 7. Stop: none
  beyond these.

## E. Entry rules

**E1, half now and half on confirmation (U1, down events).** A unit of money
is committed at the event. Compared, over 504 trading days, with the
undeployed part held in the S&P 500:

- Full: all in the stock at the event.
- Half+report: half at the event; second half the day after the first later
  report where reported EPS >= consensus and the reaction is above -5%.
- Half+trend: second half the day after the first later month-end close above
  the 200-day average.
- Half+either: the client's rule, whichever comes first.
- Half only: never add.

Reported: median, mean, worst 5% of the 24-month return. A rule "works" if it
improves the worst 5% versus Full by >= 3 points without lowering the median
by more than 3 points. Variants: 5.

**E2, deploying new money (index level).** 36 equal monthly contributions
into SPY (from 1993) and QQQ (from 1999), all 36-month windows:

- Immediately each month.
- Wait for a dip: hold cash (T-bill) until the fund closes a month >= 10%
  below its 252-day high, then invest all accumulated cash; anything still in
  cash at month 36 is counted as cash.
- Dip thresholds 5% and 20% as perturbations.

Reported: terminal value per unit contributed (median, worst 5%), and the
share of windows in which waiting wins. Variants: 4 x 2 funds = 8.

## Count

Planned variants this round: 10 + 4 + 7 + 5 + 8 = 34.
