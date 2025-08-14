# pages/Markets.py

import streamlit as st
import pandas as pd
import numpy as np
from utils import load_active_markets_from_store, get_events_to_series_mapping, get_volume_columns, make_ticker_clickable, make_title_clickable
import duckdb
import urllib.parse
import os

def main():
    st.set_page_config(page_title="Markets", layout="wide")
    st.title("📊 Markets")
    
    st.markdown("""
    This page shows all active Kalshi markets with their current prices, volumes, and trading activity.
    Click the 🔎 icon in any row to open its chart on the Overview page.
    """)
    
    # ── Load Data ───────────────────────────────────────────────────────────
    with st.spinner("Loading market data..."):
        # Load active markets from cache
        df = load_active_markets_from_store()
        
        if df.empty:
            st.error("Could not load markets data. Please check your API connection.")
            return
        
        # Get volume columns
        vol24_series, total_vol_series = get_volume_columns(df)
        
        # No custom CSS – rely on st.dataframe for consistent gridlines
        
        # ── Top Markets by 24h Volume ───────────────────────────────────────
        # Get top markets by 24h volume
        n = 20  # Show top 20 markets
        
        # Sort by 24h volume and get top N
        df_sorted = df.assign(_vol24=vol24_series).sort_values("_vol24", ascending=False).head(n)
        df_top = df_sorted.drop(columns=["_vol24"])
        
        # Get volume columns for top markets
        vol24_top = vol24_series.loc[df_top.index]
        total_vol_top = total_vol_series.loc[df_top.index]

        st.subheader(f"Top {n} Markets by 24h Volume")
        df_top_display = pd.DataFrame({
            "Series":        df_top.get("Series", pd.Series(index=df_top.index, dtype=object)),
            "Title":         df_top.get("title"),
            "Ticker":        df_top.get("ticker"),
            "Yes Bid":       df_top.get("yes_bid"),
            "Yes Ask":       df_top.get("yes_ask"),
            "No Bid":        df_top.get("no_bid"),
            "No Ask":        df_top.get("no_ask"),
            "Last Price":    df_top.get("last_price"),
            "Volume (24h)":  vol24_top,
            "Total Volume":  total_vol_top,
            "Close Time":    df_top.get("close_time"),
        })
        # Truncate long titles to single-line friendly length
        if "Title" in df_top_display.columns:
            titles = df_top_display["Title"].astype(str)
            df_top_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
        # Link column to Overview page via query params (relative link)
        # Replace link with an in-tab action button style column using Streamlit's button grid
        # We still show a placeholder text in the DataFrame for consistent layout
        df_top_display.insert(0, "🔎", "click")
        # Back to pure dataframe view (no per-row icons)
        df_top_display = df_top_display[["Series", "Title", "Ticker", "Yes Bid", "Yes Ask", "No Bid", "No Ask", "Last Price", "Volume (24h)", "Total Volume", "Close Time"]]
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
        
        # ── Summary Table (Top 10 by Total Volume - auto-displayed) ─────────────────
        st.subheader("Top 10 Active Markets by Total Volume")
        # Build summary directly from raw df, sort by Total Volume, show top 10
        vol24_sum, total_vol_sum = get_volume_columns(df)
        df_sum = pd.DataFrame({
            "Series":        df.get("Series", pd.Series(index=df.index, dtype=object)),
            "Title":         df.get("title"),
            "Ticker":        df.get("ticker"),
            "Yes Subtitle":  df.get("yes_sub_title"),
            "No Subtitle":   df.get("no_sub_title"),
            "Yes Ask":       df.get("yes_ask"),
            "No Ask":        df.get("no_ask"),
            "Last Price":    df.get("last_price"),
            "Volume (24h)":  vol24_sum,
            "Total Volume":  total_vol_sum,
            "Close Time":    df.get("close_time"),
        })
        # Sort by Total Volume descending and show top 10
        df_sum = df_sum.assign(_total_vol=df_sum["Total Volume"].fillna(0)).sort_values("_total_vol", ascending=False).head(10).drop(columns=["_total_vol"])
        # Add link icon column and truncate titles
        df_sum_display = df_sum.copy()
        if "Title" in df_sum_display.columns:
            titles = df_sum_display["Title"].astype(str)
            df_sum_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
        df_sum_display.insert(0, "🔎", "click")
        df_sum_display = df_sum_display[["Series", "Title", "Ticker", "Yes Subtitle", "No Subtitle", "Yes Ask", "No Ask", "Last Price", "Volume (24h)", "Total Volume", "Close Time"]]
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
            filt = df["title"].str.contains(search_term, case=False, na=False)
            df_search = df.loc[filt]
            
            if not df_search.empty:
                st.success(f"Found {len(df_search)} markets matching '{search_term}'")
                # Build display df
                df_search_display = pd.DataFrame({
                    "Series":        df_search.get("Series", pd.Series(index=df_search.index, dtype=object)),
                    "Title":         df_search.get("title"),
                    "Ticker":        df_search.get("ticker"),
                    "Yes Ask":       df_search.get("yes_ask"),
                    "No Ask":        df_search.get("no_ask"),
                    "Last Price":    df_search.get("last_price"),
                    "Volume (24h)":  vol24_series.loc[df_search.index],
                    "Total Volume":  total_vol_series.loc[df_search.index],
                })
                # Truncate titles and add link icon column
                if "Title" in df_search_display.columns:
                    titles = df_search_display["Title"].astype(str)
                    df_search_display["Title"] = np.where(titles.str.len() > 60, titles.str.slice(0, 57) + "...", titles)
                df_search_display.insert(0, "🔎", "click")
                df_search_display = df_search_display[["Series", "Title", "Ticker", "Yes Ask", "No Ask", "Last Price", "Volume (24h)", "Total Volume"]]
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
            st.write("""
            **Purpose**: This page displays all active Kalshi markets with comprehensive trading data.
            
            **Tables**:
            - **Top Markets by 24h Volume**: Shows the most actively traded markets in the last 24 hours
            - **Top 10 by Total Volume**: Displays markets with the highest cumulative trading volume
            - **Search Results**: Filter markets by title to find specific events
            
            **Data Source**: Live market data from Kalshi API, updated in real-time.
            
            **Clickable Elements**: 
            - Click any **ticker** to view detailed analytics on the Overview page
            - Click any **title** to view detailed analytics on the Overview page
            
            **Volume Data**: 
            - **24h Volume**: Trading volume in the last 24 hours
            - **Total Volume**: Cumulative trading volume since market creation
            
            **Price Data**:
            - **Yes Bid/Ask**: Current bid and ask prices for "Yes" outcome
            - **No Bid/Ask**: Current bid and ask prices for "No" outcome
            - **Last Price**: Most recent trade price
            """)

if __name__ == "__main__":
    main()