# pages/JKB.py

import streamlit as st
import pandas as pd
import datetime
import altair as alt
from requests.exceptions import HTTPError
import os
import duckdb
from datetime import datetime, timedelta

# Import helper to fix path issues
import import_helper

from utils import get_client, load_active_markets_from_store, load_candles_from_store, has_portfolio_auth, get_auth_status
from kalshi_client import KalshiClient



def get_portfolio_balance(client) -> dict:
    """Get the user's portfolio balance from Kalshi API"""
    try:
        response = client.get_portfolio_balance()
        if response and 'balance' in response:
            return {
                'balance_cents': response['balance'],
                'balance_dollars': response['balance'] / 100,
                'timestamp': datetime.now()
            }
        return None
    except Exception as e:
        st.error(f"Error fetching balance: {str(e)}")
        return None

def get_portfolio_positions(client) -> pd.DataFrame:
    """Get the user's portfolio positions from Kalshi API"""
    try:
        positions = []
        cursor = None
        
        while True:
            params = {'limit': 100}
            if cursor:
                params['cursor'] = cursor
                
            response = client.get_portfolio_positions(**params)
            
            if not response or 'market_positions' not in response:
                break
                
            for position in response['market_positions']:
                positions.append({
                    'ticker': position.get('ticker', ''),
                    'position': position.get('position', 0),
                    'total_traded': position.get('total_traded', 0),
                    'total_traded_dollars': position.get('total_traded', 0) / 100,
                    'realized_pnl': position.get('realized_pnl', 0),
                    'realized_pnl_dollars': position.get('realized_pnl', 0) / 100,
                    'fees_paid': position.get('fees_paid', 0),
                    'fees_paid_dollars': position.get('fees_paid', 0) / 100,
                    'resting_orders_count': position.get('resting_orders_count', 0),
                    'last_updated': datetime.now()
                })
            
            cursor = response.get('cursor')
            if not cursor:
                break
        
        return pd.DataFrame(positions)
    except Exception as e:
        st.error(f"Error fetching positions: {str(e)}")
        return pd.DataFrame()

def get_portfolio_fills(client) -> pd.DataFrame:
    """Get historical fills data for portfolio value calculation"""
    try:
        # Try the client method first
        if hasattr(client, 'get_portfolio_fills'):
            fills = []
            cursor = None
            
            while True:
                params = {'limit': 100}
                if cursor:
                    params['cursor'] = cursor
                    
                response = client.get_portfolio_fills(**params)
                
                if not response or 'fills' not in response:
                    break
                    
                for fill in response['fills']:
                    fills.append({
                        'trade_id': fill.get('trade_id', ''),
                        'market_ticker': fill.get('ticker', ''),  # Changed from 'market_ticker' to 'ticker'
                        'side': fill.get('side', ''),
                        'yes_price': fill.get('yes_price', 0),
                        'no_price': fill.get('no_price', 0),
                        'count': fill.get('count', 0),
                        'action': fill.get('action', ''),
                        'created_time': fill.get('created_time', 0),  # Changed from 'ts' to 'created_time'
                        'is_taker': fill.get('is_taker', False)
                    })
                
                cursor = response.get('cursor')
                if not cursor:
                    break
            
            return pd.DataFrame(fills)
        else:
            # Fallback: try to make the API call directly
            st.warning("Client method not found, trying direct API call...")
            try:
                # Try to make a direct request to the fills endpoint
                import requests
                
                # Get the base URL from the client
                base_url = getattr(client, 'base_url', 'https://api.elections.kalshi.com')
                
                # Try to get headers from the client
                if hasattr(client, '_sign_request'):
                    headers = client._sign_request("GET", "/trade-api/v2/portfolio/fills")
                else:
                    headers = {}
                
                response = requests.get(f"{base_url}/trade-api/v2/portfolio/fills", 
                                     params={'limit': 100}, 
                                     headers=headers, 
                                     timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'fills' in data:
                        fills = []
                        for fill in data['fills']:
                            fills.append({
                                'trade_id': fill.get('trade_id', ''),
                                'market_ticker': fill.get('ticker', ''),
                                'side': fill.get('side', ''),
                                'yes_price': fill.get('yes_price', 0),
                                'no_price': fill.get('no_price', 0),
                                'count': fill.get('count', 0),
                                'action': fill.get('action', ''),
                                'created_time': fill.get('created_time', 0),
                                'is_taker': fill.get('is_taker', False)
                            })
                        st.success("Successfully fetched fills data via direct API call!")
                        return pd.DataFrame(fills)
                    else:
                        st.warning("No fills data in response")
                        return pd.DataFrame()
                else:
                    st.error(f"Direct API call failed with status {response.status_code}")
                    return pd.DataFrame()
                    
            except Exception as e:
                st.error(f"Direct API call also failed: {str(e)}")
                return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching fills: {str(e)}")
        return pd.DataFrame()

def get_portfolio_orders(client) -> pd.DataFrame:
    """Get the user's portfolio orders from Kalshi API"""
    try:
        orders = []
        cursor = None
        
        while True:
            params = {'limit': 100}
            if cursor:
                params['cursor'] = cursor
                
            response = client.get_portfolio_orders(**params)
            
            if not response or 'orders' not in response:
                break
                
            for order in response['orders']:
                # Fix the integer conversion issue
                try:
                    yes_price = int(order.get('yes_price', 0)) if order.get('yes_price') is not None else 0
                    no_price = int(order.get('no_price', 0)) if order.get('no_price') is not None else 0
                    initial_count = int(order.get('initial_count', 0)) if order.get('initial_count') is not None else 0
                    fill_count = int(order.get('fill_count', 0)) if order.get('fill_count') is not None else 0
                    remaining_count = int(order.get('remaining_count', 0)) if order.get('remaining_count') is not None else 0
                    created_time = int(order.get('created_time', 0)) if order.get('created_time') is not None else 0
                except (ValueError, TypeError):
                    # Skip orders with invalid data
                    continue
                
                orders.append({
                    'ticker': order.get('ticker', ''),
                    'side': order.get('side', ''),
                    'action': order.get('action', ''),
                    'type': order.get('type', ''),
                    'yes_price': yes_price,
                    'yes_price_dollars': yes_price / 100,
                    'no_price': no_price,
                    'no_price_dollars': no_price / 100,
                    'initial_count': initial_count,
                    'fill_count': fill_count,
                    'remaining_count': remaining_count,
                    'status': order.get('status', ''),
                    'created_time': datetime.fromtimestamp(created_time) if created_time > 0 else None
                })
            
            cursor = response.get('cursor')
            if not cursor:
                break
        
        return pd.DataFrame(orders)
    except Exception as e:
        st.error(f"Error fetching orders: {str(e)}")
        return pd.DataFrame()

def calculate_position_pnl(positions_df: pd.DataFrame, markets_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate unrealized PnL for positions based on current market prices"""
    if positions_df.empty or markets_df.empty:
        return positions_df
    
    # Merge positions with current market data
    merged = positions_df.merge(
        markets_df[['ticker', 'last_price', 'yes_ask', 'no_ask']], 
        on='ticker', 
        how='left'
    )
    
    def calculate_unrealized_pnl(row):
        """Calculate unrealized PnL based on current market prices"""
        if pd.isna(row['last_price']):
            return 0
        
        position = row['position']
        if position == 0:
            return 0
        
        # For YES positions (positive), calculate PnL based on current YES price
        if position > 0:
            # Assume average entry price from total_traded
            if row['total_traded'] > 0:
                avg_entry_price = row['total_traded_dollars'] / abs(position)
                current_price = row['last_price'] / 100  # Convert from cents
                return (current_price - avg_entry_price) * abs(position)
        
        # For NO positions (negative), calculate PnL based on current NO price
        elif position < 0:
            if row['total_traded'] > 0:
                avg_entry_price = row['total_traded_dollars'] / abs(position)
                current_price = (100 - row['last_price']) / 100  # Convert from cents and flip for NO
                return (current_price - avg_entry_price) * abs(position)
        
        return 0
    
    # Calculate unrealized PnL
    merged['unrealized_pnl_dollars'] = merged.apply(calculate_unrealized_pnl, axis=1)
    merged['total_pnl_dollars'] = merged['realized_pnl_dollars'] + merged['unrealized_pnl_dollars']
    
    return merged

def calculate_current_position_value(positions_df: pd.DataFrame, markets_df: pd.DataFrame) -> float:
    """Calculate current value of all positions based on current market prices"""
    if positions_df.empty or markets_df.empty:
        return 0.0
    
    # Calculate current position value
    total_position_value = 0.0
    
    # Merge positions with current market data
    merged = positions_df.merge(
        markets_df[['ticker', 'last_price']], 
        on='ticker', 
        how='left'
    )
    
    for _, row in merged.iterrows():
        if pd.isna(row['last_price']):
            continue
            
        position = row['position']
        if position == 0:
            continue
            
        current_price = row['last_price'] / 100  # Convert from cents
        
        if position > 0:  # YES position
            total_position_value += abs(position) * current_price
        else:  # NO position
            total_position_value += abs(position) * (1 - current_price)
    
    return total_position_value



def create_portfolio_pnl_chart(positions_df: pd.DataFrame, balance_data: dict, markets_df: pd.DataFrame) -> alt.Chart:
    """Create a modern, high-tech bubble chart showing total PnL and position size"""
    if not balance_data:
        return None
    
    # Calculate total PnL and position data
    position_data = []
    total_pnl = 0.0
    
    if not positions_df.empty:
        for _, row in positions_df.iterrows():
            if row['position'] == 0:
                continue
                
            # Use the existing total PnL that was already calculated
            total_pnl_dollars = row.get('total_pnl_dollars', 0)
            total_pnl += total_pnl_dollars
            
            # Use total_traded_dollars for bubble size (represents position value)
            position_value = row.get('total_traded_dollars', 0)
            
            # Create a clean label
            position_direction = 'YES' if row['position'] > 0 else 'NO'
            position_size = abs(row['position'])
            label = f"{row['ticker']}\n({position_direction}, {position_size})"
            
            # Determine color based on PnL
            if total_pnl_dollars > 0:
                color = '#10b981'  # Green for profitable
            elif total_pnl_dollars < 0:
                color = '#ef4444'  # Red for loss
            else:
                color = '#6b7280'  # Gray for neutral
            
            position_data.append({
                'label': label,
                'total_pnl': total_pnl_dollars,
                'position_value': position_value,
                'position_size': position_size,
                'direction': position_direction,
                'color': color
            })
    
    # Remove aggregate bubble - just show individual positions
    
    if not position_data:
        return None
    
    # Create the modern bubble chart
    chart = alt.Chart(pd.DataFrame(position_data)).mark_circle(
        size=100,
        stroke='#ffffff',
        strokeWidth=2
    ).encode(
        x=alt.X('total_pnl:Q', 
                title='Total PnL ($)',
                scale=alt.Scale(domain=[
                    min([p['total_pnl'] for p in position_data]) - 5, 
                    max([p['total_pnl'] for p in position_data]) + 5
                ])),
        y=alt.Y('position_value:Q', 
                title='Position Value ($)',
                scale=alt.Scale(domain=[
                    0, 
                    max([p['position_value'] for p in position_data]) * 1.2
                ])),
        size=alt.Size('position_value:Q', 
                     title='Position Value ($)',
                     scale=alt.Scale(range=[100, 800])),
        color=alt.Color('color:N', scale=None),
        tooltip=[
            alt.Tooltip('label:N', title='Position'),
            alt.Tooltip('total_pnl:Q', title='Total PnL', format='$,.2f'),
            alt.Tooltip('position_value:Q', title='Position Value', format='$,.2f'),
            alt.Tooltip('position_size:Q', title='Contracts'),
            alt.Tooltip('direction:N', title='Side')
        ]
    ).properties(
        title={
            'text': 'Portfolio Performance',
            'fontSize': 20,
            'fontWeight': 'bold',
            'align': 'center',
            'color': '#1f2937'
        },
        height=400  # Match the height of portfolio summary table
    ).configure_view(
        strokeWidth=0,
        fill='#f8fafc'
    ).configure_axis(
        gridColor='#e2e8f0',
        gridOpacity=0.5,
        domainColor='#94a3b8',
        labelColor='#475569',
        titleColor='#1e293b',
        titleFontSize=16,
        titleFontWeight='bold',
        labelFontSize=12
    ).configure_title(
        fontSize=18,
        fontWeight='bold',
        color='#1f2937'
    )
    
    return chart, total_pnl

def create_portfolio_summary_table(positions_df: pd.DataFrame, balance_data: dict, markets_df: pd.DataFrame) -> pd.DataFrame:
    """Create a summary table showing key portfolio metrics"""
    if not balance_data:
        return pd.DataFrame()
    
    # Calculate current position value
    current_position_value = 0.0
    if not positions_df.empty and not markets_df.empty:
        current_position_value = calculate_current_position_value(positions_df, markets_df)
    
    # Calculate PnL metrics
    realized_pnl = 0.0
    unrealized_pnl = 0.0
    total_fees = 0.0
    if not positions_df.empty:
        positions_with_pnl = calculate_position_pnl(positions_df, markets_df)
        realized_pnl = positions_with_pnl['realized_pnl_dollars'].sum()
        unrealized_pnl = positions_with_pnl['unrealized_pnl_dollars'].sum()
        total_fees = positions_with_pnl['fees_paid_dollars'].sum()
    
    # Calculate live value
    live_value = balance_data['balance_dollars'] + current_position_value
    
    # Create summary data
    summary_data = [
        {
            'Metric': 'Portfolio Balance (Cash)',
            'Value': f"${balance_data['balance_dollars']:,.2f}"
        },
        {
            'Metric': 'Realized PnL',
            'Value': f"${realized_pnl:,.2f}"
        },
        {
            'Metric': 'Unrealized PnL',
            'Value': f"${unrealized_pnl:,.2f}"
        },
        {
            'Metric': 'Value of Current Positions',
            'Value': f"${current_position_value:,.2f}"
        },
        {
            'Metric': 'Total Fees Paid',
            'Value': f"${total_fees:,.2f}"
        },
        {
            'Metric': 'Live Value',
            'Value': f"${live_value:,.2f}"
        }
    ]
    
    return pd.DataFrame(summary_data)

def create_recent_fills_table(fills_df: pd.DataFrame) -> pd.DataFrame:
    """Create a table showing the 10 most recent fills"""
    if fills_df.empty:
        return pd.DataFrame()
    
    # Sort by created_time descending and take top 10
    recent_fills = fills_df.copy()
    
    # Use timestamp parsing if date column doesn't exist
    if 'date' not in recent_fills.columns:
        recent_fills['date'] = pd.to_datetime(recent_fills['created_time'])
    
    recent_fills = recent_fills.sort_values('date', ascending=False).head(10)
    
    # Format the data for display - handle missing columns gracefully
    available_columns = recent_fills.columns.tolist()
    
    # Create a safe display dataframe with available columns
    display_fills = recent_fills.copy()
    
    # Add dollar price columns if the original price columns exist
    if 'yes_price' in available_columns:
        display_fills['yes_price_dollars'] = display_fills['yes_price'] / 100
    if 'no_price' in available_columns:
        display_fills['no_price_dollars'] = display_fills['no_price'] / 100
    
    # Calculate fill size ($) - contracts * price
    if 'count' in available_columns and 'yes_price_dollars' in display_fills.columns and 'no_price_dollars' in display_fills.columns:
        display_fills['fill_size_dollars'] = display_fills.apply(
            lambda row: row['count'] * (row['yes_price_dollars'] if row['side'] == 'yes' else row['no_price_dollars']), 
            axis=1
        )
    
    # Select and rename columns for display, handling missing columns
    display_columns = []
    column_names = []
    
    if 'date' in available_columns:
        display_columns.append('date')
        column_names.append('Date')
    
    if 'market_ticker' in available_columns:
        display_columns.append('market_ticker')
        column_names.append('Market')
    elif 'ticker' in available_columns:
        display_columns.append('ticker')
        column_names.append('Market')
    
    if 'side' in available_columns:
        display_columns.append('side')
        column_names.append('Side')
    
    if 'action' in available_columns:
        display_columns.append('action')
        column_names.append('Action')
    
    if 'count' in available_columns:
        display_columns.append('count')
        column_names.append('Count')
    
    if 'yes_price_dollars' in display_fills.columns:
        display_columns.append('yes_price_dollars')
        column_names.append('YES Price ($)')
    
    if 'no_price_dollars' in display_fills.columns:
        display_columns.append('no_price_dollars')
        column_names.append('NO Price ($)')
    
    if 'fill_size_dollars' in display_fills.columns:
        display_columns.append('fill_size_dollars')
        column_names.append('Fill Size ($)')
    
    # Create the final display dataframe
    if display_columns:
        display_fills = display_fills[display_columns].copy()
        display_fills.columns = column_names
    else:
        # Fallback: just show what we have
        display_fills = recent_fills.head(10)
    
    return display_fills

def create_clean_positions_table(positions_df: pd.DataFrame) -> pd.DataFrame:
    """Create a clean, formatted positions table for display"""
    if positions_df.empty:
        return pd.DataFrame()
    
    # Create a clean display dataframe
    display_df = positions_df.copy()
    
    # Add position direction column
    display_df['position_direction'] = display_df['position'].apply(
        lambda x: 'YES' if x > 0 else 'NO' if x < 0 else 'Neutral'
    )
    
    # Add position size category
    display_df['position_size'] = display_df['position'].abs().apply(
        lambda x: 'Small' if x <= 10 else 'Medium' if x <= 50 else 'Large'
    )
    
    # Add PnL status (without emojis)
    display_df['pnl_status'] = display_df['total_pnl_dollars'].apply(
        lambda x: 'Profitable' if x > 0 else 'Loss' if x < 0 else 'Neutral'
    )
    
    # Reorder columns for better display
    column_order = [
        'ticker', 'position_direction', 'position', 'position_size',
        'total_traded_dollars', 'realized_pnl_dollars', 'unrealized_pnl_dollars', 
        'total_pnl_dollars', 'pnl_status', 'fees_paid_dollars', 'resting_orders_count'
    ]
    
    return display_df[column_order]

def main():
    st.set_page_config(
        page_title="JKB Portfolio Dashboard",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("JKB Portfolio Dashboard")
    st.markdown("Track your live Kalshi positions and portfolio performance")
    
    # Initialize Kalshi client
    try:
        client = get_client()
    except Exception as e:
        st.error(f"Failed to initialize Kalshi client: {str(e)}")
        st.info("Please check your API key configuration in config.py")
        return
    
    # Get portfolio data (only if we have proper credentials)
    if has_portfolio_auth():
        balance_data = get_portfolio_balance(client)
        positions_df = get_portfolio_positions(client)
        fills_df = get_portfolio_fills(client)
    else:
        balance_data = None
        positions_df = pd.DataFrame()
        fills_df = pd.DataFrame()
        with st.expander("API Key Configuration Help", expanded=True):
            st.warning("Portfolio endpoints require both API Key ID and Private Key. Public endpoints will still function.")
            status = get_auth_status()
            
            # Show detailed status
            st.write("**Authentication Status:**")
            st.json({
                "api_key_id_present": status["api_key_id_present"],
                "private_key_inline": status["private_key_inline"],
                "private_key_file": status["private_key_file"],
                "has_portfolio_auth": status["has_portfolio_auth"],
            })
            
            # Show debug information if available
            if "debug_api_key_length" in status:
                st.write("**Debug Information:**")
                st.json({
                    "API Key Length": status["debug_api_key_length"],
                    "Private Key Length": status["debug_private_key_length"],
                    "Private Key Preview": status["debug_private_key_preview"],
                    "Starts with -----BEGIN": status["debug_private_key_starts_with_begin"],
                })
            
            # Test environment variables directly
            st.write("**Environment Variable Test:**")
            import os
            api_key_env = os.getenv('KALSHI_API_KEY_ID', 'NOT_FOUND')
            private_key_env = os.getenv('KALSHI_PRIVATE_KEY', 'NOT_FOUND')
            
            st.json({
                "KALSHI_API_KEY_ID from env": f"{api_key_env[:20]}{'...' if len(api_key_env) > 20 else ''}" if api_key_env != 'NOT_FOUND' else 'NOT_FOUND',
                "KALSHI_PRIVATE_KEY from env": f"{private_key_env[:50]}{'...' if len(private_key_env) > 50 else ''}" if private_key_env != 'NOT_FOUND' else 'NOT_FOUND',
                "API Key Length (env)": len(api_key_env) if api_key_env != 'NOT_FOUND' else 0,
                "Private Key Length (env)": len(private_key_env) if private_key_env != 'NOT_FOUND' else 0,
            })
            
            st.markdown("- Set environment variables `KALSHI_API_KEY_ID` and `KALSHI_PRIVATE_KEY`, or\n- Run `python setup_api_keys.py` to create a local `config.py` (gitignored).")
    markets_df = load_active_markets_from_store()
    
    # No debug info needed - clean interface
    
    # Calculate PnL if we have data
    if not positions_df.empty and not markets_df.empty:
        positions_with_pnl = calculate_position_pnl(positions_df, markets_df)
    else:
        positions_with_pnl = positions_df
    
    # TOP SECTION: Portfolio Performance Bubble Chart (3/4 width) + Summary Table (1/4 width)
    st.write("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("Portfolio Performance")
        
        if balance_data:
            try:
                # Use positions_with_pnl instead of positions_df to get calculated PnL values
                pnl_chart_result = create_portfolio_pnl_chart(positions_with_pnl, balance_data, markets_df)
                if pnl_chart_result:
                    pnl_chart, total_pnl = pnl_chart_result
                    
                    # Display the modern PnL chart with container width
                    st.altair_chart(pnl_chart, use_container_width=True)
                    
                else:
                    st.info("No portfolio data available for performance chart")
            except Exception as e:
                st.error(f"Error creating portfolio chart: {str(e)}")
                st.info("No portfolio data available for performance chart")
        else:
            st.info("No portfolio data available for performance chart")
    
    with col2:
        st.header("Portfolio Summary")
        
        if balance_data:
            try:
                # Calculate current position value for live value calculation
                current_position_value = 0.0
                if not positions_df.empty and not markets_df.empty:
                    current_position_value = calculate_current_position_value(positions_df, markets_df)
                
                # Calculate live value
                live_value = balance_data['balance_dollars'] + current_position_value
                
                summary_table = create_portfolio_summary_table(positions_df, balance_data, markets_df)
                if not summary_table.empty:
                    # Create custom styled table with Live Value highlighted
                    st.markdown("""
                    <style>
                    .live-value-row {
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: white;
                        font-weight: bold;
                        border-radius: 8px;
                        padding: 8px;
                        margin: 4px 0;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    }
                    .metric-table {
                        border-collapse: separate;
                        border-spacing: 0;
                        border-radius: 12px;
                        overflow: hidden;
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    }
                    .metric-table th {
                        background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                        color: white;
                        padding: 16px;
                        font-weight: 600;
                        text-align: left;
                    }
                    .metric-table td {
                        padding: 16px;
                        border-bottom: 1px solid #e5e7eb;
                    }
                    .metric-table tr:last-child td {
                        border-bottom: none;
                        font-weight: bold;
                        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        color: white;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Display the table with custom styling
                    st.dataframe(
                        summary_table,
                        column_config={
                            'Metric': st.column_config.TextColumn("Metric", width="medium"),
                            'Value': st.column_config.TextColumn("Value", width="medium")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                    
                else:
                    st.warning("Summary table is empty")
            except Exception as e:
                st.error(f"Error creating summary table: {str(e)}")
        else:
            st.warning("Unable to fetch balance data")
    
    st.markdown("---")
    
    # MIDDLE SECTION: Current Positions (Full Width)
    st.header("Current Positions")
    
    if not positions_df.empty:
        # Create clean positions table
        clean_positions = create_clean_positions_table(positions_with_pnl)
        
        # Add search functionality
        search_term = st.text_input("Search by ticker:", placeholder="e.g., BIDEN-2024")
        
        if search_term:
            filtered_positions = clean_positions[
                clean_positions['ticker'].str.contains(search_term.upper(), na=False)
            ]
        else:
            filtered_positions = clean_positions
        
        # Filter out positions with zero contracts
        filtered_positions = filtered_positions[filtered_positions['position'] != 0]

        # Create color styling for PnL-based shading
        def color_pnl(val):
            if pd.isna(val):
                return ''
            # Light green for profitable, light red for loss, very light for neutral
            if val > 0:
                # Light green - very subtle
                return f'background-color: rgba(144, 238, 144, 0.15)'
            elif val < 0:
                # Light red - very subtle
                return f'background-color: rgba(255, 182, 193, 0.15)'
            else:
                # Very light gray for neutral
                return f'background-color: rgba(211, 211, 211, 0.1)'
        
        # Apply styling to the dataframe
        styled_positions = filtered_positions.style.applymap(
            color_pnl, 
            subset=['total_pnl_dollars']
        )
        
        # Display the enhanced table with styling
        st.dataframe(
            styled_positions,
            column_config={
                'ticker': st.column_config.TextColumn("Market", width="medium"),
                'position_direction': st.column_config.TextColumn("Side", width="small"),
                'position': st.column_config.NumberColumn("Contracts", width="small"),
                'position_size': st.column_config.TextColumn("Size", width="small"),
                'total_traded_dollars': st.column_config.NumberColumn("Total Traded ($)", format="$%.2f"),
                'realized_pnl_dollars': st.column_config.NumberColumn("Realized PnL ($)", format="$%.2f"),
                'unrealized_pnl_dollars': st.column_config.NumberColumn("Unrealized PnL ($)", format="$%.2f"),
                'total_pnl_dollars': st.column_config.NumberColumn("Total PnL ($)", format="$%.2f"),
                'pnl_status': st.column_config.TextColumn("Status", width="small"),
                'fees_paid_dollars': st.column_config.NumberColumn("Fees ($)", format="$%.2f"),
                'resting_orders_count': st.column_config.NumberColumn("Orders", width="small")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Add export functionality
        if not filtered_positions.empty:
            csv = filtered_positions.to_csv(index=False)
            st.download_button(
                label="Download Positions CSV",
                data=csv,
                file_name=f"kalshi_positions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No active positions found")
    
    # RECENT FILLS SECTION: Below Current Positions
    st.markdown("---")
    st.header("Recent 10 Fills")
    
    if not fills_df.empty:
        try:
            recent_fills_table = create_recent_fills_table(fills_df)
            if not recent_fills_table.empty:
                st.dataframe(
                    recent_fills_table,
                    column_config={
                        'Date': st.column_config.DatetimeColumn("Date", format="MM/DD/YY HH:mm"),
                        'Market': st.column_config.TextColumn("Market", width="medium"),
                        'Side': st.column_config.TextColumn("Side", width="small"),
                        'Action': st.column_config.TextColumn("Action", width="small"),
                        'Count': st.column_config.NumberColumn("Count", width="small"),
                        'YES Price ($)': st.column_config.NumberColumn("YES Price ($)", format="$%.2f"),
                        'NO Price ($)': st.column_config.NumberColumn("NO Price ($)", format="$%.2f"),
                        'Fill Size ($)': st.column_config.NumberColumn("Fill Size ($)", format="$%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No recent fills data to display")
        except Exception as e:
            st.error(f"Error creating recent fills table: {str(e)}")
            st.write("Raw fills data (first 5 rows):")
            st.dataframe(fills_df.head())
    else:
        st.info("No fills data available")
    
    # Add refresh button and timestamp at the bottom
    st.markdown("---")
    
    refresh_col1, refresh_col2, refresh_col3 = st.columns([1, 2, 1])
    
    with refresh_col2:
        if st.button("Refresh Data", type="primary", use_container_width=True):
            st.rerun()
    
    with refresh_col3:
        st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()
