# pages/overview.py

import streamlit as st
import pandas as pd
import datetime
import altair as alt
from requests.exceptions import HTTPError
import numpy as np
import os

# Safe imports with fallbacks
try:
    from utils import (
        API_KEY, 
        get_client, 
        get_unified_markets, 
        get_markets_by_source, 
        load_candles_from_store
    )
    UTILS_AVAILABLE = True
except ImportError as e:
    UTILS_AVAILABLE = False
    print(f"Warning: Could not import from utils: {e}")
    # Create fallback values
    API_KEY = ""
    def get_client():
        return None
    def get_unified_markets(data_sources):
        return pd.DataFrame()
    def get_markets_by_source(data_source):
        return pd.DataFrame()
    def load_candles_from_store(ticker, granularity, start_ts, end_ts):
        return pd.DataFrame()

try:
    from shared_sidebar import render_shared_sidebar, get_selected_data_sources, get_selected_data_source_display
    SIDEBAR_AVAILABLE = True
except ImportError as e:
    SIDEBAR_AVAILABLE = False
    print(f"Warning: Could not import from shared_sidebar: {e}")
    # Create fallback functions
    def render_shared_sidebar():
        st.sidebar.markdown("## 📊 Data Source")
        st.sidebar.markdown("**Kalshi** (default)")
    def get_selected_data_sources():
        return ['kalshi']
    def get_selected_data_source_display():
        return "Kalshi (default)"

def create_line_chart(df: pd.DataFrame, title: str) -> alt.Chart:
    """
    Create a line chart showing price evolution over time.
    """
    if df.empty:
        return alt.Chart().mark_text().encode(text=alt.value("No data available"))
    
    # Convert timestamp to datetime
    df_chart = df.copy()
    df_chart["timestamp"] = pd.to_datetime(df_chart["end_period_ts"], unit="s")
    
    # Make lines continuous by filling gaps with forward fill
    if not df_chart.empty:
        # Get the full timestamp range
        min_time = df_chart["timestamp"].min()
        max_time = df_chart["timestamp"].max()
        
        # Create complete timestamp range (use the same frequency as the data)
        # Determine frequency from the data
        if len(df_chart) > 1:
            time_diff = df_chart["timestamp"].iloc[1] - df_chart["timestamp"].iloc[0]
            if time_diff.total_seconds() <= 60:  # 1 minute or less
                freq = "1min"
            elif time_diff.total_seconds() <= 3600:  # 1 hour or less
                freq = "1H"
            else:
                freq = "1D"
        else:
            freq = "1H"  # Default to hourly
        
        full_timestamps = pd.date_range(start=min_time, end=max_time, freq=freq)
        
        # Create complete timestamp series
        complete_timestamps = pd.DataFrame({"timestamp": full_timestamps})
        
        # Merge with actual data and forward fill
        merged = complete_timestamps.merge(df_chart, on="timestamp", how="left")
        merged = merged.sort_values("timestamp").fillna(method="ffill")
        
        # Only keep rows where we have actual data or forward-filled data
        merged = merged.dropna(subset=["close_price"])
        
        df_chart = merged
    
    # Create price line chart (top)
    price_chart = alt.Chart(df_chart).mark_line(point=False, strokeWidth=2).encode(
        x=alt.X("timestamp:T", title="Date", scale=alt.Scale(nice=False)),
        y=alt.Y("close_price:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        tooltip=["timestamp:T", "close_price:Q", "volume:Q"]
    ).properties(
        height=300,
        title=title
    ).interactive()
    
    # Create volume chart (bottom)
    volume_chart = alt.Chart(df_chart).mark_bar(opacity=0.7).encode(
        x=alt.X("timestamp:T", title="Date", scale=alt.Scale(nice=False)),
        y=alt.Y("volume:Q", title="Volume"),
        color=alt.value("#1f77b4"),
        tooltip=["timestamp:T", "volume:Q"]
    ).properties(height=150)
    
    # Combine charts vertically
    combined_chart = alt.vconcat(
        price_chart,
        volume_chart.interactive()
    ).resolve_scale(x="shared")
    
    return combined_chart

def main():
    st.set_page_config(page_title="Overview", layout="wide")
    
    # ── Render Shared Sidebar ─────────────────────────────────────────────
    render_shared_sidebar()
    
    # ── Main Content ──────────────────────────────────────────────────────
    st.title("🏠 Market Overview")

    # Get selected data sources
    selected_sources = get_selected_data_sources()
    data_source_display = get_selected_data_source_display()
    
    # Show data source indicator
    st.info(f"📊 Showing data from: **{data_source_display}**")

    # Add CSS for clickable ticker styling
    st.markdown("""
        <style>
        .stButton > button {
            background: transparent;
            color: #0066cc;
            border: none;
            text-decoration: underline;
            font-weight: 500;
            padding: 0;
            margin: 0;
            cursor: pointer;
            text-align: left;
            box-shadow: none;
        }
        .stButton > button:hover {
            background: transparent;
            color: #004499;
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    # ── Handle deep-link via query params (e.g., ?ticker=XYZ&title=Name) ─────
    try:
        # Newer Streamlit
        qp = st.query_params  # type: ignore[attr-defined]
        qp_ticker = qp.get("ticker") if qp else None
        qp_title = qp.get("title") if qp else None
        # In some versions values may be lists
        if isinstance(qp_ticker, list):
            qp_ticker = qp_ticker[0] if qp_ticker else None
        if isinstance(qp_title, list):
            qp_title = qp_title[0] if qp_title else None
    except Exception:
        # Older Streamlit
        qp_all = st.experimental_get_query_params()
        qp_ticker = qp_all.get("ticker", [None])[0]
        qp_title = qp_all.get("title", [None])[0]

    if qp_ticker:
        st.session_state.selected_ticker = qp_ticker
        if qp_title:
            st.session_state.selected_title = qp_title

    # ── Load markets (cached for 5m) ───────────────────────────────
    markets_df = get_unified_markets()
    if markets_df.empty:
        st.error("Could not load markets—check your API key.")
        return

    # ── Enforce min-volume and sort by 24h volume desc ─────────────
    MIN_VOL = 1000
    eligible_df = (
        markets_df.loc[markets_df.get("volume", 0) >= MIN_VOL]
        .sort_values("volume", ascending=False)
    )
    if eligible_df.empty:
        st.warning("No markets meet the 24h volume threshold (>= 1,000).")
        return

    # ── Choose input mode ────────────────────────────────────────
    # Removed input mode toggle - simplified interface
    
    # Check if we have a selected ticker from navigation
    selected_ticker = st.session_state.get("selected_ticker")
    selected_title = st.session_state.get("selected_title")
    
    if selected_ticker and selected_title:
        # Clear the session state to avoid persistent selection
        del st.session_state.selected_ticker
        del st.session_state.selected_title
        
        # Pre-populate the search with the selected title
        term = selected_title
        filt = eligible_df["title"].str.contains(term, case=False, na=False)
        filtered = eligible_df.loc[filt]
        
        if not filtered.empty:
            # Find the exact match or closest match
            exact_match = filtered[filtered["title"].str.lower() == selected_title.lower()]
            if not exact_match.empty:
                choice = exact_match.iloc[0]["title"]
            else:
                # Use the first match
                choice = filtered.iloc[0]["title"]
            
            ticker = filtered.loc[filtered["title"] == choice, "ticker"].iloc[0]
            display_name = choice
        else:
            # Fall back to default behavior
            term = ""
            filt = eligible_df["title"].str.contains(term, case=False, na=False)
            filtered = eligible_df.loc[filt]
            if filtered.empty:
                st.warning("No markets match that filter (after applying ≥1k volume).")
                return
            titles = filtered["title"].tolist()
            choice = st.selectbox("► Select a market", titles, index=0)
            ticker = filtered.loc[filtered["title"] == choice, "ticker"].iloc[0]
            display_name = choice
    else:
        # Default behavior - no pre-selection
        term = st.text_input("🔍 Filter markets by title", "")
        filt = eligible_df["title"].str.contains(term, case=False, na=False)
        filtered = eligible_df.loc[filt]
        if filtered.empty:
            st.warning("No markets match that filter (after applying ≥1k volume).")
            return
        titles = filtered["title"].tolist()
        choice = st.selectbox("► Select a market", titles, index=0)
        ticker = filtered.loc[filtered["title"] == choice, "ticker"].iloc[0]
        display_name = choice

    st.subheader(f"Overview for {display_name}  ({ticker})")

    # ── Date range & granularity ────────────────────────────────
    interval = st.selectbox("Granularity", ["1m", "1h", "1d"], index=1)
    # Default to market open → today if available
    row_for_default = markets_df.loc[markets_df["ticker"] == ticker].iloc[0]
    open_ts_val = row_for_default.get("open_time") or row_for_default.get("start_time")
    try:
        if pd.notna(open_ts_val):
            # Handle both integer timestamps and ISO strings
            if isinstance(open_ts_val, (int, float)) or str(open_ts_val).isdigit():
                default_start = pd.to_datetime(int(open_ts_val), unit="s")
            else:
                default_start = pd.to_datetime(open_ts_val)
        else:
            default_start = pd.Timestamp.now() - pd.Timedelta(days=7)
    except Exception:
        default_start = pd.Timestamp.now() - pd.Timedelta(days=7)
    default_end = pd.Timestamp.now()

    start_date, end_date = st.date_input(
        "Date range",
        [default_start, default_end]
    )
    start_dt = datetime.datetime.combine(start_date, datetime.time.min)
    end_dt   = datetime.datetime.combine(end_date,   datetime.time.max)
    start_ts = int(start_dt.timestamp())
    end_ts   = int(end_dt.timestamp())

    # ── Fetch candlesticks (still cached by get_client) ──────────
    client = get_client()
    try:
        df_c = load_candles_from_store(ticker, interval, start_ts, end_ts)
        if df_c.empty:
            st.warning("No cached data for that ticker/range—try rerunning the refresher.")
            return
    except FileNotFoundError:
        st.warning("No cache file found for this ticker—run the refresher script.")
        return
    except Exception as e:
        st.error(f"Error reading cached data: {e}")
        return

    #  ── Build DataFrame (optimized OHLC processing) ──────────────────────────
    #  (you already have df_c columns: end_period_ts, price, volume)
    df_c["timestamp"] = pd.to_datetime(df_c["end_period_ts"], unit="s")
    
    # Optimized: extract all OHLC values in one vectorized operation
    price_data = pd.json_normalize(df_c["price"])
    df_c["open_price"]  = price_data.get("open", np.nan)
    df_c["high_price"]  = price_data.get("high", np.nan)
    df_c["low_price"]   = price_data.get("low", np.nan)
    df_c["close_price"] = price_data.get("close", np.nan)
    df_c["mean_price"]  = price_data.get("mean", np.nan)
    
    # ── Create Line Chart with Volume ────────────────────────────
    chart_title = f"Price Evolution for {display_name} ({ticker})"
    chart = create_line_chart(df_c, chart_title)
    st.altair_chart(chart, use_container_width=True)

    # ── Daily Stats Table ────────────────────────────────────────
    st.subheader("Daily OHLC + Volume + VWAP")
    df_daily = df_c.copy()
    df_daily["date"] = df_daily["timestamp"].dt.date

    # 1) Group OHLC + Volume
    daily = df_daily.groupby("date").agg({
        "open_price":  "first",
        "high_price":  "max",
        "low_price":   "min",
        "close_price": "last",
        "volume":      "sum",
    })

    # 2) Compute VWAP safely
    vwap_num   = (df_daily["mean_price"] * df_daily["volume"]).groupby(df_daily["date"]).sum()
    vwap_denom = daily["volume"]
    daily["VWAP"] = np.where(vwap_denom > 0, vwap_num / vwap_denom, np.nan)

    # 3) Rename for display
    daily = daily.rename(columns={
        "open_price":  "Open",
        "high_price":  "High",
        "low_price":   "Low",
        "close_price": "Close",
        "volume":      "Volume",
    })
    daily.index.name = "Date"

    # 4) Show table
    st.dataframe(
        daily.style.format({
            "Open":   "${:,.2f}",
            "High":   "${:,.2f}",
            "Low":    "${:,.2f}",
            "Close":  "${:,.2f}",
            "Volume": "{:,.0f}",
            "VWAP":   "${:,.2f}"
        }),
        use_container_width=True,
        height=300,
    )

if __name__ == "__main__":
    main()