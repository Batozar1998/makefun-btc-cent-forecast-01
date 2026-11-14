#!/usr/bin/env python3
"""btc-cent-forecast-01: Bitcoin's price 4 hours ahead.

Method
------
For each case we get 72 hours of 1-minute closes ending at the checkpoint.
The forecast is the checkpoint close plus the median 240-minute price
change observed over the last 48 hours of the case:

    forecast = last_close + median(close[i] - close[i - 240])
               for i over the final 48 hours of the series, where both
               ends of each 240-minute change lie inside those 48 hours
               (so the changes run from 44 hours before the checkpoint
               to the checkpoint itself)

Why the median of 240-minute changes: under absolute-error scoring the
best single guess is the median of where the price could land, and the
240-minute change is exactly the move we are trying to predict, measured
on the same horizon. Taking the median over two days of such moves gives
a robust middle estimate that ignores the occasional one-minute spike
from a large trade in the underlying pool. The median change is clipped
to +/- $200 so a wild stretch of history can never throw the guess far
from the checkpoint price, and the result is rounded to the price grid's
5 decimals.

If a case ever arrived too short for a 240-minute lookback, the forecast
falls back to persistence (the last close) rather than guessing blind.

I/O (per the kit's RULES.txt): read every ``*.in`` file in
$MAKEFUN_INPUT_DIR (default /input), write one ``<id>.out`` per case to
$MAKEFUN_OUTPUT_DIR (default /output) holding exactly
``{"forecasts": [{"case": "<id>", "price": <number>]}``. Standard library
only, no network, deterministic: the same case always gives the same
bytes, well inside the 8-second cap (a few thousand subtractions and a
sort per case).
"""

import json
import os
import statistics
from pathlib import Path

HORIZON_MINUTES = 240          # forecast horizon: 4 hours
WINDOW_MINUTES = 48 * 60       # look back over the last 48 hours
MAX_DRIFT = 200.0              # clip the median 240-minute change to +/- $200
GRID_DECIMALS = 5              # the price grid's 5 decimals of a dollar
MIN_PRICE = 0.00001            # scorer bounds: price must be in (0, 10_000_000)
MAX_PRICE = 9_999_999.99999

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def snap_to_grid(price: float) -> float:
    """Keep a price on the 5-decimal grid and inside the scorer's bounds."""
    clipped = min(MAX_PRICE, max(MIN_PRICE, price))
    return round(clipped, GRID_DECIMALS)


def forecast_case(prices):
    """Forecast the close 240 minutes after the last price in ``prices``."""
    if not prices:
        raise ValueError("case holds no prices")
    last = prices[-1]
    if not isinstance(last, (int, float)) or last != last:  # NaN guard
        raise ValueError("last price is not a finite number")

    # Not enough history for even one 240-minute change: stay put.
    if len(prices) <= HORIZON_MINUTES:
        return snap_to_grid(last)

    # The final 48 hours of the series, and the 240-minute changes fully
    # inside them: each change's earlier end is at least 240 minutes
    # after the window opens, so no change reaches back before it.
    window_start = max(0, len(prices) - WINDOW_MINUTES)
    start = window_start + HORIZON_MINUTES
    if start >= len(prices):
        return snap_to_grid(last)
    changes = [prices[i] - prices[i - HORIZON_MINUTES]
               for i in range(start, len(prices))]
    if not changes:
        return snap_to_grid(last)

    drift = statistics.median(changes)
    drift = max(-MAX_DRIFT, min(MAX_DRIFT, drift))
    return snap_to_grid(last + drift)


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    case_files = sorted(in_dir.glob("*.in"))
    for case_file in case_files:
        case_id = case_file.name[: -len(".in")]
        with case_file.open("r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{case_file.name} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or not prices:
            raise ValueError(f"{case_file.name} holds no prices")

        guess = forecast_case(prices)
        payload = {"forecasts": [{"case": case_id, "price": guess}]}
        out_path = out_dir / f"{case_id}.out"
        with out_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload) + "\n")


if __name__ == "__main__":
    main()
