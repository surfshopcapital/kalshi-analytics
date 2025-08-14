# pages/Series.py

import streamlit as st
import pandas as pd
import altair as alt
import datetime
import numpy as np
from html import escape
from kalshi_client import KalshiClient
from utils import load_series_data_from_store, API_KEY, get_volume_columns, load_candles_from_store, make_ticker_clickable, make_title_clickable
import datetime

@st.cache_data(ttl=300)
def load_markets_for_series(series_ticker: str) -> pd.DataFrame:
    """
    Fetch all markets (open + closed) in a given series.
    """
    client = KalshiClient(api_key=API_KEY)
    resp = client.get_markets(limit=1000, series_ticker=series_ticker, status="open")
    return pd.DataFrame(resp.get("markets", []))

def extract_subseries(ticker: str, series_ticker: str) -> str:
    """
    Extract sub-series identifier from ticker.
    Example: KXPGATOUR-FSJC25-BCAU with series KXPGATOUR returns FSJC25
    """
    if not ticker or not series_ticker:
        return "Unknown"
    
    # Remove series prefix and leading dash
    if ticker.startswith(series_ticker + "-"):
        remainder = ticker[len(series_ticker) + 1:]
        # For sub-series selection, we want the first part after series
        # e.g., KXPGATOUR-FSJC25-BCAU -> FSJC25
        # e.g., KXPAYROLLS-25AUG -> 25AUG
        parts = remainder.split("-")
        return parts[0] if parts else remainder
    return ticker

def get_subseries_display_name(subseries_code: str, series_ticker: str) -> str:
    """
    Convert subseries code to human-readable name.
    """
    # Common tournament/event mappings
    display_names = {
        # PGA Tour events
        "FSJC25": "FedEx St Jude Championship",
        "BC25": "BMW Championship",
        "TC25": "Tour Championship",
        # Add more as needed
    }
    
    # If we have a mapping, use it. Otherwise use the code.
    return display_names.get(subseries_code, subseries_code)

def get_unique_subseries(markets_df: pd.DataFrame, series_ticker: str) -> list:
    """
    Get unique sub-series from markets data.
    Returns list of tuples: (subseries_code, display_name, count)
    """
    if markets_df.empty:
        return []
    
    markets_df = markets_df.copy()
    markets_df["subseries"] = markets_df["ticker"].apply(lambda x: extract_subseries(x, series_ticker))
    
    # Count markets per subseries
    subseries_counts = markets_df["subseries"].value_counts()
    
    result = []
    for subseries_code, count in subseries_counts.items():
        if subseries_code and subseries_code != "Unknown":
            display_name = get_subseries_display_name(subseries_code, series_ticker)
            result.append((subseries_code, display_name, count))
    
    return sorted(result, key=lambda x: x[2], reverse=True)  # Sort by count desc

def create_subseries_chart(markets_df: pd.DataFrame, series_ticker: str, selected_subseries: str = None, start_date: datetime.date = None, end_date: datetime.date = None) -> alt.Chart:
    """
    Create a time series chart showing price evolution for each sub-series.
    Only shows top 10 markets by yes_bid for cleaner visualization.
    """
    if markets_df.empty:
        return alt.Chart().mark_text().encode(text=alt.value("No data available"))
    
    # Extract sub-series for each market
    markets_df = markets_df.copy()
    markets_df["subseries"] = markets_df["ticker"].apply(lambda x: extract_subseries(x, series_ticker))
    
    # Filter to selected sub-series if specified
    if selected_subseries:
        markets_df = markets_df[markets_df["subseries"] == selected_subseries]
        if markets_df.empty:
            return alt.Chart().mark_text().encode(text=alt.value(f"No markets found for sub-series: {selected_subseries}"))
    
    # Sort by yes_bid descending and take top 10 for chart (keep all for table)
    markets_df_sorted = markets_df.sort_values("yes_bid", ascending=False, na_position="last")
    top_10_markets = markets_df_sorted.head(10)
    
    # Determine time window
    if start_date and end_date:
        start_ts = int(pd.Timestamp(start_date).timestamp())
        end_ts = int(pd.Timestamp(end_date).timestamp())
        # Filter markets by date range - show markets that are active during the period
        # (markets that either opened during the period OR are still active)
        open_dt = pd.to_datetime(top_10_markets["open_time"], utc=True, errors="coerce").dt.tz_convert(None)
        close_dt = pd.to_datetime(top_10_markets["close_time"], utc=True, errors="coerce").dt.tz_convert(None)
        start_naive = pd.Timestamp(start_date)
        end_naive = pd.Timestamp(end_date)
        
        # Market is active during period if: (opens before end) AND (closes after start)
        mask = (open_dt <= end_naive) & (close_dt >= start_naive)
        top_10_markets = top_10_markets.loc[mask]
    else:
        end_ts = int(pd.Timestamp.now().timestamp())
        start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=30)).timestamp())
    
    if top_10_markets.empty:
        return alt.Chart().mark_text().encode(text=alt.value("No markets found in selected date range"))
    
    # Create chart data
    chart_data = []
    for _, market in top_10_markets.iterrows():
        ticker = market["ticker"]
        title = market["title"]
        
        # Load candle data for this market
        try:
            candles = load_candles_from_store(ticker, "1h", start_ts, end_ts)
            if not candles.empty:
                candles = candles.copy()
                # Normalize candle fields - handle both dict and direct price formats
                if "price" in candles.columns:
                    if isinstance(candles["price"].iloc[0], dict):
                        price_df = pd.json_normalize(candles["price"])
                        candles["close_price"] = price_df.get("close", np.nan)
                    else:
                        # If price is already a scalar, use it directly
                        candles["close_price"] = candles["price"]
                else:
                    # Fallback: use last_price if available
                    candles["close_price"] = market.get("last_price", market.get("yes_bid", np.nan))
                
                candles["timestamp"] = candles["end_period_ts"]
                candles["ticker"] = ticker
                candles["title"] = title
                chart_data.append(candles[["timestamp", "close_price", "volume", "ticker", "title"]])
        except Exception as e:
            # Create dummy data point using current market price for markets without candle data
            current_price = market.get("last_price", market.get("yes_bid", np.nan))
            if pd.notna(current_price):
                dummy_data = pd.DataFrame({
                    "timestamp": [end_ts],
                    "close_price": [current_price],
                    "volume": [market.get("volume", 0)],
                    "ticker": [ticker],
                    "title": [title]
                })
                chart_data.append(dummy_data)
            else:
                st.warning(f"Could not load candle data for {ticker}: {str(e)}")
            continue
    
    if not chart_data:
        return alt.Chart().mark_text().encode(text=alt.value("No historical data available for selected markets"))
    
    # Combine all candle data
    all_candles = pd.concat(chart_data, ignore_index=True)
    
    # Convert timestamp to datetime for Altair
    all_candles["datetime"] = pd.to_datetime(all_candles["timestamp"], unit="s")
    
    # Ensure continuous lines per ticker by forward-filling over complete timestamp ranges
    def infer_freq(delta_seconds: float) -> str:
        if delta_seconds <= 60:
            return "1min"
        if delta_seconds <= 3600:
            return "1H"
        return "1D"

    filled_parts = []
    for tkr, g in all_candles.sort_values("datetime").groupby("ticker"):
        if len(g) >= 2:
            deltas = (g["datetime"].diff().dropna().dt.total_seconds())
            step = deltas.mode().iloc[0] if not deltas.empty else 3600
            freq = infer_freq(step)
        else:
            freq = "1H"
        full_range = pd.date_range(start=g["datetime"].min(), end=g["datetime"].max(), freq=freq)
        g2 = g.set_index("datetime").reindex(full_range)
        g2[["close_price", "volume"]] = g2[["close_price", "volume"]].ffill()
        g2["ticker"] = tkr
        g2["title"] = g["title"].iloc[0]
        g2 = g2.reset_index().rename(columns={"index": "datetime"})
        filled_parts.append(g2)
    all_candles = pd.concat(filled_parts, ignore_index=True)

    # Create the chart
    chart = alt.Chart(all_candles).mark_line().encode(
        x=alt.X("datetime:T", title="Date", axis=alt.Axis(format="%m/%d")),
        y=alt.Y("close_price:Q", title="Close Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color("ticker:N", title="Market", legend=alt.Legend(title="Markets")),
        tooltip=[
            alt.Tooltip("datetime:T", title="Date", format="%m/%d/%Y %H:%M"),
            alt.Tooltip("ticker:N", title="Market"),
            alt.Tooltip("title:N", title="Title"),
            alt.Tooltip("close_price:Q", title="Close", format="$.2f"),
            alt.Tooltip("volume:Q", title="Volume", format=",.0f")
        ]
    ).properties(
        title=f"Price Evolution - {selected_subseries if selected_subseries else 'All Sub-series'}",
        width="container",
        height=400
    ).interactive()
    
    return chart

def create_volume_chart(markets_df: pd.DataFrame, series_ticker: str, selected_subseries: str = None, start_date: datetime.date = None, end_date: datetime.date = None) -> alt.Chart:
    """
    Create a volume chart showing trading activity over time.
    """
    if markets_df.empty:
        return alt.Chart().mark_text().encode(text=alt.value("No data available"))
    
    # Filter to selected sub-series if specified
    if selected_subseries:
        markets_df = markets_df[markets_df["ticker"].apply(lambda x: extract_subseries(x, series_ticker)) == selected_subseries]
        if markets_df.empty:
            return alt.Chart().mark_text().encode(text=alt.value(f"No markets found for sub-series: {selected_subseries}"))
    
    # Determine time window
    if start_date and end_date:
        start_ts = int(pd.Timestamp(start_date).timestamp())
        end_ts = int(pd.Timestamp(end_date).timestamp())
    else:
        end_ts = int(pd.Timestamp.now().timestamp())
        start_ts = int((pd.Timestamp.now() - pd.Timedelta(days=30)).timestamp())

    # Create chart data
    chart_data = []
    for _, market in markets_df.iterrows():
        ticker = market["ticker"]
        
        # Load candle data for this market
        try:
            candles = load_candles_from_store(ticker, "1h", start_ts, end_ts)
            if not candles.empty:
                candles = candles.copy()
                candles["timestamp"] = candles["end_period_ts"]
                candles["ticker"] = ticker
                chart_data.append(candles[["timestamp", "volume", "ticker"]])
        except Exception as e:
            continue
    
    if not chart_data:
        return alt.Chart().mark_text().encode(text=alt.value("No historical data available"))
    
    # Combine all candle data
    all_candles = pd.concat(chart_data, ignore_index=True)
    
    # Convert timestamp to datetime for Altair
    all_candles["datetime"] = pd.to_datetime(all_candles["timestamp"], unit="s")
    
    # Aggregate volume by date
    all_candles["date"] = all_candles["datetime"].dt.date
    daily_volume = all_candles.groupby("date")["volume"].sum().reset_index()
    daily_volume["datetime"] = pd.to_datetime(daily_volume["date"])
    
    # Filter by date range if specified
    if start_date and end_date:
        daily_volume = daily_volume[
            (daily_volume["datetime"] >= pd.Timestamp(start_date)) &
            (daily_volume["datetime"] <= pd.Timestamp(end_date))
        ]
    
    if daily_volume.empty:
        return alt.Chart().mark_text().encode(text=alt.value("No volume data in selected date range"))
    
    # Create the volume chart
    chart = alt.Chart(daily_volume).mark_area(opacity=0.6).encode(
        x=alt.X("datetime:T", title="Date", axis=alt.Axis(format="%m/%d")),
        y=alt.Y("volume:Q", title="Daily Volume ($)", scale=alt.Scale(type="log")),
        tooltip=[
            alt.Tooltip("datetime:T", title="Date", format="%m/%d/%Y"),
            alt.Tooltip("volume:Q", title="Volume", format="$,.0f")
        ]
    ).properties(
        title=f"Daily Trading Volume - {selected_subseries if selected_subseries else 'All Sub-series'}",
        width="container",
        height=200
    ).interactive()
    
    return chart

def main():
    st.set_page_config(page_title="Series Analysis", layout="wide")
    st.title("📊 Series Analysis")
    
    st.markdown("""
    This page allows you to analyze markets within specific Kalshi series (e.g., KXPGATOUR for PGA Tour events).
    Select a series and optionally a sub-series to view detailed price evolution charts and market data.
    """)
    
    # ── Load Series Data ───────────────────────────────────────────────────
    with st.spinner("Loading series data..."):
        # load_series_data_from_store returns (series_list, df)
        result = load_series_data_from_store()
        if isinstance(result, tuple):
            series_list, series_df = result
        else:
            # Backward compatibility
            series_list, series_df = [], result

        if series_df is None or series_df.empty:
            st.error("Could not load series data. Please check your API connection.")
            return
        # Ensure expected column naming
        if "series_ticker" not in series_df.columns and "ticker" in series_df.columns:
            series_df = series_df.rename(columns={"ticker": "series_ticker"})
        
        # Get top series by 24h volume
        vol24_series, total_vol_series = get_volume_columns(series_df)
        if total_vol_series is None or not isinstance(total_vol_series, pd.Series):
            total_vol_series = pd.Series(0, index=series_df.index)
        
        # ── Clean card grid (4 x 6), uniform size, bold amount ─────────────
        st.subheader("Top 24 Series by 24h Volume")
        st.markdown(
            """
            <style>
            .series-card{border:1px solid #e5e7eb;border-radius:10px;padding:12px;height:110px;display:flex;flex-direction:column;justify-content:space-between;background:#fff}
            .series-card .title{font-weight:600;line-height:1.2;max-height:3.0em;overflow:hidden;}
            .series-card .amt{font-weight:700;color:#111827}
            .series-card-btn > button{width:100%}
            </style>
            """,
            unsafe_allow_html=True,
        )
        series_sorted = series_df.assign(_vol24=vol24_series.fillna(0)).sort_values("_vol24", ascending=False).head(24)
        # Render in chunks of 6 per row (4 rows)
        for start in range(0, len(series_sorted), 6):
            cols = st.columns(6)
            chunk = series_sorted.iloc[start:start+6]
            for idx, (_, row) in enumerate(chunk.iterrows()):
                with cols[idx]:
                    title_txt = str(row.get("title", ""))
                    vol_val = row.get("_vol24", 0)
                    sr = str(row.get("series_ticker", ""))
                    st.markdown(f"<div class='series-card'><div class='title'>{escape(title_txt)}</div><div class='amt'>${vol_val:,.0f}</div></div>", unsafe_allow_html=True)
                    if st.button("Select", key=f"series_card_{start}_{idx}"):
                        st.session_state.selected_series = sr
                        st.rerun()
        
        st.divider()
        
        # ── Selected series → sub-series selection ─────────────────────────
        # Accept deep-link selection via query params
        try:
            qp = st.query_params  # Streamlit >=1.32
            q_series = qp.get("series") if qp else None
            if isinstance(q_series, list):
                q_series = q_series[0] if q_series else None
        except Exception:
            q_series = st.experimental_get_query_params().get("series", [None])[0]
        if q_series:
            st.session_state.selected_series = q_series

        selected = st.session_state.get("selected_series")
        if selected:
            # Load markets for selected series
            markets_df = load_markets_for_series(selected)
            
            if markets_df.empty:
                st.warning(f"No markets found for series {selected}")
                return
            

            
            # Get unique sub-series
            subseries_list = get_unique_subseries(markets_df, selected)
            
            if subseries_list:
                st.success(f"Found {len(markets_df)} markets in {len(subseries_list)} sub-series for {selected}")
                
                # Auto-select if only one subseries, otherwise show selector
                if len(subseries_list) == 1:
                    # Auto-select the only subseries
                    selected_subseries_code = subseries_list[0][0]  # Get the code from first (and only) subseries
                    st.info(f"Auto-selected subseries: {selected_subseries_code} - {subseries_list[0][1]}")
                else:
                    # Show selector for multiple subseries
                    subseries_options = [f"{code} - {name}" for code, name, count in subseries_list]
                    selected_subseries = st.selectbox(
                        "Choose a sub-series:",
                        options=subseries_options,
                        index=0,
                        key=f"subseries_selector_{selected}"
                    )
                    selected_subseries_code = selected_subseries.split(" - ")[0]
                
                markets_df_filtered = markets_df[markets_df["ticker"].apply(lambda x: extract_subseries(x, selected) == selected_subseries_code)]
                
                # Date range selector
                with st.expander("📅 Date Range Selection", expanded=False):
                    # Default to last 30 days, but allow custom range
                    if not markets_df_filtered.empty:
                        open_times = pd.to_datetime(markets_df_filtered["open_time"], utc=True, errors="coerce").dt.tz_convert(None)
                        close_times = pd.to_datetime(markets_df_filtered["close_time"], utc=True, errors="coerce").dt.tz_convert(None)
                        if not open_times.empty and not close_times.empty:
                            default_start = open_times.min().date()
                            default_end = close_times.max().date()
                        else:
                            default_start = (pd.Timestamp.now() - pd.Timedelta(days=30)).date()
                            default_end = pd.Timestamp.now().date()
                    else:
                        default_start = (pd.Timestamp.now() - pd.Timedelta(days=30)).date()
                        default_end = pd.Timestamp.now().date()
                    
                    start_date, end_date = st.date_input(
                        "Select date range for chart:",
                        [default_start, default_end],
                        key="series_date_range"
                    )
                
                # ── Sub-series Time Series Chart ──────────────────────────
                st.subheader("📈 Price Evolution Chart")
                display_name = get_subseries_display_name(selected_subseries_code, selected)
                # For a chosen sub-series, display full historical timeseries for its markets
                # Use earliest open_time and latest close_time to build full window
                if not markets_df_filtered.empty:
                    open_times = pd.to_datetime(markets_df_filtered["open_time"], utc=True, errors="coerce").dt.tz_convert(None)
                    close_times = pd.to_datetime(markets_df_filtered["close_time"], utc=True, errors="coerce").dt.tz_convert(None)
                    start_date_full = open_times.min().date() if not open_times.empty else (pd.Timestamp.now() - pd.Timedelta(days=30)).date()
                    end_date_full = close_times.max().date() if not close_times.empty else pd.Timestamp.now().date()
                else:
                    start_date_full = (pd.Timestamp.now() - pd.Timedelta(days=30)).date()
                    end_date_full = pd.Timestamp.now().date()
                # Force chart to re-render on each (series, subseries) change and include all markets if fewer than 10
                st.write("")
                chart = create_subseries_chart(markets_df_filtered.copy(), selected, selected_subseries_code, start_date_full, end_date_full)
                st.altair_chart(chart, use_container_width=True)
                
                st.markdown("---")
                
                # ── Markets Table (dataframe) ─────────────────────────────
                st.subheader(f"📋 {display_name} ({selected_subseries_code}) — Markets")
                st.caption(f"{len(markets_df_filtered)} events in this sub-series")
            else:
                markets_df_filtered = pd.DataFrame()  # Nothing to show until a subseries is present
            
            # Only show bottom section (chart + table) after series is chosen and we have data
            if not markets_df_filtered.empty:
                # Normalize columns and build tidy display with consistent volume logic
                dfm = markets_df_filtered.copy()
                vol24_series, total_vol_series = get_volume_columns(dfm)

                # Sort by Yes Bid descending
                dfm_sorted = dfm.assign(_yes_bid=dfm["yes_bid"].fillna(0)).sort_values("_yes_bid", ascending=False).drop(columns=["_yes_bid"])
                display_df = dfm_sorted[[
                    "ticker","title","yes_sub_title","no_sub_title","yes_bid","yes_ask","no_bid","no_ask","last_price","open_interest","close_time"
                ]].rename(columns={
                    "yes_sub_title":"Yes Subtitle",
                    "no_sub_title":"No Subtitle",
                    "yes_bid":"Yes Bid",
                    "yes_ask":"Yes Ask",
                    "no_bid":"No Bid",
                    "no_ask":"No Ask",
                    "last_price":"Last Price",
                    "open_interest":"Open Interest",
                    "close_time":"Close Time"
                })
                st.dataframe(
                    display_df.style.format({
                        "Yes Bid":"${:,.0f}","Yes Ask":"${:,.0f}","No Bid":"${:,.0f}","No Ask":"${:,.0f}","Last Price":"${:,.0f}","Open Interest":"{:,.0f}"
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
        
        # ── Explanation ─────────────────────────────────────────────────────
        with st.expander("ℹ️ About This Page", expanded=False):
            st.write("""
            **Purpose**: This page allows you to analyze markets within specific Kalshi series and sub-series.
            
            **Features**:
            - **Series Selection**: Choose from top series by 24h trading volume
            - **Sub-series Analysis**: Drill down into specific events within a series
            - **Price Evolution Charts**: Visualize how market prices change over time
            - **Volume Analysis**: Track trading activity patterns
            - **Interactive Tables**: Click any ticker or title to view detailed analytics on the Overview page
            
            **Data Source**: Live market data from Kalshi API, with historical price data from cached candles.
            
            **Chart Types**:
            - **Price Evolution**: Line charts showing Yes Bid price changes over time
            - **Volume Charts**: Area charts showing daily trading volume
            
            **Navigation**: Click any ticker or title in the tables to navigate to the Overview page with pre-selected data.
            """)

if __name__ == "__main__":
    main()