# Troubleshooting Guide - Kalshi Analytics Dashboard

## 🚨 Quick Diagnostic Commands

### **First Steps - Always Run These**
```bash
# 1. Activate virtual environment (CRITICAL!)
cd Market_Dashboards
env\Scripts\activate

# 2. Check if dashboard starts
streamlit run Dashboard.py

# 3. Check data files exist
python -c "import os; print([f for f in os.listdir('data') if f.endswith('.parquet')])"

# 4. Test API connection
python -c "from kalshi_client import KalshiClient; client = KalshiClient(); print(len(client.get_markets(limit=1)['markets']))"
```

## 🔍 Common Issues & Solutions

### **Issue: Dashboard Won't Start**

#### **Symptoms:**
- `ModuleNotFoundError` when running `streamlit run Dashboard.py`
- `ImportError` for pandas, streamlit, or other dependencies

#### **Diagnosis:**
```bash
# Check if virtual environment is activated
which python  # Should show path with 'env' in it
pip list | grep streamlit  # Should show streamlit installation
```

#### **Solutions:**
```bash
# 1. Activate virtual environment
env\Scripts\activate

# 2. Reinstall dependencies if needed
pip install -r requirements.txt

# 3. Check Python version (needs 3.8+)
python --version
```

---

### **Issue: "No Data Available" on Any Page**

#### **Symptoms:**
- Markets page shows "Could not load markets data"
- All tables are empty
- Charts show "No data available"

#### **Diagnosis:**
```python
# Run this in Python console
import os
import pandas as pd

# Check if parquet files exist
parquet_files = [f for f in os.listdir('data') if f.endswith('.parquet')]
print(f"Parquet files found: {parquet_files}")

# Check file sizes
for f in parquet_files:
    size = os.path.getsize(f'data/{f}') / (1024*1024)  # MB
    print(f"{f}: {size:.2f} MB")

# Check if data is readable
try:
    df = pd.read_parquet('data/active_markets.parquet')
    print(f"Active markets shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
except Exception as e:
    print(f"Error reading parquet: {e}")
```

#### **Solutions:**
```bash
# 1. Refresh data from API
python scripts/refresh_parquets_optimized.py

# 2. Check API key is correct in utils.py
# Edit utils.py and verify API_KEY variable

# 3. If API is down, use manual refresh
python -c "
from utils import load_active_markets, API_KEY
df = load_active_markets(API_KEY)
print(f'Loaded {len(df)} markets')
"
```

---

### **Issue: Series Page Charts Not Loading**

#### **Symptoms:**
- Series cards display correctly
- Subseries selection works
- Chart area is blank or shows "No data available"

#### **Diagnosis:**
```python
# Debug specific series
series_ticker = "KXMAYORNYCPARTY"  # Replace with problematic series

# Check if markets exist for series
from pages.Series import load_markets_for_series
markets_df = load_markets_for_series(series_ticker)
print(f"Markets found: {len(markets_df)}")

# Check subseries extraction
from pages.Series import get_unique_subseries
subseries = get_unique_subseries(markets_df, series_ticker)
print(f"Subseries: {subseries}")

# Check candle data availability
import os
for _, market in markets_df.head(3).iterrows():
    ticker = market['ticker']
    candle_path = f"data/candles/candles_{ticker}_1h.parquet"
    exists = os.path.exists(candle_path)
    print(f"{ticker}: candle file exists = {exists}")
```

#### **Solutions:**
```python
# 1. Recent fix applied - charts should auto-populate for single subseries
# 2. If still not working, check date filtering:

from pages.Series import create_subseries_chart
import datetime

# Test with wide date range
start_date = datetime.date(2024, 1, 1)
end_date = datetime.date(2025, 12, 31)
chart = create_subseries_chart(markets_df, series_ticker, subseries[0][0], start_date, end_date)
print(f"Chart created: {chart is not None}")
```

---

### **Issue: Movers Page Shows No Data**

#### **Symptoms:**
- Page loads but tables are empty
- Filters are present but no results shown
- Error: "No markets found meeting criteria"

#### **Diagnosis:**
```python
# Check filter values and data availability
from pages.Movers import calculate_moves_optimized
from utils import load_active_markets_from_store

# Load data
markets_df = load_active_markets_from_store()
print(f"Total markets loaded: {len(markets_df)}")

# Check volume distribution
vol24 = markets_df.get('volume_24h', markets_df.get('volume', pd.Series(0)))
print(f"Volume stats:")
print(f"  Min: ${vol24.min():,.0f}")
print(f"  Max: ${vol24.max():,.0f}")
print(f"  Median: ${vol24.median():,.0f}")
print(f"  Markets > $2000: {(vol24 > 2000).sum()}")

# Check time-related filters
from datetime import datetime, timedelta
now = datetime.now()
markets_df['hours_to_close'] = (pd.to_datetime(markets_df['close_time']) - now).dt.total_seconds() / 3600
markets_df['hours_since_open'] = (now - pd.to_datetime(markets_df['open_time'])).dt.total_seconds() / 3600

print(f"Time filter stats:")
print(f"  Hours to close - Min: {markets_df['hours_to_close'].min():.1f}, Max: {markets_df['hours_to_close'].max():.1f}")
print(f"  Hours since open - Min: {markets_df['hours_since_open'].min():.1f}, Max: {markets_df['hours_since_open'].max():.1f}")
```

#### **Solutions:**
```python
# 1. Adjust filter defaults if too restrictive
# In pages/Movers.py, try lower thresholds:
min_volume = 500  # Instead of 2000
min_days_to_close = 0.1  # Instead of 1.0
min_days_since_open = 0.5  # Instead of 2.0

# 2. Check candle file availability
import os
candle_dir = "data/candles"
candle_count = len([f for f in os.listdir(candle_dir) if f.endswith('.parquet')])
print(f"Candle files available: {candle_count}")

# 3. Test with relaxed filtering
def test_movers_data():
    df = load_active_markets_from_store()
    df_filtered = df[df.get('volume', 0) > 100]  # Very low threshold
    print(f"Markets with volume > $100: {len(df_filtered)}")
    return df_filtered
```

---

### **Issue: API Rate Limiting / Connection Errors**

#### **Symptoms:**
- Error messages about "429 Too Many Requests"
- "Connection timeout" errors
- Slow data loading

#### **Diagnosis:**
```python
# Test API connection
from kalshi_client import KalshiClient
import time

client = KalshiClient(api_key="your_key")

# Test with small requests
start_time = time.time()
try:
    markets = client.get_markets(limit=10)
    duration = time.time() - start_time
    print(f"API call successful in {duration:.2f}s")
    print(f"Returned {len(markets['markets'])} markets")
except Exception as e:
    print(f"API error: {e}")
```

#### **Solutions:**
```python
# 1. Use cached data primarily
# The dashboard should work mostly from cached Parquet files

# 2. If you need fresh data, reduce API calls
# In scripts/refresh_parquets_optimized.py:
# - Increase refresh interval from 5min to 15min
# - Use smaller page sizes (limit=100 instead of 1000)

# 3. Check rate limits in kalshi_client.py
# Current settings: 5 retries with exponential backoff
# You can increase backoff_factor from 1 to 2 for slower retries
```

---

### **Issue: Virtual Environment Problems**

#### **Symptoms:**
- `env\Scripts\activate` doesn't work
- Command not found errors
- Python modules not found despite installation

#### **Diagnosis:**
```bash
# Check if virtual environment exists
ls env/Scripts/  # Windows
ls env/bin/      # Mac/Linux

# Check what Python you're using
which python
python -c "import sys; print(sys.executable)"
```

#### **Solutions:**
```bash
# Windows - Different activation methods
env\Scripts\activate.bat
# or
env\Scripts\Activate.ps1  # PowerShell
# or  
.\env\Scripts\activate

# Mac/Linux
source env/bin/activate

# If environment is corrupted, recreate it
rm -rf env  # Delete old environment
python -m venv env  # Create new one
env\Scripts\activate  # Activate
pip install -r requirements.txt  # Reinstall dependencies
```

---

### **Issue: Performance Problems (Slow Loading)**

#### **Symptoms:**
- Pages take >10 seconds to load
- Charts don't render
- Browser becomes unresponsive

#### **Diagnosis:**
```python
# Check data file sizes
import os

def check_file_sizes():
    data_dir = "data"
    total_size = 0
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.parquet'):
                path = os.path.join(root, file)
                size = os.path.getsize(path) / (1024*1024)  # MB
                total_size += size
                if size > 50:  # Large files
                    print(f"Large file: {path} - {size:.1f} MB")
    
    print(f"Total data size: {total_size:.1f} MB")

check_file_sizes()

# Check DuckDB performance
from utils import get_duckdb_performance_stats
stats = get_duckdb_performance_stats()
print(f"DuckDB stats: {stats}")
```

#### **Solutions:**
```python
# 1. Clear Streamlit cache
import streamlit as st
st.cache_data.clear()

# 2. Optimize parquet files
python scripts/optimize_storage.py

# 3. Reduce data scope
# In utils.py, add more aggressive filtering:
def load_active_markets_from_store():
    df = pd.read_parquet("data/active_markets.parquet")
    # Only keep high-volume markets for better performance
    return df[df.get('volume', 0) > 500]

# 4. Use sampling for large datasets
# In DuckDB queries, add TABLESAMPLE for big operations:
query = "SELECT * FROM large_table TABLESAMPLE SYSTEM(10) WHERE condition"
```

---

## 🔧 Advanced Debugging

### **Enable Debug Mode**
```python
# Add to top of any page for detailed logging
import logging
import streamlit as st

logging.basicConfig(level=logging.DEBUG)
st.set_option('deprecation.showPyplotGlobalUse', False)

# Show detailed error traces
import traceback
try:
    # problematic code
    pass
except Exception as e:
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())
```

### **Data Quality Checks**
```python
def diagnose_data_quality(df):
    """Comprehensive data quality report"""
    report = {
        'shape': df.shape,
        'columns': list(df.columns),
        'dtypes': df.dtypes.to_dict(),
        'null_counts': df.isnull().sum().to_dict(),
        'memory_usage': df.memory_usage(deep=True).sum() / (1024*1024),  # MB
        'duplicates': df.duplicated().sum(),
    }
    
    # Check for common issues
    issues = []
    if report['null_counts']['ticker'] > 0:
        issues.append("Missing ticker values")
    if report['memory_usage'] > 100:
        issues.append(f"High memory usage: {report['memory_usage']:.1f} MB")
    if report['duplicates'] > 0:
        issues.append(f"Duplicate rows: {report['duplicates']}")
    
    report['issues'] = issues
    return report
```

### **Performance Profiling**
```python
import time
import functools

def time_function(func):
    """Decorator to time function execution"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

# Use on slow functions
@time_function
def slow_operation():
    # your code here
    pass
```

---

## 📞 Emergency Fixes

### **Dashboard Completely Broken**
```bash
# Nuclear option - reset everything
git stash  # Save any changes
git checkout main  # Return to known good state
env\Scripts\activate
pip install -r requirements.txt
python scripts/refresh_parquets_optimized.py
streamlit run Dashboard.py
```

### **Data Corruption**
```bash
# Delete and regenerate all data
rm data/*.parquet
rm -rf data/candles/
python scripts/refresh_parquets_optimized.py
```

### **API Completely Down**
```python
# Work with cached data only
# In utils.py, modify functions to never hit API:
def load_active_markets(api_key, page_size=1000):
    # Skip API, only use cache
    return pd.read_parquet("data/active_markets.parquet")
```

---

## 🎯 Prevention Strategies

### **Regular Health Checks**
```bash
# Daily: Check data freshness
python -c "
import os, datetime
file_time = os.path.getmtime('data/active_markets.parquet')
age_hours = (datetime.datetime.now().timestamp() - file_time) / 3600
print(f'Data age: {age_hours:.1f} hours')
if age_hours > 24:
    print('WARNING: Data is stale')
"

# Weekly: Storage optimization
python scripts/optimize_storage.py

# Monthly: Full refresh
rm data/*.parquet && python scripts/refresh_parquets_optimized.py
```

### **Monitoring Setup**
```python
# Add to Dashboard.py for health monitoring
def display_system_health():
    """Show system health in sidebar"""
    with st.sidebar:
        st.subheader("System Health")
        
        # Data freshness
        try:
            import os
            file_age = (pd.Timestamp.now() - pd.Timestamp.fromtimestamp(
                os.path.getmtime("data/active_markets.parquet")
            )).total_seconds() / 3600
            
            if file_age < 1:
                st.success(f"Data fresh ({file_age:.1f}h)")
            elif file_age < 24:
                st.warning(f"Data aging ({file_age:.1f}h)")
            else:
                st.error(f"Data stale ({file_age:.1f}h)")
        except:
            st.error("Data unavailable")
```

Remember: Most issues are resolved by refreshing data and ensuring the virtual environment is properly activated. When in doubt, start with the basic diagnostic commands at the top of this guide.
