#!/usr/bin/env python3
"""Test script to verify Kalshi portfolio access"""

try:
    from utils import get_client
    print("✓ Successfully imported utils and get_client")
    
    client = get_client()
    print("✓ Successfully created Kalshi client")
    
    print("\n--- Testing Portfolio Balance ---")
    balance = client.get_portfolio_balance()
    print(f"Balance data: {balance}")
    
    print("\n--- Testing Portfolio Positions ---")
    positions = client.get_portfolio_positions()
    print(f"Positions count: {len(positions) if positions else 0}")
    if positions:
        print("Sample position:", positions.iloc[0].to_dict() if len(positions) > 0 else "No positions")
    
    print("\n--- Testing Portfolio Orders ---")
    orders = client.get_portfolio_orders()
    print(f"Orders count: {len(orders) if orders else 0}")
    
    print("\n🎉 Portfolio access successful! All endpoints working.")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
