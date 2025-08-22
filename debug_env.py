#!/usr/bin/env python3
"""
Debug script to test environment variable loading in Streamlit Cloud
"""

import os
import streamlit as st

st.title("Environment Variable Debug")

st.write("## Testing Environment Variables")

# Test Kalshi API Key ID
api_key_id = os.getenv('KALSHI_API_KEY_ID', 'NOT_FOUND')
st.write(f"**KALSHI_API_KEY_ID:** {api_key_id}")
st.write(f"**Length:** {len(api_key_id) if api_key_id != 'NOT_FOUND' else 0}")
if api_key_id != 'NOT_FOUND':
    st.write(f"**Preview:** {api_key_id[:20]}...")

# Test Kalshi Private Key
private_key = os.getenv('KALSHI_PRIVATE_KEY', 'NOT_FOUND')
st.write(f"**KALSHI_PRIVATE_KEY:** {private_key}")
st.write(f"**Length:** {len(private_key) if private_key != 'NOT_FOUND' else 0}")
if private_key != 'NOT_FOUND':
    st.write(f"**Preview:** {private_key[:50]}...")
    st.write(f"**Starts with -----BEGIN:** {private_key.startswith('-----BEGIN')}")

# Test all environment variables
st.write("## All Environment Variables")
all_env = {k: v for k, v in os.environ.items() if 'KALSHI' in k}
st.json(all_env)

# Test if we can access the variables through utils
try:
    from utils import get_auth_status, has_portfolio_auth
    st.write("## Utils Module Test")
    
    auth_status = get_auth_status()
    st.write("**Auth Status:**")
    st.json(auth_status)
    
    portfolio_auth = has_portfolio_auth()
    st.write(f"**Has Portfolio Auth:** {portfolio_auth}")
    
except Exception as e:
    st.error(f"Error importing utils: {e}")
    st.write("Utils module not available")
