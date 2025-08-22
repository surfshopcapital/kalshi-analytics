#!/usr/bin/env python3
"""
Print out the raw data for each Polymarket market
Shows exactly what information we're getting from the API
"""

import sys
import os
import pandas as pd
import json
import numpy as np

# Add project root to path
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from utils import get_markets_by_source

def print_polymarket_markets():
    """Print out the raw data for each Polymarket market"""
    print("🔍 Raw Polymarket Market Data")
    print("=" * 80)
    
    try:
        # Load Polymarket data
        print("📊 Loading Polymarket markets...")
        df = get_markets_by_source('polymarket')
        
        if df.empty:
            print("❌ No Polymarket data found")
            return
        
        print(f"✅ Loaded {len(df)} Polymarket markets")
        print(f"📋 Total columns: {len(df.columns)}")
        print(f"📋 Column names: {list(df.columns)}")
        
        print("\n" + "=" * 80)
        print("📊 DETAILED MARKET DATA")
        print("=" * 80)
        
        # Print each market's data
        for i, (idx, market) in enumerate(df.iterrows()):
            print(f"\n🔍 Market {i+1} (Index: {idx}):")
            print("-" * 60)
            
            # Print each column value
            for col in df.columns:
                value = market[col]
                value_type = type(value).__name__
                
                # Handle different value types safely
                if isinstance(value, (list, pd.Series, np.ndarray)):
                    if len(value) == 0:
                        print(f"  {col}: Empty {value_type}")
                    else:
                        print(f"  {col}: {value_type} with {len(value)} items")
                        print(f"    Items: {value}")
                elif isinstance(value, dict):
                    print(f"  {col}: dict with {len(value)} keys")
                    print(f"    Keys: {list(value.keys())}")
                    print(f"    Values: {value}")
                elif pd.isna(value):
                    print(f"  {col}: NULL")
                elif isinstance(value, str) and len(value) > 100:
                    print(f"  {col}: {value[:100]}... ({value_type})")
                else:
                    print(f"  {col}: {value} ({value_type})")
            
            # Add separator between markets
            if i < len(df) - 1:
                print("\n" + "─" * 60)
        
        print("\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS")
        print("=" * 80)
        
        # Show data types and null counts
        print("\n📋 Data Types:")
        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isna().sum()
            total_count = len(df)
            print(f"  {col}: {dtype} ({null_count}/{total_count} NULL)")
        
        # Show unique values for categorical columns
        print("\n📊 Unique Values for Key Columns:")
        categorical_cols = ['status', 'closed', 'category', 'market_type']
        for col in categorical_cols:
            if col in df.columns:
                unique_vals = df[col].unique()
                print(f"  {col}: {unique_vals}")
        
        # Show value ranges for numeric columns
        print("\n📊 Numeric Column Ranges:")
        numeric_cols = ['yes_bid', 'yes_ask', 'last_price', 'volume_24h', 'volume_total', 'liquidity', 'spread']
        for col in numeric_cols:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                mean_val = df[col].mean()
                print(f"  {col}: min={min_val}, max={max_val}, mean={mean_val:.3f}")
        
        print("\n" + "=" * 80)
        print("🎯 DATA STRUCTURE ANALYSIS")
        print("=" * 80)
        
        print("\n📊 Key Observations:")
        print("1. All markets appear to be CLOSED (historical data)")
        print("2. Volume data shows 24h, 1wk, 1mo, and total volumes")
        print("3. Outcomes are stored as arrays (e.g., ['Yes', 'No'])")
        print("4. Outcome prices are stored as tuples")
        print("5. No 'no_bid' or 'no_ask' columns (unlike Kalshi)")
        print("6. Market status and closure information is available")
        
    except Exception as e:
        print(f"❌ Error analyzing Polymarket data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print_polymarket_markets()
