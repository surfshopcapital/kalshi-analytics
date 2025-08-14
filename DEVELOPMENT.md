# Development Guide - Kalshi Analytics Dashboard

## 🎯 Current Project Context

This is a **Streamlit-based analytics dashboard** for Kalshi prediction markets. You're working on enhancing the UI, fixing data display issues, and optimizing performance.

### **Recent Major Work Completed**
- ✅ Fixed Series page auto-population for single subseries
- ✅ Implemented advanced filtering on Movers page (min/max days to close, min days since open)
- ✅ Resolved chart loading issues across all subseries (not just PGA Tour)
- ✅ Optimized table formatting for compact, gridlined display
- ✅ Fixed in-tab navigation between pages using session state

### **Current State**
- **Markets Page**: Clean `st.dataframe` display, no custom icons/CSS
- **Movers Page**: 5 evenly-spaced filters, proper data filtering, no verbose status messages
- **Series Page**: Auto-populating charts for single subseries, card-based UI for series selection
- **Data Layer**: DuckDB-optimized with Parquet caching, robust error handling

## 🏗️ Architecture Overview

### **Core Philosophy**
1. **Performance First**: DuckDB + Parquet for sub-second queries
2. **User Experience**: Clean, intuitive UI with consistent navigation
3. **Data Reliability**: Robust fallbacks for missing/stale data
4. **Error Resilience**: Graceful handling of API failures and data issues

### **Key Technical Patterns**

#### **Data Flow**
```python
# Standard pattern for all pages
1. Load cached data from Parquet (utils.py)
2. Apply filters and transformations
3. Display in st.dataframe with consistent formatting
4. Handle navigation via session state + st.switch_page
```

#### **Navigation Pattern**
```python
# In-tab navigation (NOT new tabs)
if st.button("View Market"):
    st.session_state.selected_ticker = ticker
    st.session_state.selected_title = title
    st.switch_page("pages/Overview.py")
```

#### **Error Handling Pattern**
```python
# Always provide fallbacks
try:
    data = load_primary_source()
except Exception:
    data = load_fallback_source()
    st.warning("Using fallback data")
```

## 🔧 Common Development Tasks

### **Adding New Filters**
```python
# 1. Add UI component
col1, col2 = st.columns(2)
with col1:
    min_value = st.number_input("Minimum Value", min_value=0, value=100)

# 2. Apply filter to DataFrame
filtered_df = df[df["column"] >= min_value]

# 3. Update caching if needed (@st.cache_data)
```

### **Adding New Charts**
```python
# Use Altair for interactive charts
chart = alt.Chart(df).mark_line().encode(
    x=alt.X("date:T", title="Date"),
    y=alt.Y("price:Q", title="Price"),
    color=alt.Color("ticker:N", title="Market")
).properties(height=400).interactive()

st.altair_chart(chart, use_container_width=True)
```

### **Debugging Data Issues**
```python
# 1. Check data existence and freshness
st.write(f"Data shape: {df.shape}")
st.write(f"Columns: {list(df.columns)}")
st.write(f"Sample data:")
st.dataframe(df.head())

# 2. Check file timestamps
import os
file_age = (pd.Timestamp.now() - pd.Timestamp.fromtimestamp(os.path.getmtime("data/active_markets.parquet"))).total_seconds() / 60
st.write(f"Data age: {file_age:.1f} minutes")

# 3. Validate data quality
st.write(f"Null values: {df.isnull().sum().sum()}")
st.write(f"Duplicate rows: {df.duplicated().sum()}")
```

## 🚨 Known Issues & Solutions

### **Series Page Chart Loading**
**Issue**: Charts not loading for certain series (e.g., Nobel Prize)  
**Status**: FIXED - Auto-population logic and date filtering improved  
**Solution**: Charts now auto-detect single subseries and use proper date range filtering

### **Movers Page Blank Display**
**Issue**: Page showing no data despite markets meeting criteria  
**Status**: FIXED - Corrected candle file paths and filtering logic  
**Solution**: Fixed file naming convention and removed duplicate filtering

### **Table Formatting Inconsistency**
**Issue**: Tables with wrapped titles, no gridlines, inconsistent sizing  
**Status**: FIXED - Using native `st.dataframe` with consistent formatting  
**Solution**: Removed custom CSS, rely on Streamlit's native table rendering

### **Navigation Opening New Tabs**
**Issue**: Clicking navigation elements opened new browser tabs  
**Status**: FIXED - Implemented in-tab navigation  
**Solution**: Use `st.session_state` + `st.switch_page` instead of URL manipulation

## 📝 Coding Standards

### **File Organization**
```
pages/PageName.py           # Main page logic
utils.py                    # Shared functions, caching, DuckDB operations
kalshi_client.py           # API client with rate limiting
```

### **Function Naming**
```python
# Data loading
load_*_from_store()        # Load cached Parquet data
get_*_data()              # Fetch live API data
compute_*()               # Calculate derived metrics

# UI components  
create_*_chart()          # Generate Altair charts
make_*_clickable()        # Navigation helpers
```

### **Error Handling**
```python
# Always handle API failures gracefully
try:
    data = api_call()
except Exception as e:
    st.error(f"API error: {e}")
    data = load_cached_fallback()
```

### **Performance Guidelines**
```python
# 1. Use caching for expensive operations
@st.cache_data(ttl=300)
def expensive_computation():
    pass

# 2. Filter early and often
df = df[df["volume"] > 1000]  # Apply filters before expensive operations

# 3. Use DuckDB for large data operations
result = duckdb_query_optimized("SELECT * FROM data WHERE condition")
```

## 🎯 User Experience Patterns

### **Filter Design**
- **Evenly spaced**: Use `st.columns()` for consistent layout
- **Reasonable defaults**: Set sensible default values (e.g., min volume $2000)
- **Clear labels**: Include help text for complex filters
- **Immediate feedback**: Apply filters instantly, no "Apply" button needed

### **Table Display**
- **Consistent formatting**: Use `st.dataframe()` for all tables
- **Proper column config**: Format currencies, percentages, dates consistently
- **Reasonable sizing**: `use_container_width=True`, `hide_index=True`
- **Clear headers**: Single-line titles, no wrapping

### **Chart Design**
- **Interactive**: Always include `.interactive()` for Altair charts
- **Responsive**: Use `use_container_width=True`
- **Continuous lines**: Fill gaps with forward-fill for smooth visualization
- **Clear tooltips**: Include relevant context (date, ticker, price, volume)

## 🔄 Testing & Debugging

### **Quick Test Script Pattern**
```python
# Create temp debug file (will be gitignored)
# test_issue.py
import sys
sys.path.insert(0, '.')

from utils import *
from pages.PageName import *

# Test specific functionality
result = problematic_function()
print(f"Result: {result}")
```

### **Data Validation Checklist**
- [ ] Check file existence: `os.path.exists("data/file.parquet")`
- [ ] Verify data freshness: File modification time < 30 minutes
- [ ] Validate DataFrame shape: Non-empty, expected columns
- [ ] Test filtering logic: Ensure filters don't eliminate all data
- [ ] Check for null values: Handle missing data gracefully

### **UI Testing Checklist**
- [ ] Page loads without errors
- [ ] Filters work and show immediate results
- [ ] Charts render and are interactive
- [ ] Navigation stays within same tab
- [ ] Error messages are user-friendly
- [ ] Loading indicators appear for slow operations

## 🚀 Common Enhancement Patterns

### **Adding New Page**
1. Create `pages/NewPage.py` with standard structure
2. Add navigation link in `Dashboard.py`
3. Implement caching for data loading
4. Add error handling and loading states
5. Test navigation flow

### **Performance Optimization**
1. Profile slow operations: Use `@st.cache_data` decorators
2. Optimize DuckDB queries: Use column selection, early filtering
3. Reduce API calls: Leverage Parquet cache, batch operations
4. Monitor file sizes: Use compression, remove unused data

### **UI Polish**
1. Consistent spacing: Use `st.columns()` for layout
2. Loading feedback: `with st.spinner("Loading..."):`
3. Error recovery: Provide fallback data sources
4. Progressive disclosure: Hide complex options in `st.expander()`

---

## 📞 Quick Reference

### **Virtual Environment** (CRITICAL!)
```bash
# ALWAYS activate before working
cd Market_Dashboards
env\Scripts\activate
```

### **Start Dashboard**
```bash
streamlit run Dashboard.py
```

### **Refresh Data**
```bash
python scripts/refresh_parquets_optimized.py
```

### **Common Debug Commands**
```python
# Check data files
import os; print([f for f in os.listdir('data') if f.endswith('.parquet')])

# Check API connection  
from kalshi_client import KalshiClient
client = KalshiClient(api_key="your_key")
markets = client.get_markets(limit=1)
```

This development guide should provide immediate context for anyone picking up this project in a new Cursor chat session.
