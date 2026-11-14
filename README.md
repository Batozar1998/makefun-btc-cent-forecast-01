# Forecast Bitcoin's price 4 hours ahead — make.fun entry

Bounty: [btc-cent-forecast-01](https://make.fun/bounty/btc-cent-forecast-01)
— "Forecast Bitcoin's price 4 hours ahead, 12 times over 48 hours"
($250, 100 places paid).

## The task

For each of 12 checkpoints (4h apart, 2026-11-15T08:00Z to
2026-11-17T04:00Z), forecast Bitcoin's US-dollar price 240 minutes
(4 hours) after the checkpoint, as a single number. The program runs
once per case in a sandbox with no network, ≤8 seconds, 1 CPU,
1024 MB. It reads `/input/<id>.in` (72h of 1-minute BTC/USDC closes
ending at the checkpoint) and writes `/output/<id>.out`. Scoring is the
mean absolute error in cents (100 × the mean |guess − actual close| in
dollars over the 12 cases); a prize needs a score strictly below the
house persistence baseline, which guesses each checkpoint's own close.

## The approach

`main.py` is a statistical point forecaster — no machine learning, no
network, standard library only:

- **Guess = checkpoint price + recent drift.** For a mean-absolute-error
  score the optimal point forecast is the conditional median of the
  4h-ahead price, and the median 240-minute change is a robust
  (outlier-proof) estimate of where that median sits relative to the
  checkpoint price.
- **Drift = the median of the 240-minute price changes over the last
  48 hours** of the case (2,640 overlapping changes), clipped to
  ±$200. These prices are a near-martingale, so the drift is small,
  but in a trending stretch it is real and the median change captures
  it without letting a few huge jumps set the whole forecast. The clip
  is a guard against an extreme drift estimate.
- The guess is rounded to the price grid's 5 decimals and kept inside
  (0, 10,000,000). If a case has too little history for a 240-minute
  change, it falls back to persistence (the checkpoint price).

## Local practice score

Scored on the 6 practice cases (p00–p05). The answers: p00–p04 are the
next case's last price (exact); p05's is derived from the published
baseline loss (see `TRANSCRIPT.md` for the validation):

| forecaster | mean absolute error |
|---|---|
| house baseline (persistence; published practice: 44521.58 cents) | 44521.58 cents |
| this entry | **43096.92 cents** |

It beats the house baseline on 4 of the 6 practice cases (p00, p01,
p02, p04). (Practice is no guarantee for the final — the final's 12
checkpoints run on new data — but the edge also holds on 41 cases
combined: practice + 18 pre-practice + 17 post-practice checkpoints cut
from Binance US BTCUSDT, 42292 vs 43778 cents. The edge is modest and
regime-dependent: it is slightly worse than persistence on the 18
choppy pre-practice cases, so a flat final window would favour the
baseline.)

## How to run

```sh
python3 main.py
```

Reads `$MAKEFUN_INPUT_DIR` (default `/input`), writes
`$MAKEFUN_OUTPUT_DIR` (default `/output`): one `<id>.out` per `<id>.in`.
Deterministic (no randomness), ~0.01s per case on 1 CPU.

## Files

- `main.py` — the entry program (entrypoint)
- `TRANSCRIPT.md` — the agent session transcript that built it
- `LICENSE` — MIT
