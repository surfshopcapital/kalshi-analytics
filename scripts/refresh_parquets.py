#!/usr/bin/env python3
import os
import sys

# ── Stub out Streamlit decorators so utils can import safely ─────
import streamlit as _st
_st.cache_data     = lambda *args, **kwargs: (lambda f: f)
_st.cache_resource = lambda f: f

# ── Add project root to path so we can import utils ─────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

import pandas as pd
import duckdb

from utils import (
    DATA_DIR,
    ACTIVE_MARKETS_PQ,
    SUMMARY_MARKETS_PQ,
    SERIES_VOLUMES_PQ, 
    CANDLES_DIR,
    API_KEY,
    get_client,
    load_series_list,
    compute_group_volumes,
)

# ── Ensure data directories exist ────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CANDLES_DIR, exist_ok=True)

# ── Path for series volumes parquet ─────────────────────────────
SERIES_VOLUMES_PQ = os.path.join(DATA_DIR, "series_volumes.parquet")


def refresh_active_markets(page_size: int = 1000, min_volume: int = 1000) -> pd.DataFrame:
    print(f"Refreshing active markets with volume >= ${min_volume:,}…")
    client = get_client()
    all_markets = []
    cursor = None

    while True:
        resp  = client.get_markets(limit=page_size, status="open", cursor=cursor)
        batch = resp.get("markets", [])
        all_markets.extend(batch)

        cursor = resp.get("cursor")
        print(f"  → Fetched {len(batch)} rows; next cursor = {cursor!r}")
        if not cursor:
            break

    df = pd.DataFrame(all_markets)
    
    # Filter to markets with volume >= min_volume 
    if "volume" in df.columns:
        original_count = len(df)
        df = df[df["volume"] >= min_volume]
        print(f"  → Filtered {original_count} → {len(df)} markets with volume >= ${min_volume:,}")
    
    duckdb.from_df(df).to_parquet(ACTIVE_MARKETS_PQ, compression="snappy")
    print(f"  → Wrote {len(df)} high-volume markets to {ACTIVE_MARKETS_PQ}")
    return df


def refresh_summary(df_active: pd.DataFrame) -> pd.DataFrame:
    print("Building summary table…")
    df = df_active.sort_values("volume", ascending=False)
    df = df.rename(columns={
        "title":         "Title",
        "yes_sub_title": "Yes Subtitle",
        "no_sub_title":  "No Subtitle",
        "yes_ask":       "Yes Ask",
        "no_ask":        "No Ask",
        "last_price":    "Last Price",
        "volume":        "Volume (24h)",
        "close_time":    "Close Time",
    })[[
        "Title", "Yes Subtitle", "No Subtitle",
        "Yes Ask", "No Ask", "Last Price",
        "Volume (24h)", "Close Time"
    ]]

    duckdb.from_df(df).to_parquet(SUMMARY_MARKETS_PQ, compression="snappy")
    print(f"  → Wrote {len(df)} rows to {SUMMARY_MARKETS_PQ}")
    return df


def write_series_volumes() -> pd.DataFrame:
    print("Building series volumes…")
    series_list = load_series_list(API_KEY)
    df_series   = compute_group_volumes(API_KEY, series_list)

    duckdb.from_df(df_series)\
          .to_parquet(SERIES_VOLUMES_PQ, compression="snappy")
    print(f"  → Wrote {len(df_series)} rows to {SERIES_VOLUMES_PQ}")
    return df_series


def tickers_with_min_volume(
    min_volume: int = 1000,
    days: int = 30,
    granularity: str = "1h",
) -> list[str]:
    """
    Return tickers whose cached 30-day volume > min_volume,
    by scanning candlestick Parquets.
    """
    parquet_glob = os.path.join(CANDLES_DIR, f"candles_*_{granularity}.parquet")
    cutoff_ts    = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp())

    q = rf"""
      SELECT
        regexp_extract(filename, 'candles_(.*)_{granularity}\.parquet', 1) AS ticker,
        SUM(volume) AS vol_30d
      FROM read_parquet('{parquet_glob}')
      WHERE end_period_ts >= {cutoff_ts}
      GROUP BY ticker
      HAVING SUM(volume) > {min_volume}
      ORDER BY vol_30d DESC
    """
    df = duckdb.query(q).to_df()
    print(f"→ {len(df)} tickers exceed {min_volume:,} in last {days} days")
    return df["ticker"].tolist()


def refresh_candles(
    days: int = 30,
    granularity: str = "1h",
    min_volume: int = 1000,
):
    """
    Serially fetch and dump candlesticks only for tickers above min_volume.
    """
    print(f"Refreshing {days}d/{granularity} candles for volume > {min_volume:,}…")
    client = get_client()

    # 1) Determine which tickers to fetch
    tickers = tickers_with_min_volume(min_volume, days, granularity)
    if not tickers:
        print("  → No tickers meet the threshold; nothing to do.")
        return

    end_ts   = int(pd.Timestamp.now().timestamp())
    start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp())

    # 2) Loop serially
    for ticker in tickers:
        payload = client.get_candlesticks(
            ticker,
            granularity=granularity,
            start_ts=start_ts,
            end_ts=end_ts,
        )
        df_c = pd.DataFrame(payload.get("candlesticks", []))
        if df_c.empty:
            print(f"  → No data for {ticker}; skipped.")
            continue

        path = os.path.join(CANDLES_DIR, f"candles_{ticker}_{granularity}.parquet")
        duckdb.from_df(df_c).to_parquet(path, compression="snappy")
        print(f"  → Wrote {len(df_c)} rows for {ticker}")

    print("Candles refresh complete.")


if __name__ == "__main__":
    # Only process markets with volume >= $1000
    df_active  = refresh_active_markets(min_volume=1000)
    df_summary = refresh_summary(df_active)
    write_series_volumes()
    refresh_candles(days=30, granularity="1h", min_volume=1000)
    print("All refresh steps complete.")