# pages/Decay.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

def get_orderbook_liquidity(client, ticker: str, target_price_cents: int) -> float:
    """
    Get the liquidity (total contract value) available at the target price.
    
    Args:
        client: KalshiClient instance
        ticker: Market ticker
        target_price_cents: Price level to check liquidity for (in cents)
    
    Returns:
        Total notional value available at that price level (in dollars)
    """
    try:
        # Get orderbook data
        orderbook_response = client.get_market_orderbook(ticker)
        
        if not orderbook_response or 'orderbook' not in orderbook_response:
            return 0.0
        
        orderbook = orderbook_response['orderbook']
        
        # Check both YES and NO sides for the target price
        total_liquidity = 0.0
        
        # Check YES bids
        if 'yes' in orderbook:
            for price_level in orderbook['yes']:
                price, quantity = price_level[0], price_level[1]
                if price >= target_price_cents:
                    # Convert to notional dollars: (price * quantity) / 100
                    total_liquidity += (price * quantity) / 100
        
        # Check NO bids
        if 'no' in orderbook:
            for price_level in orderbook['no']:
                price, quantity = price_level[0], price_level[1]
                if price >= target_price_cents:
                    # Convert to notional dollars: (price * quantity) / 100
                    total_liquidity += (price * quantity) / 100
        
        return total_liquidity
        
    except Exception as e:
        # st.error(f"Error fetching orderbook for {ticker}: {str(e)}")
        return 0.0

def calculate_annualized_return(current_price: float, target_price: float, days_to_target: float) -> float:
    """
    Calculate annualized return for a position.
    
    Args:
        current_price: Current market price (0-1)
        target_price: Target price at expiration (0 for betting against, 1 for betting for)
        days_to_target: Days until target date
    
    Returns:
        Annualized return as percentage (capped to avoid extreme values)
    """
    if days_to_target <= 0 or current_price <= 0:
        return np.nan
    
    if target_price == 0:  # Betting against (expecting price to go to 0)
        # Return if betting NO: (1 - current_price) / current_price
        simple_return = (1 - current_price) / current_price
    else:  # Betting for (expecting price to go to 1) - HIGH PROBABILITY STRATEGY
        # Return if betting YES: (target_price - current_price) / current_price  
        simple_return = (target_price - current_price) / current_price
    
    # Cap simple return to avoid extreme annualized values
    simple_return = min(simple_return, 50.0)  # Cap at 5000% simple return
    
    # Annualize the return
    try:
        annualized_return = ((1 + simple_return) ** (365.25 / days_to_target) - 1) * 100
        # Cap annualized return to reasonable values
        annualized_return = min(annualized_return, 10000.0)  # Cap at 10,000%
        return annualized_return
    except (OverflowError, ValueError):
        return 10000.0  # Return max value for extreme cases

def parse_time_to_target(time_str) -> float:
    """Parse time string to days from now"""
    try:
        if pd.isna(time_str):
            return np.nan
        dt = pd.to_datetime(time_str, utc=True).tz_convert(None)
        now = pd.Timestamp.now()
        days_to_target = (dt - now).total_seconds() / (24 * 3600)
        return max(0.0, days_to_target)
    except:
        return np.nan

def main():
    st.set_page_config(page_title="Decay Strategy", layout="wide")
    st.title("⏰ Decay Strategy")
    
    st.markdown("""
    This page identifies markets with **high probability outcomes** (≥90¢ bids) where you can capture the final **time decay** premium.
    The strategy focuses on very likely events where you can collect the last few cents before expiration.
    
    **Strategy**: Buy shares on high-probability events (≥90¢) and hold until expiration to collect final premium.
    **Key Insight**: Time decay works in your favor on near-certain outcomes with substantial time remaining.
    **Risk**: "Sure thing" bets can still fail. The closer to 100¢, the lower the return but higher the probability.
    """)
    
    # ── Configuration ───────────────────────────────────────────────────────
    st.subheader("⚙️ Strategy Configuration")
    
    # First row of filters
    col1, col2, col3 = st.columns(3)
    
    # Second row of filters
    col4, col5, col6 = st.columns(3)
    
    with col1:
        min_bid_price = st.number_input(
            "Minimum Bid Price (¢)",
            min_value=80,
            max_value=99,
            value=90,
            step=1,
            help="Only show markets with bid prices above this threshold (high probability events)"
        )
    
    with col2:
        min_days_to_close = st.number_input(
            "Minimum Days to Close",
            min_value=0.1,
            value=2.0,
            step=0.1,
            help="Minimum time until trading closes"
        )
    
    with col3:
        min_days_to_expiration = st.number_input(
            "Minimum Days to Expiration",
            min_value=0.1,
            value=2.0,
            step=0.1,
            help="Minimum time until market actually resolves"
        )
    
    with col4:
        min_volume = st.number_input(
            "Minimum 24h Volume ($)",
            min_value=0,
            value=500,
            step=100,
            help="Minimum trading volume for liquidity"
        )
    
    with col5:
        max_rows = st.number_input(
            "Maximum Rows",
            min_value=10,
            value=50,
            step=10,
            help="Maximum number of opportunities to display"
        )
    
    with col6:
        min_annualized_return = st.number_input(
            "Minimum Annualized Return (%)",
            min_value=0,
            value=20,
            step=5,
            help="Filter for minimum expected annualized return"
        )
    

    
    # ── Load and Process Data ────────────────────────────────────────────────
    with st.spinner("Loading decay opportunities..."):
        # Load active markets
        markets_df = load_active_markets_from_store()
        
        if markets_df.empty:
            st.error("Could not load markets data.")
            return
        
        # Get volume columns
        vol24_series, total_vol_series = get_volume_columns(markets_df)
        
        # Apply basic filters
        markets_df["volume_24h"] = vol24_series
        markets_df = markets_df[markets_df["volume_24h"] >= min_volume]
        
        if markets_df.empty:
            st.warning(f"No markets meet the volume requirement (≥${min_volume:,}).")
            return
        
        # Use ask prices for actual trading opportunities (what you'd pay to enter)
        markets_df["yes_ask_cents"] = markets_df["yes_ask"]
        markets_df["no_ask_cents"] = markets_df["no_ask"]
        
        # Filter for HIGH probability markets (≥90¢ asks) - decay strategy on likely outcomes
        # Note: We use ask prices since that's what you'd actually pay to enter the position
        high_prob_filter = (markets_df["yes_ask_cents"] >= min_bid_price) | (markets_df["no_ask_cents"] >= min_bid_price)
        markets_df = markets_df[high_prob_filter]
        
        if markets_df.empty:
            st.warning(f"No markets have bid prices ≥ {min_bid_price}¢.")
            return
        
        # Calculate time to close and expiration
        markets_df["days_to_close"] = markets_df["close_time"].apply(parse_time_to_target)
        markets_df["days_to_expiration"] = markets_df["expiration_time"].apply(parse_time_to_target)
        
        # Apply time filters
        time_filter = (
            (markets_df["days_to_close"] >= min_days_to_close) &
            (markets_df["days_to_expiration"] >= min_days_to_expiration)
        )
        markets_df = markets_df[time_filter]
        
        if markets_df.empty:
            st.warning("No markets meet the time requirements.")
            return
        
        # Calculate annualized returns using ask prices for HIGH probability events
        markets_df["yes_price_decimal"] = markets_df["yes_ask_cents"] / 100
        markets_df["no_price_decimal"] = markets_df["no_ask_cents"] / 100
        
        # For high-probability decay strategy: choose the HIGHER price option (≥90¢)
        # We want to bet ON the likely outcome and collect the final premium
        markets_df["best_strategy_price"] = np.maximum(markets_df["yes_price_decimal"], markets_df["no_price_decimal"])
        
        # Filter to only include markets where the best price is actually ≥ min_bid_price
        min_price_decimal = min_bid_price / 100
        markets_df = markets_df[markets_df["best_strategy_price"] >= min_price_decimal]
        
        if markets_df.empty:
            st.warning(f"No markets have prices ≥ {min_bid_price}¢ after filtering.")
            return
        
        # Annualized return to close (when you can exit)
        # For high-probability events: return = (100¢ - current_price) / current_price
        markets_df["annualized_return_to_close"] = markets_df.apply(
            lambda row: calculate_annualized_return(
                current_price=row["best_strategy_price"],
                target_price=1.0,  # Betting FOR - expecting 100¢
                days_to_target=row["days_to_close"]
            ), axis=1
        )
        
        # Annualized return to expiration (full hold)
        markets_df["annualized_return_to_expiration"] = markets_df.apply(
            lambda row: calculate_annualized_return(
                current_price=row["best_strategy_price"],
                target_price=1.0,  # Betting FOR - expecting 100¢
                days_to_target=row["days_to_expiration"]
            ), axis=1
        )
        
        # Round returns to 3 decimal places to avoid precision issues
        markets_df["annualized_return_to_close"] = markets_df["annualized_return_to_close"].round(3)
        markets_df["annualized_return_to_expiration"] = markets_df["annualized_return_to_expiration"].round(3)
        
        # Filter by minimum annualized return
        return_filter = markets_df["annualized_return_to_close"] >= min_annualized_return
        markets_df = markets_df[return_filter]
        
        if markets_df.empty:
            st.warning(f"No opportunities meet the minimum return requirement (≥{min_annualized_return}%).")
            return
        
        # Sort by annualized return to close (descending)
        markets_df = markets_df.sort_values("annualized_return_to_close", ascending=False)
        
        # Limit results
        markets_df = markets_df.head(max_rows)
        
        # Determine which side corresponds to the best_strategy_price
        # We need to know which side (YES or NO) has the higher ask price
        markets_df["best_side"] = np.where(
            markets_df["yes_ask_cents"] >= markets_df["no_ask_cents"],
            "yes",
            "no"
        )
        
        # Use the current ask price from the best side
        markets_df["current_ask_cents"] = np.where(
            markets_df["best_side"] == "yes",
            markets_df["yes_ask_cents"],
            markets_df["no_ask_cents"]
        )
    
    # ── Display Results ──────────────────────────────────────────────────────
    st.subheader(f"🎯 Top Decay Opportunities ({len(markets_df)} found)")
    
    # Summary metrics
    if not markets_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_return = markets_df["annualized_return_to_close"].mean()
            st.metric("Avg Annualized Return", f"{avg_return:.1f}%")
        
        with col2:
            avg_price = markets_df["best_strategy_price"].mean() * 100
            st.metric("Avg Best Price", f"{avg_price:.1f}¢")
        
        with col3:
            avg_days = markets_df["days_to_close"].mean()
            st.metric("Avg Days to Close", f"{avg_days:.1f}")
        
        with col4:
            total_volume = markets_df["volume_24h"].sum()
            st.metric("Total 24h Volume", f"${total_volume:,.0f}")
    
    # Prepare display dataframe
    display_df = pd.DataFrame({
        "Ticker": markets_df["ticker"],
        "Title": markets_df["title"],
        "YES Ask (¢)": markets_df["yes_ask_cents"].round(1),
        "NO Ask (¢)": markets_df["no_ask_cents"].round(1),
        "Best Ask (¢)": markets_df["current_ask_cents"].round(1),
        "Days to Close": markets_df["days_to_close"].round(1),
        "Days to Expiration": markets_df["days_to_expiration"].round(1),
        "Annual Return to Close (%)": markets_df["annualized_return_to_close"].round(3),
        "Annual Return to Expiration (%)": markets_df["annualized_return_to_expiration"].round(3),
        "24h Volume ($)": markets_df["volume_24h"].round(0)
    })
    
    # Display the table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Title": st.column_config.TextColumn(width="large"),
            "YES Ask (¢)": st.column_config.NumberColumn(format="%.1f¢"),
            "NO Ask (¢)": st.column_config.NumberColumn(format="%.1f¢"),
            "Best Ask (¢)": st.column_config.NumberColumn(format="%.1f¢"),
            "Days to Close": st.column_config.NumberColumn(format="%.1f"),
            "Days to Expiration": st.column_config.NumberColumn(format="%.1f"),
            "Annual Return to Close (%)": st.column_config.NumberColumn(format="%.3f%%"),
            "Annual Return to Expiration (%)": st.column_config.NumberColumn(format="%.3f%%"),
            "24h Volume ($)": st.column_config.NumberColumn(format="$%.0f")
        }
    )
    


if __name__ == "__main__":
    main()
