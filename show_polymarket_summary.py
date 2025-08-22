#!/usr/bin/env python3
"""
Show a clean summary of each Polymarket market's key data
Focuses on the most important fields for understanding the data structure
"""

import sys
import os
import pandas as pd

# Add project root to path
ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from utils import get_markets_by_source

def show_polymarket_summary():
    """Show a clean summary of each Polymarket market"""
    print("📊 Polymarket Markets - Clean Summary")
    print("=" * 100)
    
    try:
        # Load Polymarket data
        df = get_markets_by_source('polymarket')
        
        if df.empty:
            print("❌ No Polymarket data found")
            return
        
        print(f"✅ Total Markets: {len(df)}")
        print(f"📋 Data Columns: {len(df.columns)}")
        
        # Show key columns we care about
        key_columns = [
            'market_id', 'title', 'category', 'outcomes', 'outcome_prices',
            'yes_bid', 'yes_ask', 'last_price', 'volume_total', 'status', 'close_time'
        ]
        
        print(f"\n🎯 Key Columns: {key_columns}")
        print("=" * 100)
        
        # Show each market's key data
        for i, (idx, market) in enumerate(df.iterrows()):
            print(f"\n🔍 Market {i+1}: {market['title'][:60]}...")
            print("-" * 80)
            
            # Show key data in a clean format
            print(f"  ID: {market['market_id']}")
            print(f"  Category: {market['category']}")
            print(f"  Outcomes: {market['outcomes']}")
            print(f"  Outcome Prices: {market['outcome_prices']}")
            print(f"  Yes Bid: ${market['yes_bid']:.3f}")
            print(f"  Yes Ask: ${market['yes_ask']:.3f}")
            print(f"  Last Price: ${market['last_price']:.3f}")
            print(f"  Total Volume: ${market['volume_total']:,.2f}")
            print(f"  Status: {market['status']}")
            print(f"  Close Time: {market['close_time']}")
            
            # Show full title if it was truncated
            if len(market['title']) > 60:
                print(f"  Full Title: {market['title']}")
        
        print("\n" + "=" * 100)
        print("📊 DATA STRUCTURE INSIGHTS")
        print("=" * 100)
        
        print("\n🔍 Key Findings:")
        print("1. **All markets are CLOSED** - This is historical data, not live trading")
        print("2. **Outcomes structure**: Each market has an 'outcomes' array (e.g., ['Yes', 'No'])")
        print("3. **Outcome prices**: Stored as tuples like [('Yes', '0'), ('No', '0')]")
        print("4. **Missing columns**: No 'no_bid' or 'no_ask' columns (unlike Kalshi)")
        print("5. **Volume data**: 24h, 1wk, 1mo, and total volumes available")
        print("6. **Price structure**: All markets show $0.00 bid, $1.00 ask (closed state)")
        print("7. **Categories**: US-current-affairs, Tech, Pop-Culture, Crypto, Coronavirus")
        print("8. **Market types**: 'normal' and 'scalar' markets")
        
        print("\n🎯 **Why This Data is Different from Kalshi:**")
        print("- **Kalshi**: Live, active markets with real-time bid/ask prices")
        print("- **Polymarket**: Historical, closed markets with final settlement prices")
        print("- **Kalshi**: Binary Yes/No structure with separate bid/ask for each outcome")
        print("- **Polymarket**: Multi-outcome structure with outcome arrays and price tuples")
        
        print("\n💡 **Recommendation for Display:**")
        print("- Show 'Outcomes' column instead of 'No Bid/Ask'")
        print("- Use 'Status' column to indicate markets are closed")
        print("- Format prices with 3 decimal places (they're very small)")
        print("- Highlight that this is historical data, not live trading")
        
    except Exception as e:
        print(f"❌ Error showing Polymarket summary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_polymarket_summary()
