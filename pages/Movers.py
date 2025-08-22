# pages/Movers.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
# Import helper to fix path issues
import import_helper

from utils import (
    load_active_markets_from_store,
    get_events_to_series_mapping,
    get_volume_columns,
    load_candles_from_store,
    API_KEY,
    make_ticker_clickable,
    make_title_clickable,
    ACTIVE_MARKETS_PQ,
)
from kalshi_client import KalshiClient
import duckdb
import os

def check_parquet_data_freshness() -> tuple[bool, str]:
    """
    Check if Parquet data is fresh enough to use instead of live API calls.
    Returns (is_fresh, reason) tuple.
    """
    try:
        # Check the actual parquet file timestamp instead of changelog
        parquet_path = ACTIVE_MARKETS_PQ
        if not os.path.exists(parquet_path):
            return False, f"Active markets parquet not found: {parquet_path}"
        
        # Get the file's last modified time
        file_stat = os.stat(parquet_path)
        last_refresh_dt = pd.Timestamp.fromtimestamp(file_stat.st_mtime)
        now = pd.Timestamp.now()
        
        # Check if data is less than 30 minutes old
        age_minutes = (now - last_refresh_dt).total_seconds() / 60
        
        if age_minutes < 30:
            return True, f"Data is {age_minutes:.1f} minutes old - fresh enough"
        else:
            return False, f"Data is {age_minutes:.1f} minutes old - too stale"
            
    except Exception as e:
        return False, f"Error checking freshness: {e}"

def get_live_market_data(tickers: list) -> pd.DataFrame:
    """
    Fetch live market data from Kalshi API to get current yes_bid prices.
    This fixes the stale data issue by getting real-time prices.
    """
    try:
        client = KalshiClient(api_key=API_KEY)
        live_data = []
        
        # Add progress bar for live data fetching
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Fetch markets in batches to avoid overwhelming the API
        batch_size = 50
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i:i + batch_size]
            
            for ticker in batch_tickers:
                try:
                    status_text.text(f"Fetching live data for {ticker}... ({len(live_data)+1}/{len(tickers)})")
                    
                    # Get individual market data
                    resp = client.get_market(ticker)
                    if resp and "market" in resp:
                        market = resp["market"]
                        live_data.append({
                            "ticker": ticker,
                            "yes_bid": market.get("yes_bid"),
                            "yes_ask": market.get("yes_ask"),
                            "last_price": market.get("last_price"),
                            "volume": market.get("volume", 0),
                            "open_interest": market.get("open_interest", 0),
                            "status": market.get("status"),
                            "close_time": market.get("close_time")
                        })
                    
                    progress_bar.progress((len(live_data)) / len(tickers))
                    
                except Exception as e:
                    st.warning(f"Could not fetch live data for {ticker}: {str(e)}")
                    continue
        
        progress_bar.empty()
        status_text.empty()
        
        return pd.DataFrame(live_data)
    except Exception as e:
        st.error(f"Error fetching live market data: {str(e)}")
        return pd.DataFrame()

def get_7d_ago_price_optimized(ticker: str, hours_to_close: float) -> float:
    """
    Optimized version: fetch minimal data needed for 7 days ago price using duckdb efficiently.
    """
    try:
        # Check if candle file exists
        candle_path = os.path.join("data", "candles", f"candles_{ticker}_1h.parquet")
        if not os.path.exists(candle_path):
            return np.nan
            
        # If market closes soon, we don't need much historical data
        if hours_to_close < 168:  # Market closes within 7 days
            # Just fetch 2-3 hours around the 7d mark
            now = datetime.now()
            target_time = now - timedelta(days=7)
            start_ts = int((target_time - timedelta(hours=1)).timestamp())
            end_ts = int((target_time + timedelta(hours=1)).timestamp())
        else:
            # Market has time - fetch 24 hours around the 7d mark
            now = datetime.now()
            target_time = now - timedelta(days=7)
            start_ts = int((target_time - timedelta(hours=12)).timestamp())
            end_ts = int((target_time + timedelta(hours=12)).timestamp())
        
        # Use duckdb to efficiently query the parquet files
        query = f"""
        SELECT yes_bid, end_period_ts
        FROM read_parquet('{candle_path}')
        WHERE end_period_ts BETWEEN {start_ts} AND {end_ts}
        ORDER BY ABS(end_period_ts - {int(target_time.timestamp())})
        LIMIT 1
        """
        
        result = duckdb.query(query).fetchone()
        if result and result[0] is not None:
            return float(result[0])
        
        return np.nan
        
    except Exception as e:
        return np.nan

def get_24h_ago_price_optimized(ticker: str, hours_to_close: float) -> float:
    """
    Optimized version: fetch minimal data needed for 24h ago price using duckdb efficiently.
    """
    try:
        # Check if candle file exists
        candle_path = os.path.join("data", "candles", f"candles_{ticker}_1h.parquet")
        if not os.path.exists(candle_path):
            return np.nan
            
        # If market closes soon, we don't need much historical data
        if hours_to_close < 24:  # Market closes within 24 hours
            # Just fetch 1 hour around the 24h mark
            now = datetime.now()
            target_time = now - timedelta(hours=24)
            start_ts = int((target_time - timedelta(minutes=30)).timestamp())
            end_ts = int((target_time + timedelta(minutes=30)).timestamp())
        else:
            # Market has time - fetch 2 hours around the 24h mark
            now = datetime.now()
            target_time = now - timedelta(hours=24)
            start_ts = int((target_time - timedelta(hours=1)).timestamp())
            end_ts = int((target_time + timedelta(hours=1)).timestamp())
        
        # Use duckdb to efficiently query the parquet files
        query = f"""
        SELECT yes_bid, end_period_ts
        FROM read_parquet('{candle_path}')
        WHERE end_period_ts BETWEEN {start_ts} AND {end_ts}
        ORDER BY ABS(end_period_ts - {int(target_time.timestamp())})
        LIMIT 1
        """
        
        result = duckdb.query(query).fetchone()
        if result and result[0] is not None:
            return float(result[0])
        
        return np.nan
        
    except Exception as e:
        return np.nan

def calculate_moves_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 24h and 7d moves for all markets in the dataframe.
    Uses optimized historical data fetching.
    """
    try:
        # Parse close times and calculate hours to close
        def parse_close_time(close_time):
            try:
                if pd.isna(close_time):
                    return np.nan
                if isinstance(close_time, str):
                    # Parse ISO format string
                    dt = pd.to_datetime(close_time)
                else:
                    dt = close_time
                now = pd.Timestamp.now()
                hours_to_close = (dt - now).total_seconds() / 3600
                return max(0, hours_to_close)
            except:
                return np.nan
        
        # Ensure hours_to_close is calculated (data should already be pre-filtered)
        df = df.copy()
        if "hours_to_close" not in df.columns:
            df["hours_to_close"] = df["close_time"].apply(parse_close_time)
        
        # Get list of tickers for batch processing
        tickers = df["ticker"].tolist()
        
        # Calculate moves for each market
        moves_data = []
        
        # Add progress indicator (only if in Streamlit context)
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            in_streamlit = True
        except:
            progress_bar = None
            status_text = None
            in_streamlit = False
        
        for i, ticker in enumerate(tickers):
            try:
                if in_streamlit and status_text:
                    status_text.text(f"Calculating moves for {ticker}... ({i+1}/{len(tickers)})")
                
                # Get current values for this ticker
                row_now = df[df["ticker"] == ticker].iloc[0]
                current_yes_bid = row_now.get("yes_bid")
                if pd.isna(current_yes_bid) or current_yes_bid == 0:
                    current_yes_bid = row_now.get("last_price")
                # If still missing, skip this ticker
                if pd.isna(current_yes_bid) or current_yes_bid == 0:
                    continue
                
                # Get hours to close for this market
                hours_to_close = df[df["ticker"] == ticker]["hours_to_close"].iloc[0]
                
                # Get 24h ago price
                yes_bid_24h_ago = get_24h_ago_price_optimized(ticker, hours_to_close)
                if pd.isna(yes_bid_24h_ago):
                    # Fallback: use previous_yes_bid from market data, or assume 0 move
                    previous_bid = row_now.get("previous_yes_bid", 0)
                    if pd.notna(previous_bid) and previous_bid > 0:
                        yes_bid_24h_ago = previous_bid
                    else:
                        # Assume 0 move if no historical data found
                        yes_bid_24h_ago = current_yes_bid
                
                # Get 7d ago price (only if market has enough time)
                yes_bid_7d_ago = None
                if hours_to_close >= 168:  # At least 7 days to close
                    yes_bid_7d_ago = get_7d_ago_price_optimized(ticker, hours_to_close)
                
                # Calculate moves
                if pd.notna(yes_bid_24h_ago) and yes_bid_24h_ago > 0:
                    notional_move_24h = current_yes_bid - yes_bid_24h_ago
                    percent_move_24h = (notional_move_24h / yes_bid_24h_ago) * 100
                else:
                    # If we can't get historical data, use a simple fallback
                    # Show as 0 move rather than excluding the market entirely
                    notional_move_24h = 0
                    percent_move_24h = 0
                
                if pd.notna(yes_bid_7d_ago) and yes_bid_7d_ago > 0:
                    notional_move_7d = current_yes_bid - yes_bid_7d_ago
                    percent_move_7d = (notional_move_7d / yes_bid_7d_ago) * 100
                else:
                    # No 7d data available - show as N/A
                    notional_move_7d = np.nan
                    percent_move_7d = np.nan
                
                # Determine volume fields for display
                vol_24h_val = row_now.get("volume_24h") if "volume_24h" in row_now.index else None
                if pd.isna(vol_24h_val) or vol_24h_val is None:
                    vol_24h_val = row_now.get("volume")
                total_vol_val = row_now.get("volume")

                # Store the data
                moves_data.append({
                    "ticker": ticker,
                    "title": df[df["ticker"] == ticker]["title"].iloc[0],
                    "yes_bid": current_yes_bid,
                    "yes_bid_24h_ago": yes_bid_24h_ago,
                    "yes_bid_7d_ago": yes_bid_7d_ago,
                    "notional_move_24h": notional_move_24h,
                    "percent_move_24h": percent_move_24h,
                    "notional_move_7d": notional_move_7d,
                    "percent_move_7d": percent_move_7d,
                    "hours_to_close": hours_to_close,
                    "abs_notional_move_24h": abs(notional_move_24h) if pd.notna(notional_move_24h) else 0,
                    "volume_24h": vol_24h_val,
                    "total_volume": total_vol_val,
                })
                
                if in_streamlit and progress_bar:
                    progress_bar.progress((i + 1) / len(tickers))
                
            except Exception as e:
                if in_streamlit:
                    st.warning(f"Error calculating moves for {ticker}: {str(e)}")
                else:
                    print(f"Warning: Error calculating moves for {ticker}: {str(e)}")
                continue
        
        # Clear progress indicators (only if in Streamlit context)
        if in_streamlit and progress_bar:
            progress_bar.empty()
        if in_streamlit and status_text:
            status_text.empty()
        
        if not moves_data:
            return pd.DataFrame()
        
        # Convert to DataFrame and sort by absolute notional move
        moves_df = pd.DataFrame(moves_data)
        moves_df = moves_df.sort_values("abs_notional_move_24h", ascending=False)
        
        return moves_df
        
    except Exception as e:
        st.error(f"Error calculating moves: {str(e)}")
        return pd.DataFrame()

def filter_by_time_to_close(df: pd.DataFrame, min_hours_to_close: int) -> pd.DataFrame:
    """
    Filter markets by minimum time to close.
    """
    try:
        def parse_close_time(close_time):
            """Robustly parse Kalshi close_time values to hours from now.
            Handles ISO strings, pandas Timestamps, and epoch seconds/milliseconds.
            """
            try:
                if pd.isna(close_time):
                    return np.nan
                # Epoch seconds/milliseconds
                if isinstance(close_time, (int, float)) or (isinstance(close_time, str) and close_time.isdigit()):
                    ts = int(float(close_time))
                    # Detect ms vs s by magnitude (>= 10^12 → ms)
                    if ts >= 10**12:
                        dt = pd.to_datetime(ts, unit="ms", utc=True).tz_convert(None)
                    else:
                        dt = pd.to_datetime(ts, unit="s", utc=True).tz_convert(None)
                # String timestamp (ISO)
                elif isinstance(close_time, str):
                    dt = pd.to_datetime(close_time, utc=True, errors="coerce")
                    if pd.isna(dt):
                        return np.nan
                    dt = dt.tz_convert(None)
                # Already datetime-like
                else:
                    dt = pd.to_datetime(close_time, utc=True).tz_convert(None)
                now = pd.Timestamp.utcnow().tz_localize(None)
                hours_to_close = (dt - now).total_seconds() / 3600.0
                return max(0.0, hours_to_close)
            except Exception:
                return np.nan
        
        df = df.copy()
        df["hours_to_close"] = df.get("close_time", pd.Series(np.nan, index=df.index)).apply(parse_close_time)
        return df[df["hours_to_close"] >= min_hours_to_close]
        
    except Exception as e:
        st.error(f"Error filtering by time to close: {str(e)}")
        return df

def filter_by_expiration_time(df: pd.DataFrame, min_hours_to_expiration: int) -> pd.DataFrame:
    """
    Filter markets by minimum time until expiration (actual resolution).
    This is more accurate than close_time for filtering out sports games.
    """
    try:
        def parse_expiration_time(expiration_time):
            """Parse expiration_time to hours from now - similar to close_time parsing"""
            try:
                if pd.isna(expiration_time):
                    return np.nan
                # Handle different timestamp formats like in parse_close_time
                if isinstance(expiration_time, (int, float)) or (isinstance(expiration_time, str) and expiration_time.isdigit()):
                    ts = int(float(expiration_time))
                    if ts >= 10**12:
                        dt = pd.to_datetime(ts, unit="ms", utc=True).tz_convert(None)
                    else:
                        dt = pd.to_datetime(ts, unit="s", utc=True).tz_convert(None)
                elif isinstance(expiration_time, str):
                    dt = pd.to_datetime(expiration_time, utc=True, errors="coerce")
                    if pd.isna(dt):
                        return np.nan
                    dt = dt.tz_convert(None)
                else:
                    dt = pd.to_datetime(expiration_time, utc=True).tz_convert(None)
                
                now = pd.Timestamp.utcnow().tz_localize(None)
                hours_to_expiration = (dt - now).total_seconds() / 3600.0
                return max(0.0, hours_to_expiration)
            except Exception:
                return np.nan
        
        df = df.copy()
        df["hours_to_expiration"] = df.get("expiration_time", pd.Series(np.nan, index=df.index)).apply(parse_expiration_time)
        return df[df["hours_to_expiration"] >= min_hours_to_expiration]
        
    except Exception as e:
        st.error(f"Error filtering by expiration time: {str(e)}")
        return df

def main():
    st.set_page_config(page_title="Market Movers", layout="wide")
    st.title("📈 Market Movers")
    
    st.markdown("""
    This page shows the biggest 24-hour and 7-day price movers among active Kalshi events.
    Markets are filtered by minimum volume, time to expiration, and time to close, then sorted by largest notional move (absolute price change).
    
    **Move Definition**: Absolute price change determined by Yes bid price over 24 hours and 7 days.
    **Data Source**: Live market data from Kalshi API (not stale cached data).
    **New Filter**: "Days to Expiration" filters out sports games that resolve tonight but have distant close times.
    """)
    
    # ── Configuration ───────────────────────────────────────────────────────
    st.subheader("⚙️ Configuration")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        min_volume = st.number_input(
            "Minimum 24h Volume ($)",
            min_value=500,
            value=2000,
            step=500,
            help="Only show markets with at least this much 24h volume"
        )
    
    with col2:
        min_days_to_expiration = st.number_input(
            "Minimum Days to Expiration",
            min_value=0.1,
            value=1.0,
            step=0.1,
            help="Minimum time until market actually resolves (filters out tonight's sports games)"
        )
    
    with col3:
        min_days_to_close = st.number_input(
            "Minimum Days to Close",
            min_value=0.1,
            value=1.0,
            step=0.1,
            help="Minimum time remaining until market trading ends"
        )
    
    with col4:
        max_days_to_close = st.number_input(
            "Maximum Days to Close",
            min_value=1.0,
            value=365.0,
            step=1.0,
            help="Maximum time remaining until market trading ends"
        )
    
    with col5:
        min_days_since_open = st.number_input(
            "Minimum Days Since Open",
            min_value=0.0,
            value=2.0,
            step=0.1,
            help="Only show markets that have been open for at least this many days"
        )
    
    with col6:
        max_rows = st.number_input(
            "Maximum Rows to Display",
            min_value=10,
            value=50,
            step=10,
            help="Maximum number of markets to show in the table"
        )
    
    # ── Load Data ───────────────────────────────────────────────────────────
    with st.spinner("Loading market data..."):
        # Check if Parquet data is fresh enough to use
        is_fresh, freshness_reason = check_parquet_data_freshness()
        
        if is_fresh:

            # Load active markets from cache (fresh data)
            markets_df = load_active_markets_from_store()
            
            if markets_df.empty:
                st.error("Could not load markets data. Please check your API connection.")
                return
            
            # Get volume columns for proper filtering
            vol24_series, total_vol_series = get_volume_columns(markets_df)
            
            # Filter by volume requirement using the actual 24h volume data
            volume_filter = vol24_series >= min_volume
            markets_df = markets_df[volume_filter]
            
            
            if markets_df.empty:
                st.warning(f"No markets meet the volume requirement (≥${min_volume:,}).")
                return
            
            # Filter by days to expiration (NEW - this solves the sports game issue!)
            min_hours_to_expiration = int(min_days_to_expiration * 24)
            markets_df = filter_by_expiration_time(markets_df, min_hours_to_expiration)
            
            if markets_df.empty:
                st.warning(f"No markets meet the expiration time requirement (≥{min_days_to_expiration:.1f} days to expiration).")
                return
            
            # Filter by days to close using separate min/max filters
            min_hours_to_close = int(min_days_to_close * 24)
            max_hours_to_close = int(max_days_to_close * 24)
            
            # Apply min days to close filtering
            markets_df = filter_by_time_to_close(markets_df, min_hours_to_close)
            
            # Add max days filtering
            def parse_close_time_for_max(close_time):
                try:
                    if pd.isna(close_time):
                        return np.nan
                    dt = pd.to_datetime(close_time, utc=True).tz_convert(None)
                    now = pd.Timestamp.now()
                    hours_to_close = (dt - now).total_seconds() / 3600
                    return max(0, hours_to_close)
                except:
                    return np.nan
            
            if "hours_to_close" not in markets_df.columns:
                markets_df["hours_to_close"] = markets_df["close_time"].apply(parse_close_time_for_max)
            
            # Filter by max days as well
            markets_df = markets_df[markets_df["hours_to_close"] <= max_hours_to_close]
            
            if markets_df.empty:
                st.warning(f"No markets meet the days to close requirement ({min_days_to_close:.1f}-{max_days_to_close:.1f} days).")
                return
            
            # Filter by days since open
            def parse_open_time_for_days_since(open_time):
                try:
                    if pd.isna(open_time):
                        return np.nan
                    dt = pd.to_datetime(open_time, utc=True).tz_convert(None)
                    now = pd.Timestamp.now()
                    hours_since_open = (now - dt).total_seconds() / 3600
                    return max(0, hours_since_open / 24)  # Convert to days
                except:
                    return np.nan
            
            markets_df["days_since_open"] = markets_df["open_time"].apply(parse_open_time_for_days_since)
            markets_df = markets_df[markets_df["days_since_open"] >= min_days_since_open]
            
            if markets_df.empty:
                st.warning(f"No markets meet the days since open requirement (≥{min_days_since_open:.1f} days).")
                return
            
            # Use Parquet data directly - no need for live API calls
            
        else:
            st.warning(f"⚠️ Parquet data is stale: {freshness_reason}")
            st.info("🔄 Fetching live market data from Kalshi API...")
            
            # Load active markets from cache first (for initial filtering)
            markets_df = load_active_markets_from_store()
            st.caption(f"Loaded {len(markets_df)} rows from active markets parquet (stale mode)")
            
            if markets_df.empty:
                st.error("Could not load markets data. Please check your API connection.")
                return
            
            # Get volume columns for proper filtering
            vol24_series, total_vol_series = get_volume_columns(markets_df)
            
            # Filter by volume requirement using the actual 24h volume data
            volume_filter = vol24_series >= min_volume
            markets_df = markets_df[volume_filter]
            
            
            if markets_df.empty:
                st.warning(f"No markets meet the volume requirement (≥${min_volume:,}).")
                return
            
            # Filter by days to expiration (same logic as fresh data path)
            min_hours_to_expiration = int(min_days_to_expiration * 24)
            markets_df = filter_by_expiration_time(markets_df, min_hours_to_expiration)
            
            if markets_df.empty:
                st.warning(f"No markets meet the expiration time requirement (≥{min_days_to_expiration:.1f} days to expiration).")
                return
            
            # Filter by days to close using separate min/max filters (same logic as fresh data path)
            min_hours_to_close = int(min_days_to_close * 24)
            max_hours_to_close = int(max_days_to_close * 24)
            
            # Apply min days to close filtering
            markets_df = filter_by_time_to_close(markets_df, min_hours_to_close)
            
            # Add max days filtering
            def parse_close_time_for_max_stale(close_time):
                try:
                    if pd.isna(close_time):
                        return np.nan
                    dt = pd.to_datetime(close_time, utc=True).tz_convert(None)
                    now = pd.Timestamp.now()
                    hours_to_close = (dt - now).total_seconds() / 3600
                    return max(0, hours_to_close)
                except:
                    return np.nan
            
            if "hours_to_close" not in markets_df.columns:
                markets_df["hours_to_close"] = markets_df["close_time"].apply(parse_close_time_for_max_stale)
            
            # Filter by max days as well
            markets_df = markets_df[markets_df["hours_to_close"] <= max_hours_to_close]
            
            if markets_df.empty:
                st.warning(f"No markets meet the days to close requirement ({min_days_to_close:.1f}-{max_days_to_close:.1f} days).")
                return
            
            # Filter by days since open
            def parse_open_time_for_days_since_stale(open_time):
                try:
                    if pd.isna(open_time):
                        return np.nan
                    dt = pd.to_datetime(open_time, utc=True).tz_convert(None)
                    now = pd.Timestamp.now()
                    hours_since_open = (now - dt).total_seconds() / 3600
                    return max(0, hours_since_open / 24)  # Convert to days
                except:
                    return np.nan
            
            markets_df["days_since_open"] = markets_df["open_time"].apply(parse_open_time_for_days_since_stale)
            markets_df = markets_df[markets_df["days_since_open"] >= min_days_since_open]
            
            if markets_df.empty:
                st.warning(f"No markets meet the days since open requirement (≥{min_days_since_open:.1f} days).")
                return
            
            # Get list of tickers for live data fetch
            tickers = markets_df["ticker"].tolist()
            
            # Fetch live market data to get current yes_bid prices
            live_markets_df = get_live_market_data(tickers)
            
            if live_markets_df.empty:
                st.error("Could not fetch live market data. Using cached data instead.")
                # Fall back to cached data
                live_markets_df = markets_df
            
            # Merge live data with cached data
            markets_df = markets_df.merge(
                live_markets_df[["ticker", "yes_bid", "volume", "close_time"]], 
                on="ticker", 
                how="left",
                suffixes=("_cached", "_live")
            )
            
            # Use live yes_bid if available, otherwise fall back to cached
            markets_df["yes_bid"] = markets_df["yes_bid_live"].fillna(markets_df["yes_bid_cached"])
            markets_df["volume"] = markets_df["volume_live"].fillna(markets_df["volume_cached"])
            markets_df["close_time"] = markets_df["close_time_live"].fillna(markets_df["close_time_cached"])
        
        # Calculate moves (optimized version)
        moves_df = calculate_moves_optimized(markets_df)
        
        if moves_df.empty:
            st.warning("No markets have sufficient data for move calculations.")
            return
    
    # ── Display Results ────────────────────────────────────────────────────
    st.subheader(f"📊 Top Movers by Notional Move (showing {min(len(moves_df), max_rows)} of {len(moves_df)} markets)")
    
    # Sort by absolute notional move (largest moves first) - this is the key requirement
    top_movers = moves_df.nlargest(max_rows, "abs_notional_move_24h")
    
    # Get volume columns for display
    vol24_series, total_vol_series = get_volume_columns(top_movers)
    
    # FIXED: Ensure all columns are properly typed and handle missing data
    # Add proper +/- indicators for moves
    def format_move_with_sign(value, prefix="$"):
        if pd.isna(value):
            return "N/A"
        sign = "+" if value > 0 else ""
        return f"{sign}{prefix}{value:,.0f}"
    
    def format_percent_with_sign(value):
        if pd.isna(value):
            return "N/A"
        sign = "+" if value > 0 else ""
        return f"{sign}{value:.1f}%"
    
    # ── Inject inline CSS for compact, sleek table formatting ───────────────
    st.markdown(
        """
        <style>
        .stDataFrame table { border-collapse: collapse !important; }
        .stDataFrame th, .stDataFrame td {
          border: 1px solid #ddd !important;
          padding: 4px 6px !important;
          white-space: nowrap !important;
          font-size: 12px !important;
          line-height: 1.2 !important;
        }
        .stDataFrame th { 
          background-color: #f2f2f2 !important;
          font-weight: bold !important;
        }
        .stDataFrame td {
          vertical-align: top !important;
        }
        /* Ensure titles don't wrap to multiple lines */
        .stDataFrame td:nth-child(3) {
          max-width: 300px !important;
          overflow: hidden !important;
          text-overflow: ellipsis !important;
          white-space: nowrap !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Build one consolidated dataframe for display instead of manual row rendering
    display_df = pd.DataFrame({
        "Rank": range(1, len(top_movers) + 1),
        "Ticker": top_movers["ticker"].astype(str),
        "Title": top_movers["title"].astype(str),
        "Yes Bid": pd.to_numeric(top_movers["yes_bid"], errors="coerce"),
        "Yes Bid (24h Ago)": pd.to_numeric(top_movers["yes_bid_24h_ago"], errors="coerce"),
        "24h Notional Move": pd.to_numeric(top_movers["notional_move_24h"], errors="coerce"),
        "24h % Move": pd.to_numeric(top_movers["percent_move_24h"], errors="coerce"),

        "Volume (24h)": pd.to_numeric(top_movers["volume_24h"], errors="coerce"),
        "Total Volume": pd.to_numeric(top_movers["total_volume"], errors="coerce"),
        "Days to Close": pd.to_numeric(top_movers["hours_to_close"], errors="coerce") / 24,
    })
    
    # Format and display the dataframe
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Yes Bid": st.column_config.NumberColumn("Yes Bid", format="$%.0f"),
            "Yes Bid (24h Ago)": st.column_config.NumberColumn("Yes Bid (24h Ago)", format="$%.0f"),
            "24h Notional Move": st.column_config.NumberColumn("24h Notional Move", format="$%.0f"),
            "24h % Move": st.column_config.NumberColumn("24h % Move", format="%.1f%%"),

            "Volume (24h)": st.column_config.NumberColumn("Volume (24h)", format="$%.0f"),
            "Total Volume": st.column_config.NumberColumn("Total Volume", format="$%.0f"),
            "Days to Close": st.column_config.NumberColumn("Days to Close", format="%.1f"),
        }
    )
    
    st.divider()
    
    # ── New Table: Markets by % Recent Volume ──────────────────────────────
    st.subheader("📈 Markets by % Recent Volume (24h Volume / Total Volume)")
    
    # Calculate % recent volume for all markets that meet the filters
    if not moves_df.empty:
        # Fix total volume calculation - ensure we're using the correct column mapping
        # moves_df should have volume_24h and total_volume from the calculation
        vol_24h = pd.to_numeric(moves_df.get("volume_24h", 0), errors="coerce").fillna(0)
        total_volume = pd.to_numeric(moves_df.get("total_volume", 0), errors="coerce").fillna(0)
        
        # Calculate % recent volume (24h / total)
        percent_recent_volume = np.where(total_volume > 0, (vol_24h / total_volume) * 100, 0)
        
        # Create dataframe for % recent volume table
        volume_df = pd.DataFrame({
            "Ticker": moves_df["ticker"].astype(str),
            "Title": moves_df["title"].astype(str),
            "24h Volume": vol_24h,
            "Total Volume": total_volume,
            "% Recent Volume": percent_recent_volume,
            "Yes Bid": pd.to_numeric(moves_df["yes_bid"], errors="coerce").fillna(0),
            "Days to Close": pd.to_numeric(moves_df.get("hours_to_close", 0), errors="coerce").fillna(0) / 24
        })
        
        # Sort by % recent volume descending
        volume_df = volume_df.sort_values("% Recent Volume", ascending=False)
        
        # Display as proper dataframe
        st.dataframe(
            volume_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "24h Volume": st.column_config.NumberColumn("24h Volume", format="$%.0f"),
                "Total Volume": st.column_config.NumberColumn("Total Volume", format="$%.0f"),
                "% Recent Volume": st.column_config.NumberColumn("% Recent Volume", format="%.1f%%"),
                "Yes Bid": st.column_config.NumberColumn("Yes Bid", format="$%.0f"),
                "Days to Close": st.column_config.NumberColumn("Days to Close", format="%.1f"),
            }
        )
    
    # ── Explanation ─────────────────────────────────────────────────────────
    with st.expander("ℹ️ About This Page", expanded=False):
        st.write("""
        **Purpose**: This page identifies markets with the biggest 24-hour and 7-day price movements based on absolute price change (notional move).
        
        **Data Source**: 
        - **Current Yes Bid**: Live data from Kalshi API (updated in real-time)
        - **Historical Data**: Optimized queries from cached candle data
        
        **Filters Applied**:
        - **Volume**: Only markets with sufficient 24h volume (≥$1,000 minimum enforced)
        - **Time to Close**: Excludes markets closing soon to avoid daily event noise
        
        **Move Calculations**:
        - **24h Notional Move**: Absolute price change in dollars over 24 hours
        - **Percentage Moves**: Relative changes over 24 hours
        
        **Sorting**: Markets are ordered by largest absolute notional move (24h) in descending order.
        
        **% Recent Volume Table**: Shows markets sorted by the percentage of total volume that occurred in the last 24 hours. This helps identify markets with recent activity spikes.
        
        **Why This Matters**: Large notional moves in markets with time remaining often indicate:
        - New information entering the market
        - Significant position changes
        - Potential trading opportunities
        - Markets to watch for further developments
        """)

if __name__ == "__main__":
    main()
