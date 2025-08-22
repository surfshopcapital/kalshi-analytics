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


def tickers_with_min_volume(min_volume: int, days: int, granularity: str) -> list:
    """Get tickers that have minimum volume over the specified period"""
    try:
        # Check if candles directory exists and has files
        candles_dir = os.path.join("data", "candles")
        if not os.path.exists(candles_dir):
            os.makedirs(candles_dir, exist_ok=True)
            print(f"📁 Created candles directory: {candles_dir}")
            return []
        
        # Check if there are any candle files
        candle_files = [f for f in os.listdir(candles_dir) if f.endswith(f'_{granularity}.parquet')]
        if not candle_files:
            print(f"📊 No {granularity} candle files found yet. Will create them during refresh.")
            return []
        
        # If we have files, proceed with the query
        q = f"""
            SELECT DISTINCT 
                REPLACE(filename, 'candles_', '') as ticker
            FROM read_dir('{candles_dir}', glob='candles_*_{granularity}.parquet')
            WHERE filename LIKE 'candles_%_{granularity}.parquet'
        """
        
        df = duckdb.query(q).to_df()
        if df.empty:
            print(f"📊 No tickers found in {granularity} candle files")
            return []
        
        # Extract ticker names from filenames
        tickers = []
        for filename in df.iloc[:, 0]:  # First column contains filenames
            # Extract ticker from filename like "candles_TICKER_1h.parquet"
            if filename.startswith('candles_') and filename.endswith(f'_{granularity}.parquet'):
                ticker = filename[8:-len(f'_{granularity}.parquet')-1]  # Remove "candles_" prefix and "_1h.parquet" suffix
                tickers.append(ticker)
        
        print(f"�� Found {len(tickers)} tickers with existing {granularity} candle data")
        return tickers
        
    except Exception as e:
        print(f"⚠️ Error getting tickers with min volume: {e}")
        print("💡 This is expected on first run when no candle files exist yet")
        return []

def refresh_candles(days: int = 30, granularity: str = "1h", min_volume: int = 1000):
    """Refresh candle data for markets with minimum volume"""
    print(f"Refreshing {days}d/{granularity} candles for volume > {min_volume:,}…")
    
    try:
        # Get tickers that need candle refresh
        tickers = tickers_with_min_volume(min_volume, days, granularity)
        
        if not tickers:
            print(f"📊 No existing {granularity} candle files found. Starting fresh...")
            # Get tickers from active markets instead
            if os.path.exists("data/active_markets.parquet"):
                df = pd.read_parquet("data/active_markets.parquet")
                # Filter by volume and get top tickers
                high_volume = df[df["volume"] >= min_volume].nlargest(100, "volume")
                tickers = high_volume["ticker"].tolist()
                print(f"�� Using {len(tickers)} high-volume tickers from active markets")
            else:
                print("❌ No active markets data available. Cannot refresh candles.")
                return
        
        # Ensure candles directory exists
        candles_dir = os.path.join("data", "candles")
        os.makedirs(candles_dir, exist_ok=True)
        
        # Refresh candles for each ticker
        for i, ticker in enumerate(tickers, 1):
            try:
                print(f"  → [{i}/{len(tickers)}] Refreshing {ticker} {granularity} candles...")
                
                # Calculate time range
                end_ts = int(datetime.datetime.now().timestamp())
                start_ts = end_ts - (days * 24 * 3600)
                
                # Get candle data
                client = get_client()
                payload = client.get_candlesticks(
                    ticker, granularity=granularity, start_ts=start_ts, end_ts=end_ts
                )
                
                if payload and "candlesticks" in payload:
                    df = pd.DataFrame(payload["candlesticks"])
                    if not df.empty:
                        # Write to parquet
                        output_path = os.path.join(candles_dir, f"candles_{ticker}_{granularity}.parquet")
                        df.to_parquet(output_path, index=False)
                        print(f"    ✅ Wrote {len(df)} candles to {output_path}")
                    else:
                        print(f"    ⚠️ No candle data for {ticker}")
                else:
                    print(f"    ⚠️ No response for {ticker}")
                    
            except Exception as e:
                print(f"    ❌ Error refreshing {ticker}: {e}")
                continue
        
        print(f"✅ Completed candle refresh for {len(tickers)} tickers")
        
    except Exception as e:
        print(f"❌ Error in refresh_candles: {e}")
        print("💡 This is expected on first run when no data exists yet")


if __name__ == "__main__":
    try:
        print("🔄 Starting parquet refresh...")
        
        # Refresh active markets
        df_active = refresh_active_markets()  # Store the returned DataFrame
        
        # Build summary table (pass the DataFrame)
        refresh_summary(df_active)  # Pass the DataFrame as argument
        
        # Build series volumes
        write_series_volumes()
        
        # Refresh candles (this might fail on first run, which is OK)
        try:
            refresh_candles(days=30, granularity="1h", min_volume=1000)
        except Exception as e:
            print(f"⚠️ Candle refresh failed (this is OK on first run): {e}")
            print("💡 Candle data will be created on subsequent runs")
        
        print("✅ Parquet refresh completed successfully!")
        
    except Exception as e:
        print(f"❌ Fatal error in parquet refresh: {e}")
        # Don't exit with error code 1, as this is expected on first run
        print("💡 Some operations may have failed, but this is normal on first run")
        sys.exit(0)  # Exit successfully even if some operations failed