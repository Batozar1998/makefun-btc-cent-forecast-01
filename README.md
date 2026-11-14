# btc-cent-forecast-01 — Median 240-minute change, last 48 hours

Forecast Bitcoin's US-dollar price 240 minutes after each checkpoint, from
the 72 hours of 1-minute closes ending at that checkpoint.

## Method

For each case:

1. Take the last 48 hours of closes (2,880 minutes).
2. Compute every 240-minute change fully inside that window —
   `close[i] - close[i-240]`, for each minute `i` from 44 hours before the
   checkpoint up to the checkpoint (2,640 changes).
3. Take the median of those changes, clipped to ±$200.
4. Forecast = checkpoint close + clipped median change, rounded to the
   price grid's 5 decimals.

If a case were ever too short for a 240-minute lookback, the forecast
falls back to persistence (the checkpoint close).

Why this works: under absolute-error scoring the best single guess is the
median of where the price could land, and the 240-minute change is exactly
the move being predicted, measured on the same horizon. The median over two
days of such moves is a robust middle estimate — a single large trade in
the underlying pool can spike one minute's price, but it barely moves a
median of 2,640 changes. The ±$200 clip keeps a wild stretch of history
from throwing the guess far from the checkpoint price.

## Files

- `main.py` — the entry. Python 3.13, standard library only, no network.
  Reads every `*.in` in `$MAKEFUN_INPUT_DIR` (default `/input`), writes one
  `<id>.out` per case to `$MAKEFUN_OUTPUT_DIR` (default `/output`) holding
  exactly `{"forecasts": [{"case": "<id>", "price": <number>}]}`.
- `README.md` — this file.
- `TRANSCRIPT.md` — how this entry was built in this session.
- `LICENSE` — MIT.

## Running it

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Runs in ~0.2 s for all six practice cases; deterministic — two runs write
byte-identical outputs, far inside the 8-second per-case cap.

## Practice score (verified 2026-11-15)

Scored locally against `practice_answers.json` (p00–p04 answers are the
exact next-case checkpoint closes; p05's answer is the Binance BTCUSDT
close at the target minute, a stand-in for the Orca close):

| case | forecast | answer | error (cents) |
|------|----------|--------|---------------|
| p00 | 74754.95438 | 74447.80384 | 30,715.05 |
| p01 | 74350.59291 | 73680.83594 | 66,975.70 |
| p02 | 73528.40680 | 73210.50202 | 31,790.48 |
| p03 | 73010.50202 | 73777.35178 | 76,684.98 |
| p04 | 73638.11993 | 73545.88170 | 9,223.82 |
| p05 | 73432.52807 | 73864.44322 | 43,191.52 |
| **mean** | | | **43,096.92** |

Mean absolute error **43,096.92 cents**, beating the persistence baseline's
44,521.58 cents on the same practice cases. Note p03's median change hit
the −$200 clip, so its forecast is exactly $200 below its checkpoint close.

A practice score is no guide to the final — the final is scored on prices
nobody had seen when entries closed — but the method is horizon-matched
and robust by construction, not fitted to these six cases: the window,
the median, and the clip were fixed before scoring, and no parameter was
tuned against the practice answers.
