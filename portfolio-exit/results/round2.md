# Round 2 results

Stocks with prices, filings and a sector label: 787 (408 index members, 379 others). Stocks with earnings history: 785.
Report-time hours (New York) in the earnings data: 6h 14%, 7h 20%, 8h 11%, 9h 2%, 16h 40%, 17h 6%

Down events, index members (U1): design 955 (median 12m vs index +6.1%, worst 5% -48.5%, lost over half 3.5%); holdout 342 (median -6.4%, worst 5% -66.2%, lost over half 3.8%).

Down events, all stocks (U1+U2): design 1830 (median 12m vs index +4.9%, worst 5% -57.4%, lost over half 6.0%); holdout 747 (median -5.9%, worst 5% -70.8%, lost over half 4.8%).

## B. Buy-tests 1 and 3 with earnings data

| Test | Design events pass / fail | Median 12m vs index, pass minus fail (90% interval) | Worst 5% pass / fail | Lost over half pass / fail | Holdout pass minus fail (events) | Verdict |
|---|---|---|---|---|---|---|
| T1b met expectations, U1 | 624 / 315 | +3.5% (-4.2% to +11.2%) | -45.4% / -52.4% | 2.7% / 4.8% | -0.4% (210/129) | fails |
| T1b met expectations, U1+U2 | 1149 / 624 | +2.7% (-3.5% to +8.8%) | -53.0% / -60.1% | 4.7% / 7.4% | -4.6% (450/283) | fails |
| T1c growth expected, U1 | 524 / 389 | -4.2% (-10.6% to +1.0%) | -48.5% / -44.9% | 4.0% / 2.1% | -11.1% (179/156) | fails |
| T1c growth expected, U1+U2 | 973 / 704 | -1.5% (-6.3% to +2.1%) | -52.7% / -55.2% | 5.4% / 4.3% | -5.9% (389/325) | fails |
| T1d forward growth expected (look-ahead), U1 | 408 / 504 | -5.3% (-13.2% to +3.1%) | -46.7% / -51.5% | 2.7% / 4.2% | +0.1% (143/195) | fails |
| T1d forward growth expected (look-ahead), U1+U2 | 768 / 889 | -3.2% (-10.3% to +6.0%) | -53.4% / -58.8% | 5.1% / 5.5% | +1.6% (325/392) | fails |
| T3b no company-specific earnings shock, U1 | 721 / 225 | +6.3% (-1.8% to +12.6%) | -47.6% / -51.7% | 2.9% / 5.3% | +6.9% (204/138) | fails |
| T3b no company-specific earnings shock, U1+U2 | 1333 / 454 | +7.8% (+0.1% to +13.8%) | -53.9% / -59.3% | 4.7% / 8.6% | +0.6% (434/307) | works |
| T3c no earnings-day drop of 8%+, U1 | 656 / 290 | +4.6% (-1.5% to +10.3%) | -47.7% / -50.7% | 2.9% / 4.8% | +3.2% (184/158) | fails |
| T3c no earnings-day drop of 8%+, U1+U2 | 1217 / 570 | +6.1% (+0.1% to +10.6%) | -53.5% / -59.3% | 4.7% / 7.7% | -0.4% (404/337) | fails |

## C. Buy-test 2 on the wider universe (U1+U2)

| Test | Design events pass / fail | Median 12m vs index, pass minus fail (90% interval) | Worst 5% pass / fail | Lost over half pass / fail | Holdout pass minus fail (events) | Verdict |
|---|---|---|---|---|---|---|
| T2 profitable or funded 2x | 1722 / 107 | +13.1% (+0.4% to +22.7%) | -53.8% / -94.7% | 5.3% / 15.0% | -51.8% (698/49) | fails |
| T2 funded 1x | 1771 / 58 | +10.7% (-6.4% to +17.0%) | -55.0% / -94.2% | 5.7% / 12.1% | n/a | fails |
| T2 funded 3x | 1682 / 147 | +12.0% (-5.6% to +18.8%) | -53.5% / -93.1% | 5.3% / 12.9% | -53.6% (683/64) | fails |
| T2p profitable only | 1357 / 473 | +4.6% (-4.3% to +10.0%) | -50.6% / -71.4% | 3.8% / 12.1% | -4.6% (494/253) | fails |

## D. Cheap plus improving, and dilution (U1+U2)

| Test | Design events pass / fail | Median 12m vs index, pass minus fail (90% interval) | Worst 5% pass / fail | Lost over half pass / fail | Holdout pass minus fail (events) | Verdict |
|---|---|---|---|---|---|---|
| D1 among cheap: improving vs not | 347 / 489 | -7.8% (-13.3% to -1.6%) | -48.8% / -48.4% | 3.7% / 2.2% | -9.1% (147/304) | fails |
| D1 variant: margin-only improving | 437 / 399 | -7.4% (-13.2% to -1.4%) | -48.5% / -48.5% | 3.7% / 2.0% | -4.8% (187/264) | fails |
| D1 variant: among bottom-quartile P/S | 254 / 395 | -8.4% (-15.1% to -3.2%) | -48.1% / -48.3% | 2.4% / 2.3% | -11.8% (112/239) | fails |
| D2 not diluting (<=10%) vs diluting | 1353 / 187 | +11.1% (+3.7% to +19.1%) | -51.5% / -65.1% | 4.0% / 10.2% | -12.0% (608/94) | fails |
| D2 variant: threshold 5% | 1258 / 282 | +8.3% (+2.8% to +14.5%) | -51.4% / -57.5% | 3.8% / 8.9% | -4.5% (555/147) | fails |
| D2 variant: threshold 20% | 1455 / 85 | +19.0% (+8.5% to +27.7%) | -52.1% / -76.1% | 4.3% / 12.9% | -20.3% (658/44) | fails |
| D3 cheap vs own history vs not | 839 / 238 | +2.9% (-3.0% to +7.5%) | -48.5% / -46.6% | 2.9% / 4.2% | -3.7% (451/94) | fails |

## E1. Half now, half on confirmation (U1 down events, 24 months, undeployed half in the S&P 500)

| Rule | Design median | Design mean | Design worst 5% | Holdout median | Holdout worst 5% | Verdict vs Full |
|---|---|---|---|---|---|---|
| Full | +44.0% | +68.7% | -44.8% | +25.6% | -49.4% |  |
| Half + report | +41.8% | +63.8% | -41.0% | +31.8% | -44.1% | works |
| Half + trend | +42.2% | +61.8% | -38.6% | +31.2% | -42.5% | works |
| Half + either | +42.2% | +64.9% | -43.6% | +29.5% | -43.5% | fails |
| Half + only | +40.9% | +52.9% | -14.3% | +36.2% | -6.3% | fails |
| Index | +35.6% | +37.1% | +0.6% | +42.8% | +23.5% |  |

Events: design 955, holdout 196. Trading costs ignored.

## E2. Deploying new money: invest each month, or hold cash and wait (36 monthly contributions)

| Fund | Rule | Windows | Median value per 1 contributed | Worst 5% | Windows where waiting beats investing at once | Median share of time in cash |
|---|---|---|---|---|---|---|
| SPY | Invest each month | 359 | 1.20 | 0.80 | | 0% |
| SPY | Wait for 10% below high (pre-registered) | 359 | 1.08 | 0.83 | 30% | 89% |
| SPY | Wait for 5% below high | 359 | 1.16 | 0.80 | 22% | 69% |
| SPY | Wait for 20% below high | 359 | 1.07 | 0.92 | 33% | 100% |
| SPY | Buy on S&P one-day drop of 2%+ (added at client's request, not pre-registered) | 359 | 1.16 | 0.82 | 20% | 76% |
| SPY | Buy on S&P one-day drop of 3%+ (added, not pre-registered) | 359 | 1.15 | 0.86 | 21% | 92% |
| QQQ | Invest each month | 285 | 1.27 | 0.91 | | 0% |
| QQQ | Wait for 10% below high (pre-registered) | 285 | 1.21 | 0.92 | 37% | 86% |
| QQQ | Wait for 5% below high | 285 | 1.23 | 0.91 | 25% | 61% |
| QQQ | Wait for 20% below high | 285 | 1.03 | 0.90 | 18% | 100% |
| QQQ | Buy on S&P one-day drop of 2%+ (added at client's request, not pre-registered) | 285 | 1.22 | 0.92 | 13% | 77% |
| QQQ | Buy on S&P one-day drop of 3%+ (added, not pre-registered) | 285 | 1.19 | 0.99 | 25% | 94% |
