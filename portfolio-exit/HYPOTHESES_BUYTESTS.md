# Pre-registered test of the three buy-tests for "down" stocks

Written and committed before any fundamentals were downloaded or any result seen.

## Question

Among stocks that are down, do the client's three tests pick the ones that go
on to do better? And is buying a down stock that passes better than buying a
strong stock?

## Data and its limits

- Prices: Yahoo Finance daily adjusted closes (same 411-stock US sample).
- Fundamentals: SEC EDGAR XBRL company facts, using each figure's first filing
  date, so only what was public at the time is used. Coverage starts ~2009-10.
- Sector and sub-industry: current GICS labels from Wikipedia.
- **No analyst estimates or guidance history is available for free.** Test 1
  and test 3 are therefore proxies built from reported results and prices.
  This is a weaker test than the client's real rule and is labelled as such.
- Survivorship: today's index members only. Down stocks that later failed are
  missing, which flatters every "buy the dip" result. Comparisons between
  passing and failing down stocks are less affected than absolute returns.

## Definitions (fixed)

**Down event.** At a month-end, the stock closes at least **30%** below its
252-day high and below its 200-day average. Only the first month counts; the
same stock cannot produce another event for 12 months.

**Strong comparison.** At the same month-ends, stocks above their 200-day
average and within 10% of their 252-day high (same 12-month spacing).

Fundamentals are trailing-twelve-month (TTM) figures from the latest quarter
filed on or before the event date.

- **Test 1 (outlook flat or rising, proxy).** TTM revenue >= TTM revenue one
  year earlier, and TTM net income >= TTM net income one year earlier.
- **Test 2 (profitable or funded).** TTM net income > 0, or cash and
  short-term investments >= 2 x TTM operating cash burn (operating cash flow
  if negative; a company with positive operating cash flow passes).
- **Test 3 (not company-specific, proxy).** Fails only if there was a
  one-day drop (<= -8% and below -3 daily standard deviations) in the last 126
  trading days **and** the stock's GICS sector peers in the sample are not
  down (median peer 126-day return > -10%). Otherwise passes.

**Outcomes.** Return over the next 252 and 504 trading days, absolute and
minus the S&P 500 price index. Reported: median, mean, worst 5%, share beating
the index, share losing more than half.

## Hypotheses

- H1: down events passing all three tests beat down events failing at least
  one, on median and on worst-5% 12-month excess return.
- H2: each test separately helps (pass beats fail on median excess return).
- H3: down-and-passing is at least as good as strong (median excess return),
  with a worse bad tail. I expect the tail to be worse.

## Evaluation

- Design sample: events up to 31 Oct 2022 (12-month outcomes end by the
  earlier holdout line). Holdout: events from Nov 2022 to Nov 2025.
- Confidence intervals by bootstrap, resampling whole months (events in the
  same month are not independent).
- Perturbations: drawdown threshold 20% and 40%; test 3 peer threshold -5%
  and -15%; test 2 funding multiple 1x and 3x.
- **A test "works" only if** pass beats fail on median 12-month excess return
  by at least 3 points with a 90% interval excluding zero in design, the sign
  holds in the holdout, and it holds in at least 4 of 5 perturbation settings.
  Variants tried will be counted.
