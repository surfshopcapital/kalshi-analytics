# dashboard.py

import streamlit as st

# Global Streamlit configuration
st.set_page_config(
    page_title="Kalshi Analytics",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
# Kalshi Analytics  
Use the sidebar to navigate between pages:

- **Overview**: Market overview and summary statistics
- **Movers**: Biggest 24-hour price movers by notional move
- **Decay**: Time decay strategy for low-probability markets
- **Markets**: Explore all active markets
- **Series**: Analyze market series and trends

- **Changelog**: Track changes and updates
""")