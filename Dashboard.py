# dashboard.py

import streamlit as st
from shared_sidebar import render_shared_sidebar, get_selected_data_sources, get_selected_data_source_display

# Global Streamlit configuration
st.set_page_config(
    page_title="Market Analytics Dashboard",
    page_icon="📈",
    layout="wide",
)

# ── Render Shared Sidebar ─────────────────────────────────────────────
render_shared_sidebar()

# ── Main Dashboard Content ─────────────────────────────────────────────
st.markdown("""
# 📊 Market Analytics Dashboard

Welcome to your unified market analytics platform! This dashboard now supports multiple data sources:

""")

# Get selected data sources
selected_sources = get_selected_data_sources()
data_source_display = get_selected_data_source_display()

# Show selected data sources
if selected_sources:
    sources_text = ", ".join([s.capitalize() for s in selected_sources])
    st.success(f"✅ **Active Data Sources**: {sources_text}")
    
    # TEMPORARY: Don't show market count until we can fix the utils import
    st.info(f"📊 **Data Source**: {data_source_display}")
else:
    st.warning("⚠️ Please select at least one data source from the sidebar")

st.markdown("""
## 🧭 Navigation

Use the sidebar to navigate between pages:

- **Overview**: Market overview and summary statistics
- **Movers**: Biggest 24-hour price movers by notional move  
- **Decay**: Time decay strategy for low-probability markets
- **Markets**: Explore all active markets
- **Series**: Analyze market series and trends
- **Changelog**: Track changes and updates

## 🔄 Data Management

- **Kalshi Data**: Traditional prediction markets
- **Polymarket Data**: Blockchain-based prediction markets
- **Unified View**: Combined analysis across all sources

## 📈 Getting Started

1. Select your preferred data sources from the sidebar
2. Navigate to any page to start analyzing markets
3. Use the unified data view to compare across sources
4. Refresh data regularly using the provided scripts

---

*Data is automatically combined and normalized for seamless analysis across platforms.*
""")

# ── Data Source Information ─────────────────────────────────────────────
if selected_sources:
    st.markdown("## 📋 Data Source Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Kalshi Markets")
        if 'kalshi' in selected_sources:
            st.markdown("✅ **Selected** - Data will be loaded when available")
        else:
            st.markdown("❌ Not selected")
    
    with col2:
        st.markdown("### 🔗 Polymarket Markets")
        if 'polymarket' in selected_sources:
            st.markdown("✅ **Selected** - Data will be loaded when available")
        else:
            st.markdown("❌ Not selected")