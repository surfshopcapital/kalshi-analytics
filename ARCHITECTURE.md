# Technical Architecture - Kalshi Analytics Dashboard

## 🏗️ System Overview

This document provides a comprehensive technical architecture overview for developers and AI assistants working on the Kalshi Analytics Dashboard.

### **High-Level Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kalshi API    │    │   Data Layer     │    │  Streamlit UI   │
│                 │────▶│                  │────▶│                 │
│ • Markets       │    │ • DuckDB Engine  │    │ • Multi-page    │
│ • Events        │    │ • Parquet Cache  │    │ • Interactive   │
│ • Series        │    │ • Smart Caching  │    │ • Real-time     │
│ • Candlesticks  │    │ • Error Handling │    │ • Navigation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Technology Stack**

- **Frontend**: Streamlit 1.47+ (Python-based web framework)
- **Data Processing**: DuckDB 1.3+ (Analytical SQL database)
- **Data Storage**: Apache Parquet (Columnar storage format)
- **Visualization**: Altair 5.5+ (Declarative statistical visualization)
- **API Client**: Requests with retry logic and rate limiting
- **Caching**: Multi-layer (Streamlit decorators + file-based)

## 📊 Data Flow Architecture

### **Data Pipeline Stages**

```
1. API Ingestion → 2. DuckDB Processing → 3. Parquet Storage → 4. UI Rendering
```

#### **Stage 1: API Ingestion**
```python
# kalshi_client.py - Rate-limited API client
class KalshiClient:
    def get_markets(self, limit=100, status="open") -> dict
    def get_events(self, limit=200) -> dict  
    def get_series(self) -> dict
    def get_candlesticks(self, ticker, granularity="1h") -> dict
```

**Key Features**:
- Automatic retry with exponential backoff
- Rate limiting compliance (5 requests/second)
- Chunked data fetching for large datasets
- Error handling with fallback mechanisms

#### **Stage 2: DuckDB Processing**
```python
# utils.py - Advanced analytics engine
def duckdb_query_optimized(query: str, params: dict = None) -> pd.DataFrame
def duckdb_write_optimized(df: pd.DataFrame, path: str) -> None
def duckdb_aggregate_optimized(path: str, group_by: list, agg_functions: dict) -> pd.DataFrame
```

**Optimizations**:
- Memory limit: 2GB, 4 threads
- Query hints for sampling large datasets
- Columnar compression (Snappy/ZSTD)
- Advanced indexing and statistics

#### **Stage 3: Parquet Storage**
```
data/
├── active_markets.parquet     # ~5-10 MB, refreshed every 5-15 min
├── series_volumes.parquet     # ~1-2 MB, aggregated series data
├── summary_markets.parquet    # ~5-10 MB, processed display data
└── candles/                   # ~2-5 GB total
    ├── candles_TICKER_1h.parquet  # 1-2 MB per ticker
    └── ... (1000+ files)
```

**Storage Strategy**:
- Row group size: 100,000 rows for optimal compression
- Compression ratio: 60-80% space reduction
- Partitioning: By ticker for candle data
- TTL management: Automatic cleanup of stale data

#### **Stage 4: UI Rendering**
```python
# Streamlit pages with consistent patterns
@st.cache_data(ttl=300)
def load_page_data() -> pd.DataFrame

# Standardized display components
st.dataframe(df, use_container_width=True, hide_index=True)
st.altair_chart(chart, use_container_width=True)
```

## 🔧 Core Components

### **1. API Client Layer (`kalshi_client.py`)**

**Purpose**: Robust interface to Kalshi's REST API with enterprise-grade reliability

```python
class KalshiClient:
    """
    Read-only client for Kalshi public market data
    Features:
    - Automatic retries with exponential backoff
    - Rate limiting compliance
    - Chunked data fetching for large responses
    - Connection pooling for efficiency
    """
```

**Key Patterns**:
- Session-based connections with retry adapters
- Chunked fetching for candlestick data (5000 intervals max)
- Automatic series discovery for market relationships
- Error handling with graceful degradation

### **2. Data Utilities Layer (`utils.py`)**

**Purpose**: High-performance data processing and caching infrastructure

#### **DuckDB Integration**
```python
@contextmanager
def duckdb_context():
    """Context manager ensuring proper connection cleanup"""
    
def duckdb_query_optimized(query: str) -> pd.DataFrame:
    """Execute optimized queries with performance hints"""
    
def duckdb_write_optimized(df: pd.DataFrame, path: str) -> None:
    """Write with advanced compression and optimization"""
```

#### **Caching Strategy**
```python
# Multi-layer caching approach
@st.cache_data(ttl=300)  # Streamlit memory cache
def load_active_markets() -> pd.DataFrame:
    # 1. Try Parquet cache (fastest)
    # 2. Fall back to API (slower)
    # 3. Fall back to minimal dataset (last resort)
```

#### **Performance Monitoring**
```python
def analyze_parquet_performance(path: str) -> dict:
    """Real-time performance analysis of data files"""
    
def get_duckdb_performance_stats() -> dict:
    """Monitor DuckDB query performance and configuration"""
```

### **3. Page Components (`pages/`)**

#### **Standardized Page Structure**
```python
def main():
    st.set_page_config(page_title="Page Name", layout="wide")
    st.title("📊 Page Title")
    
    # 1. Load data with caching
    with st.spinner("Loading..."):
        df = load_cached_data()
    
    # 2. Apply filters
    filtered_df = apply_user_filters(df)
    
    # 3. Display results
    display_data_table(filtered_df)
    display_charts(filtered_df)
    
    # 4. Handle navigation
    handle_user_interactions()
```

#### **Navigation Pattern**
```python
# Consistent in-tab navigation
if user_action:
    st.session_state.selected_ticker = ticker
    st.session_state.selected_title = title  
    st.switch_page("pages/Overview.py")
```

### **4. Chart Generation (`altair` integration)**

#### **Interactive Chart Pattern**
```python
def create_price_chart(df: pd.DataFrame) -> alt.Chart:
    """Standard pattern for all charts"""
    return alt.Chart(df).mark_line().encode(
        x=alt.X("datetime:T", title="Date", axis=alt.Axis(format="%m/%d")),
        y=alt.Y("price:Q", title="Price ($)", scale=alt.Scale(zero=False)),
        color=alt.Color("ticker:N", title="Market"),
        tooltip=[
            alt.Tooltip("datetime:T", title="Date", format="%m/%d/%Y %H:%M"),
            alt.Tooltip("price:Q", title="Price", format="$.2f"),
            alt.Tooltip("volume:Q", title="Volume", format=",.0f")
        ]
    ).properties(
        height=400,
        width="container"
    ).interactive()  # Always interactive
```

## 🚀 Performance Architecture

### **Query Optimization Strategy**

#### **1. Lazy Loading**
```python
# Load only what's needed, when it's needed
df = load_minimal_data()  # Fast initial load
if user_requests_details:
    detailed_df = load_comprehensive_data()  # On-demand loading
```

#### **2. Column Selection**
```python
# DuckDB column pruning for 10x performance
query = """
    SELECT ticker, title, yes_bid, volume_24h  -- Only needed columns
    FROM active_markets 
    WHERE volume_24h > 1000  -- Early filtering
    ORDER BY volume_24h DESC
    LIMIT 100  -- Pagination
"""
```

#### **3. Intelligent Caching**
```python
# Cache at multiple levels
@st.cache_data(ttl=300)    # Memory cache (fastest)
def load_markets():
    return read_parquet_cache()  # Disk cache (fast)
    # fallback to API (slow) only if needed
```

### **Memory Management**

#### **DuckDB Configuration**
```python
# Optimized for analytical workloads
con.execute("SET memory_limit='2GB'")
con.execute("SET threads=4") 
con.execute("SET enable_object_cache=true")
con.execute("SET enable_http_metadata_cache=true")
```

#### **Streamlit Optimization**
```python
# Prevent memory leaks
@st.cache_data(max_entries=10, ttl=600)  # Limited cache size
def expensive_computation():
    pass

# Clear cache when needed  
if st.button("Refresh Data"):
    st.cache_data.clear()
```

## 🔒 Error Handling Architecture

### **Layered Error Resilience**

#### **1. API Level**
```python
# Retry with exponential backoff
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
```

#### **2. Data Level**
```python
# Graceful degradation
try:
    data = load_fresh_api_data()
except APIError:
    data = load_cached_data()
    st.warning("Using cached data due to API issues")
except CacheError:
    data = load_minimal_fallback()
    st.error("Limited data available")
```

#### **3. UI Level**
```python
# User-friendly error messages
try:
    chart = create_complex_chart(data)
    st.altair_chart(chart)
except DataError:
    st.info("Chart unavailable - insufficient data")
except Exception as e:
    st.error(f"Visualization error: {e}")
    # Still show raw data table as fallback
    st.dataframe(data)
```

### **Data Validation Pipeline**

```python
def validate_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Comprehensive data validation"""
    # 1. Schema validation
    required_cols = ["ticker", "title", "yes_bid", "volume"]
    assert all(col in df.columns for col in required_cols)
    
    # 2. Data type validation  
    df["yes_bid"] = pd.to_numeric(df["yes_bid"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    
    # 3. Business logic validation
    df = df[df["yes_bid"].between(0, 100)]  # Valid price range
    df = df[df["volume"] >= 0]  # Non-negative volume
    
    # 4. Completeness validation
    completion_rate = df.notnull().mean().mean()
    if completion_rate < 0.9:
        st.warning(f"Data completeness: {completion_rate:.1%}")
    
    return df
```

## 🔄 State Management

### **Session State Architecture**

```python
# Persistent state across page reloads
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "user_filters" not in st.session_state:
    st.session_state.user_filters = default_filters()

# Navigation state
def navigate_to_overview(ticker: str, title: str):
    st.session_state.selected_ticker = ticker
    st.session_state.selected_title = title
    st.switch_page("pages/Overview.py")
```

### **Query Parameter Handling**

```python
# Deep linking support
query_params = st.query_params
if "ticker" in query_params:
    selected_ticker = query_params["ticker"]
    # Auto-load market data
else:
    selected_ticker = st.session_state.get("selected_ticker")
```

## 📈 Scalability Considerations

### **Data Volume Scaling**

#### **Current Scale**
- Markets: ~3,000-5,000 active markets
- Candles: ~1,000 tickers × 8,760 hours/year = 8.7M records
- Storage: ~2-5 GB total
- Query time: <100ms for most operations

#### **Scaling Strategy**
```python
# Partitioning for larger datasets
def write_partitioned_data(df: pd.DataFrame, partition_col: str):
    """Partition by series, date, or volume tier"""
    for partition_value in df[partition_col].unique():
        partition_df = df[df[partition_col] == partition_value]
        path = f"data/{partition_col}={partition_value}/data.parquet"
        duckdb_write_optimized(partition_df, path)

# Sampling for very large datasets  
query = """
    SELECT * FROM large_table 
    TABLESAMPLE SYSTEM(10)  -- 10% sample
    WHERE conditions
"""
```

### **Performance Monitoring**

```python
# Built-in performance tracking
import time

@st.cache_data
def monitor_query_performance(query: str) -> tuple:
    start_time = time.time()
    result = execute_query(query)
    duration = time.time() - start_time
    
    # Log slow queries
    if duration > 1.0:
        st.warning(f"Slow query detected: {duration:.2f}s")
    
    return result, duration
```

## 🎯 Design Patterns

### **1. Repository Pattern**
```python
class MarketDataRepository:
    """Centralized data access with multiple backends"""
    def get_markets(self) -> pd.DataFrame:
        # Try cache first, then API
        pass
    
    def get_candles(self, ticker: str) -> pd.DataFrame:
        # Smart caching with TTL
        pass
```

### **2. Factory Pattern**
```python
def create_chart(chart_type: str, data: pd.DataFrame) -> alt.Chart:
    """Factory for different chart types"""
    if chart_type == "line":
        return create_line_chart(data)
    elif chart_type == "bar":
        return create_bar_chart(data)
    # etc.
```

### **3. Observer Pattern**
```python
# Watch for data changes and update UI
if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()  # Trigger UI refresh
```

This architecture provides a solid foundation for scalable, maintainable analytics applications with enterprise-grade performance and reliability.
