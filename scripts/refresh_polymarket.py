#!/usr/bin/env python3
"""
Refresh script for Polymarket data
Fetches and stores Polymarket markets in parquet format
"""

import os
import sys

# ── Add project root to path so we can import modules ─────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

import pandas as pd
import duckdb
from polymarket_client import fetch_and_normalize_polymarket_markets

# ── Data file paths ─────────────────────────────────────────────
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

POLYMARKET_MARKETS_PQ = os.path.join(DATA_DIR, "polymarket_markets.parquet")
POLYMARKET_SUMMARY_PQ = os.path.join(DATA_DIR, "polymarket_summary.parquet")

def refresh_polymarket_markets(min_volume: float = 0.0):
    """
    Refresh Polymarket markets data, fetching only ACTIVE markets.
    
    Args:
        min_volume: Minimum volume threshold (default: 0 to get all active markets)
    """
    print("🔄 Refreshing Polymarket ACTIVE markets data...")
    
    try:
        # Fetch only active markets (not closed ones)
        markets = fetch_and_normalize_polymarket_markets(active_only=True, min_volume=min_volume)
        
        if markets.empty:
            print("❌ No active Polymarket markets found")
            return
        
        print(f"✅ Successfully fetched {len(markets)} ACTIVE Polymarket markets")
        
        # Save to parquet
        markets.to_parquet(POLYMARKET_MARKETS_PQ, index=False)
        print(f"💾 Saved {len(markets)} active markets to {POLYMARKET_MARKETS_PQ}")
        
        # Create summary
        summary = create_polymarket_summary(markets)
        summary.to_parquet(POLYMARKET_SUMMARY_PQ, index=False)
        print(f"💾 Saved summary to {POLYMARKET_SUMMARY_PQ}")
        
        print("🎉 Polymarket ACTIVE markets refresh complete!")
        
    except Exception as e:
        print(f"❌ Error refreshing Polymarket markets: {e}")
        import traceback
        traceback.print_exc()

def create_polymarket_summary(df_markets: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary table for Polymarket markets.
    
    Args:
        df_markets: DataFrame with Polymarket markets
        
    Returns:
        Summary DataFrame
    """
    print("📋 Creating Polymarket summary table...")
    
    if df_markets.empty:
        print("❌ No markets to summarize")
        return pd.DataFrame()
    
    try:
        # Create summary with key fields
        df_summary = df_markets.copy()
        
        # Sort by volume
        df_summary = df_summary.sort_values('volume_total', ascending=False)
        
        # Select and rename key columns
        df_summary = df_summary.rename(columns={
            'title': 'Title',
            'category': 'Category',
            'outcomes': 'Outcomes',
            'last_price': 'Last Price',
            'yes_bid': 'Yes Bid',
            'yes_ask': 'Yes Ask',
            'volume_total': 'Total Volume',
            'volume_24h': 'Volume (24h)',
            'liquidity': 'Liquidity',
            'close_time': 'Close Time',
            'status': 'Status',
        })[[
            'Title', 'Category', 'Outcomes', 'Last Price', 'Yes Bid', 'Yes Ask',
            'Total Volume', 'Volume (24h)', 'Liquidity', 'Close Time', 'Status'
        ]]
        
        # Store summary
        duckdb.from_df(df_summary).to_parquet(POLYMARKET_SUMMARY_PQ, compression="snappy")
        print(f"✅ Created summary with {len(df_summary)} markets")
        
        return df_summary
        
    except Exception as e:
        print(f"❌ Error creating summary: {e}")
        return pd.DataFrame()

def analyze_polymarket_data(df_markets: pd.DataFrame):
    """
    Analyze the fetched Polymarket data.
    
    Args:
        df_markets: DataFrame with Polymarket markets
    """
    if df_markets.empty:
        print("❌ No data to analyze")
        return
    
    print("\n📊 Polymarket Data Analysis")
    print("=" * 50)
    
    # Basic stats
    print(f"📈 Total Markets: {len(df_markets)}")
    print(f"📊 Active Markets: {len(df_markets[df_markets['status'] == 'open'])}")
    print(f"🔒 Closed Markets: {len(df_markets[df_markets['status'] == 'closed'])}")
    
    # Volume analysis
    total_volume = df_markets['volume_total'].sum()
    avg_volume = df_markets['volume_total'].mean()
    print(f"💰 Total Volume: ${total_volume:,.2f}")
    print(f"📊 Average Volume: ${avg_volume:,.2f}")
    
    # Category breakdown
    categories = df_markets['category'].value_counts()
    print(f"\n🏷️ Top Categories:")
    for category, count in categories.head(5).items():
        print(f"  {category}: {count} markets")
    
    # Price analysis
    active_markets = df_markets[df_markets['status'] == 'open']
    if not active_markets.empty:
        print(f"\n💹 Active Market Pricing:")
        print(f"  Average Yes Bid: ${active_markets['yes_bid'].mean():.3f}")
        print(f"  Average Yes Ask: ${active_markets['yes_ask'].mean():.3f}")
        print(f"  Average Spread: ${active_markets['spread'].mean():.3f}")

def main():
    """Main refresh function"""
    print("🚀 Polymarket Data Refresh")
    print("=" * 50)
    
    # Step 1: Refresh markets
    refresh_polymarket_markets(min_volume=1000.0)
    
    # Step 2: Create summary
    # df_summary = create_polymarket_summary(df_markets) # This line is removed as per the new_code
    
    # Step 3: Analyze data
    # analyze_polymarket_data(df_markets) # This line is removed as per the new_code
    
    print("\n" + "=" * 50)
    print("✅ Polymarket refresh completed successfully!")
    print(f"📁 Data stored in: {DATA_DIR}")
    print(f"📊 Markets: {POLYMARKET_MARKETS_PQ}")
    print(f"📋 Summary: {POLYMARKET_SUMMARY_PQ}")

if __name__ == "__main__":
    main()
