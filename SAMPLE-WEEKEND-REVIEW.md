# KAIRO Performance Intelligence Review

**Period:** 2026-07-24T08:13:03.692146+00:00 to 2026-07-27T08:13:03.692146+00:00
**Generated:** 2026-07-27T08:13:03.695070+00:00

## Executive Summary

KAIRO recorded 31 intelligence cycles with 83.9% completing successfully or with warnings. Research created 247 items and skipped 4355. The platform generated 9 shadow decisions; 4 have a measured one-day outcome, with 100.0% directional success.

## System Health

- Jobs recorded: 31
- Intelligence cycles: 31
- Completion rate: 90.3%
- Successful/warnings/failed/abandoned: 5 / 21 / 2 / 3
- Average completed cycle duration: 19.83 seconds

## Research Activity

- Research runs: 28
- Items created: 247
- Items skipped: 4355
- Failures: 79
- Skip rate: 93.0%
- Articles fetched by intelligence cycles: 48
- Signals stored by intelligence cycles: 33

## Decision Intelligence

- Shadow decisions created: 9
- Eligible decisions: 0
- Opportunities seen: 78
- Decisions skipped by cycles: 69
- Average decision confidence: 88.1%

## Shadow Performance

- Total decisions reported: 12
- Measured 1-day decisions: 4
- Directional success: 100.0%
- Profitable after costs: 75.0%
- Recorded outcomes: 0

## Confidence Calibration

- Average snapshot confidence: 74.3%
- Latest snapshot confidence: 82.0%
- Stale snapshot share: 0.0%

## Insights and Recommendations

- 3 jobs remain RUNNING in the selected period; investigate worker interruptions before judging strategy quality.
- Research skip rate is very high. This may be healthy deduplication, but 30-minute cycles should be compared with hourly cycles for incremental value.
- Research recorded 79 failed items; inspect provider and parsing diagnostics.
- The measured decision sample is still too small for strategy conclusions; use 100-200 matured decisions as the first serious review point.
- Price outcome capture recorded 79 failed or deferred operations; central market-data rate limiting and caching would improve data quality.
