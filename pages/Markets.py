# pages/Markets.py

import streamlit as st
import pandas as pd
import numpy as np

# Import helper to fix path issues
import import_helper

# Safe imports with fallbacks
try:
    from utils import (
        get_unified_markets, 
        get_markets_by_source, 
        get_volume_columns, 
        make_ticker_clickable, 
        make_title_clickable
    )
    UTILS_AVAILABLE = True
except ImportError as e:
    UTILS_AVAILABLE = False
    print(f"Warning: Could not import from utils: {e}")
    # Create fallback functions
    def get_unified_markets(data_sources):
        return pd.DataFrame()
    def get_markets_by_source(data_source):
        return pd.DataFrame()
    def get_volume_columns(df):
        return pd.Series(0, index=df.index), pd.Series(0, index=df.index)
    def make_ticker_clickable(ticker, display_text=None, key=None):
        return False
    def make_title_clickable(title, ticker=None, key=None):
        return False

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

# Safe imports for other dependencies
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    duckdb = None

import urllib.parse
import os

def main():
    st.set_page_config(page_title="Markets", layout="wide")
    
    # ── Render Shared Sidebar ─────────────────────────────────────────────
    render_shared_sidebar()
    
    # ── Main Content ──────────────────────────────────────────────────────
    st.title("📊 Markets")
    
    # Get selected data source
    selected_sources = get_selected_data_sources()
    data_source_display = get_selected_data_source_display()
    
    st.markdown(f"""
    This page shows all active markets from **{data_source_display}** with their current prices, volumes, and trading activity.
    Click the 🔎 icon in any row to open its chart on the Overview page.
    """)
    
    # ── Load Data ───────────────────────────────────────────────────────────
    with st.spinner(f"Loading {data_source_display} market data..."):
        # Load markets based on selected data source
        if len(selected_sources) > 1:
            # Multiple sources - use unified function
            df = get_unified_markets(selected_sources)
        else:
            # Single source - use source-specific function
            df = get_markets_by_source(selected_sources[0])
        
        if df.empty:
            st.error(f"Could not load {data_source_display} markets data. Please check your data refresh.")
            return
        
        # Get volume columns (handle both Kalshi and Polymarket data structures)
        vol24_series, total_vol_series = get_volume_columns(df)
        
        # Ensure volume series are not None and have proper indices
        if vol24_series is None or vol24_series.empty:
            vol24_series = pd.Series(0, index=df.index)
        if total_vol_series is None or total_vol_series.empty:
            total_vol_series = pd.Series(0, index=df.index)
        
        # ── Data Source Indicator ──────────────────────────────────────────
        st.info(f"📊 Showing data from: **{data_source_display}** ({len(df)} markets)")
        
        # ── Top Markets by 24h Volume ───────────────────────────────────────
        # Get top markets by 24h volume
        n = 20  # Show top 20 markets
        
        # Sort by 24h volume and get top N
        df_sorted = df.assign(_vol24=vol24_series).sort_values("_vol24", ascending=False).head(n)
        df_top = df_sorted.drop(columns=["_vol24"])
        
        # Get volume columns for top markets - ensure indices match
        try:
            vol24_top = vol24_series.loc[df_top.index]
            total_vol_top = total_vol_series.loc[df_top.index]
        except (KeyError, AttributeError):
            # Fallback if indices don't match
            vol24_top = pd.Series(0, index=df_top.index)
            total_vol_top = pd.Series(0, index=df_top.index)

        st.subheader(f"Top {n} Markets by 24h Volume")
        
        # Handle different column names for different data sources
        title_col = 'title' if 'title' in df_top.columns else 'Title'
        ticker_col = 'ticker' if 'ticker' in df_top.columns else 'market_id'
        yes_bid_col = 'yes_bid' if 'yes_bid' in df_top.columns else 'Yes Bid'
        yes_ask_col = 'yes_ask' if 'yes_ask' in df_top.columns else 'Yes Ask'
        
        # Handle Polymarket vs Kalshi differences
        if 'data_source' in df_top.columns and df_top['data_source'].iloc[0] == 'polymarket':
            # Polymarket data - no no_bid/no_ask columns
            no_bid_col = None
            no_ask_col = None
            # Use outcomes instead
            outcomes_col = 'outcomes' if 'outcomes' in df_top.columns else None
        else:
            # Kalshi data - has no_bid/no_ask columns
            no_bid_col = 'no_bid' if 'no_bid' in df_top.columns else 'No Bid'
            no_ask_col = 'no_ask' if 'no_ask' in df_top.columns else 'No Ask'
            outcomes_col = None
        
        last_price_col = 'last_price' if 'last_price' in df_top.columns else 'Last Price'
        close_time_col = 'close_time' if 'close_time' in df_top.columns else 'Close Time'
        
        # Build display DataFrame based on data source
        if 'data_source' in df_top.columns and df_top['data_source'].iloc[0] == 'polymarket':
            # Polymarket display - simpler structure
            df_top_display = pd.DataFrame({
                "Series":        df_top.get("Series", pd.Series(index=df_top.index, dtype=object)),
                "Title":         df_top.get(title_col),
                "Ticker":        df_top.get(ticker_col),
                "Outcomes":      df_top.get(outcomes_col, "N/A"),
                "Yes Bid":       df_top.get(yes_bid_col),
                "Yes Ask":       df_top.get(yes_ask_col),
                "Last Price":    df_top.get(last_price_col),
                "Volume (24h)":  vol24_top,
                "Total Volume":  total_vol_top,
                "Status":        df_top.get('status', 'Unknown'),
            })
            
            # Select columns for Polymarket
            display_columns = ["Series", "Title", "Ticker", "Outcomes", "Yes Bid", "Yes Ask", "Last Price", "Volume (24h)", "Total Volume", "Status"]
        else:
            # Kalshi display - full structure
            df_top_display = pd.DataFrame({
                "Series":        df_top.get("Series", pd.Series(index=df_top.index, dtype=object)),
                "Title":         df_top.get(title_col),
                "Ticker":        df_top.get(ticker_col),
                "Yes Bid":       df_top.get(yes_bid_col),
                "Yes Ask":       df_top.get(yes_ask_col),
                "No Bid":        df_top.get(no_bid_col),
                "No Ask":        df_top.get(no_ask_col),
                "Last Price":    df_top.get(last_price_col),
                "Volume (24h)":  vol24_top,
                "Total Volume":  total_vol_top,
                "Close Time":    df_top.get(close_time_col),
            })
            
            # Select columns for Kalshi
            display_columns = ["Series", "Title", "Ticker", "Yes Bid", "Yes Ask", "No Bid", "No Ask", "Last Price", "Volume (24h)", "Total Volume", "Close Time"]
        
        # Truncate long titles to single-line friendly length
        if "Title" in df_top_display.columns:
            titles = df_top_display["Title"].astype(str)
            df_top_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
        
        # Show clean dataframe with appropriate columns
        df_top_display = df_top_display[display_columns]
        
        # Apply formatting based on data source
        if 'data_source' in df_top.columns and df_top['data_source'].iloc[0] == 'polymarket':
            # Polymarket formatting - simpler
            st.dataframe(
                df_top_display.style.format({
                    "Yes Bid": "${:,.3f}",
                    "Yes Ask": "${:,.3f}",
                    "Last Price": "${:,.3f}",
                    "Volume (24h)": "${:,.0f}",
                    "Total Volume": "${:,.0f}",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            # Kalshi formatting - full
            st.dataframe(
                df_top_display.style.format({
                    "Yes Bid": "${:,.0f}",
                    "Yes Ask": "${:,.0f}",
                    "No Bid": "${:,.0f}",
                    "No Ask": "${:,.0f}",
                    "Last Price": "${:,.0f}",
                    "Volume (24h)": "${:,.0f}",
                    "Total Volume": "${:,.0f}",
                }),
                use_container_width=True,
                hide_index=True,
            )
        
        st.divider()
        
        # ── Summary Table (Top 10 by Total Volume) ─────────────────────────
        st.subheader("Top 10 Active Markets by Total Volume")
        # Build summary directly from raw df, sort by Total Volume, show top 10
        vol24_sum, total_vol_sum = get_volume_columns(df)
        
        # Build summary DataFrame based on data source
        if 'data_source' in df.columns and df['data_source'].iloc[0] == 'polymarket':
            # Polymarket summary - simpler structure
            df_sum = pd.DataFrame({
                "Series":        df.get("Series", pd.Series(index=df.index, dtype=object)),
                "Title":         df.get(title_col),
                "Ticker":        df.get(ticker_col),
                "Outcomes":      df.get('outcomes', "N/A"),
                "Yes Ask":       df.get(yes_ask_col),
                "Last Price":    df.get(last_price_col),
                "Volume (24h)":  vol24_sum,
                "Total Volume":  total_vol_sum,
                "Status":        df.get('status', 'Unknown'),
            })
            
            # Select columns for Polymarket summary
            summary_columns = ["Series", "Title", "Ticker", "Outcomes", "Yes Ask", "Last Price", "Volume (24h)", "Total Volume", "Status"]
        else:
            # Kalshi summary - full structure
            df_sum = pd.DataFrame({
                "Series":        df.get("Series", pd.Series(index=df.index, dtype=object)),
                "Title":         df.get(title_col),
                "Ticker":        df.get(ticker_col),
                "Yes Subtitle":  df.get("yes_sub_title", ""),
                "No Subtitle":   df.get("no_sub_title", ""),
                "Yes Ask":       df.get(yes_ask_col),
                "No Ask":        df.get(no_ask_col),
                "Last Price":    df.get(last_price_col),
                "Volume (24h)":  vol24_sum,
                "Total Volume":  total_vol_sum,
                "Close Time":    df.get(close_time_col),
            })
            
            # Select columns for Kalshi summary
            summary_columns = ["Series", "Title", "Ticker", "Yes Subtitle", "No Subtitle", "Yes Ask", "No Ask", "Last Price", "Volume (24h)", "Total Volume", "Close Time"]
        
        # Sort by Total Volume descending and show top 10
        df_sum = df_sum.assign(_total_vol=df_sum["Total Volume"].fillna(0)).sort_values("_total_vol", ascending=False).head(10).drop(columns=["_total_vol"])
        
        # Add link icon column and truncate titles
        df_sum_display = df_sum.copy()
        if "Title" in df_sum_display.columns:
            titles = df_sum_display["Title"].astype(str)
            df_sum_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
        
        df_sum_display.insert(0, "🔎", "click")
        df_sum_display = df_sum_display[summary_columns]
        
        # Apply formatting based on data source
        if 'data_source' in df.columns and df['data_source'].iloc[0] == 'polymarket':
            # Polymarket formatting - simpler
            st.dataframe(
                df_sum_display.style.format({
                    "Yes Ask": "${:,.3f}",
                    "Last Price": "${:,.3f}",
                    "Volume (24h)": "${:,.0f}",
                    "Total Volume": "${:,.0f}",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            # Kalshi formatting - full
            st.dataframe(
                df_sum_display.style.format({
                    "Yes Ask": "${:,.0f}",
                    "No Ask": "${:,.0f}",
                    "Last Price": "${:,.0f}",
                    "Volume (24h)": "${:,.0f}",
                    "Total Volume": "${:,.0f}",
                }),
                use_container_width=True,
                hide_index=True,
            )
        
        st.divider()
        
        # ── Search Markets ───────────────────────────────────────────────────
        st.subheader("🔍 Search Markets")
        
        # Search by title
        search_term = st.text_input("Search markets by title:", placeholder="Enter part of a market title...")
        
        if search_term:
            # Filter markets by search term
            filt = df[title_col].str.contains(search_term, case=False, na=False)
            df_search = df.loc[filt]
            
            if not df_search.empty:
                st.success(f"Found {len(df_search)} markets matching '{search_term}'")
                
                # Safely get volume data for search results
                try:
                    vol24_search = vol24_series.loc[df_search.index]
                    total_vol_search = total_vol_series.loc[df_search.index]
                except (KeyError, AttributeError):
                    # Fallback if indices don't match
                    vol24_search = pd.Series(0, index=df_search.index)
                    total_vol_search = pd.Series(0, index=df_search.index)
                
                # Build display df based on data source
                if 'data_source' in df_search.columns and df_search['data_source'].iloc[0] == 'polymarket':
                    # Polymarket search display - simpler structure
                    df_search_display = pd.DataFrame({
                        "Series":        df_search.get("Series", pd.Series(index=df_search.index, dtype=object)),
                        "Title":         df_search.get(title_col),
                        "Ticker":        df_search.get(ticker_col),
                        "Outcomes":      df_search.get('outcomes', "N/A"),
                        "Yes Ask":       df_search.get(yes_ask_col),
                        "Last Price":    df_search.get(last_price_col),
                        "Volume (24h)":  vol24_search,
                        "Total Volume":  total_vol_search,
                    })
                    
                    # Select columns for Polymarket search
                    search_columns = ["Series", "Title", "Ticker", "Outcomes", "Yes Ask", "Last Price", "Volume (24h)", "Total Volume"]
                else:
                    # Kalshi search display - full structure
                    df_search_display = pd.DataFrame({
                        "Series":        df_search.get("Series", pd.Series(index=df_search.index, dtype=object)),
                        "Title":         df_search.get(title_col),
                        "Ticker":        df_search.get(ticker_col),
                        "Yes Ask":       df_search.get(yes_ask_col),
                        "No Ask":        df_search.get(no_ask_col),
                        "Last Price":    df_search.get(last_price_col),
                        "Volume (24h)":  vol24_search,
                        "Total Volume":  total_vol_search,
                    })
                    
                    # Select columns for Kalshi search
                    search_columns = ["Series", "Title", "Ticker", "Yes Ask", "No Ask", "Last Price", "Volume (24h)", "Total Volume"]
                
                # Truncate titles and add link icon column
                if "Title" in df_search_display.columns:
                    titles = df_search_display["Title"].astype(str)
                    df_search_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
                
                df_search_display.insert(0, "🔎", "click")
                df_search_display = df_search_display[search_columns]
                
                # Apply formatting based on data source
                if 'data_source' in df_search.columns and df_search['data_source'].iloc[0] == 'polymarket':
                    # Polymarket formatting - simpler
                    st.dataframe(
                        df_search_display.style.format({
                            "Yes Ask": "${:,.3f}",
                            "Last Price": "${:,.3f}",
                            "Volume (24h)": "${:,.0f}",
                            "Total Volume": "${:,.0f}",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    # Kalshi formatting - full
                    st.dataframe(
                        df_search_display.style.format({
                            "Yes Ask": "${:,.0f}",
                            "No Ask": "${:,.0f}",
                            "Last Price": "${:,.0f}",
                            "Volume (24h)": "${:,.0f}",
                            "Total Volume": "${:,.0f}",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.warning(f"No markets found matching '{search_term}'")
        
        # ── Explanation ─────────────────────────────────────────────────────
        with st.expander("ℹ️ About This Page", expanded=False):
            st.write(f"""
            **Purpose**: This page displays all active markets from **{data_source_display}** with comprehensive trading data.
            
            **Tables**:
            - **Top Markets by 24h Volume**: Shows the most actively traded markets in the last 24 hours
            - **Top 10 by Total Volume**: Displays markets with the highest cumulative trading volume
            - **Search Results**: Filter markets by title to find specific events
            
            **Data Source**: Live market data from {data_source_display}, updated in real-time.
            
            **Clickable Elements**: 
            - Click any **ticker** to view detailed analytics on the Overview page
            - Click any **title** to view detailed analytics on the Overview page
            
            **Volume Data**: 
            - **24h Volume**: Trading volume in the last 24 hours
            - **Total Volume**: Cumulative trading volume since market creation
            
            **Price Data**:
            - **Yes Bid/Ask**: Current bid and ask prices for "Yes" outcome
            - **No Bid/Ask**: Current bid and ask prices for "No" outcome (Kalshi only)
            - **Last Price**: Most recent trade price
            
            **Data Source Differences**:
            - **Kalshi**: Full binary market structure with Yes/No bid/ask prices
            - **Polymarket**: Simplified structure with outcomes array and Yes bid/ask prices
            """)

if __name__ == "__main__":
    main()