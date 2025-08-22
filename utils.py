# utils.py

# Try to import streamlit, but make it optional to prevent import errors
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

import pandas as pd

# Safe import for os and datetime
try:
    import os
    import datetime
    import time
    from contextlib import contextmanager
    OS_AVAILABLE = True
except ImportError:
    OS_AVAILABLE = False
    os = None
    datetime = None
    time = None
    contextmanager = None

# Helper functions for Streamlit decorators when streamlit is not available
def safe_cache_data(ttl=None):
    """Safe wrapper for st.cache_data decorator"""
    if STREAMLIT_AVAILABLE and st is not None:
        return st.cache_data(ttl=ttl)
    else:
        # Return a no-op decorator
        def decorator(func):
            return func
        return decorator

def safe_cache_resource():
    """Safe wrapper for st.cache_resource decorator"""
    if STREAMLIT_AVAILABLE and st is not None:
        return st.cache_resource
    else:
        # Return a no-op decorator
        def decorator(func):
            return func
        return decorator

def safe_error(message):
    """Safe wrapper for st.error"""
    if STREAMLIT_AVAILABLE and st is not None:
        safe_error(message)
    else:
        print(f"ERROR: {message}")

def safe_button(text, key=None, help=None):
    """Safe wrapper for st.button"""
    if STREAMLIT_AVAILABLE and st is not None:
        return st.button(text, key=key, help=help)
    else:
        return False

def safe_session_state():
    """Safe wrapper for st.session_state"""
    if STREAMLIT_AVAILABLE and st is not None:
        return st.session_state
    else:
        # Return a simple dict-like object
        class MockSessionState:
            def __init__(self):
                self._data = {}
            def get(self, key, default=None):
                return self._data.get(key, default)
            def __setattr__(self, key, value):
                if key == '_data':
                    super().__setattr__(key, value)
                else:
                    self._data[key] = value
        return MockSessionState()

def safe_switch_page(page):
    """Safe wrapper for st.switch_page"""
    if STREAMLIT_AVAILABLE and st is not None:
        st.switch_page(page)
    else:
        print(f"Would switch to page: {page}")

# Try to import optional dependencies
try:
    from kalshi_client import KalshiClient
    KALSHI_AVAILABLE = True
except ImportError:
    KALSHI_AVAILABLE = False
    KalshiClient = None

try:
    from requests.exceptions import HTTPError
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    HTTPError = None
    requests = None

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    duckdb = None

# Safe import for os and datetime
try:
    import os
    import datetime
    import time
    from contextlib import contextmanager
    OS_AVAILABLE = True
except ImportError:
    OS_AVAILABLE = False
    os = None
    datetime = None
    time = None
    contextmanager = None

# ── Define your data directories here ─────────────────────────────
try:
    BASE_DIR = os.path.dirname(__file__) if os else "."
    DATA_DIR = os.path.join(BASE_DIR, "data") if os else "./data"
except Exception:
    BASE_DIR = "."
    DATA_DIR = "./data"

# Move directory creation to a function to avoid issues during import
def ensure_directories():
    """Ensure all required directories exist"""
    if not OS_AVAILABLE:
        return
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, "candles"), exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directories: {e}")

# Don't call this during import - call it when needed instead
# ensure_directories()  # Commented out to prevent import errors

# File paths
try:
    ACTIVE_MARKETS_PQ = os.path.join(DATA_DIR, "active_markets.parquet") if os else "./data/active_markets.parquet"
    SUMMARY_MARKETS_PQ = os.path.join(DATA_DIR, "summary_markets.parquet") if os else "./data/summary_markets.parquet"
    CANDLES_DIR = os.path.join(DATA_DIR, "candles") if os else "./data/candles"
    SERIES_VOLUMES_PQ = os.path.join(DATA_DIR, "series_volumes.parquet") if os else "./data/series_volumes.parquet"
    CHANGELOG_FILE = os.path.join(DATA_DIR, "changelog.json") if os else "./data/changelog.json"

    # NEW: Polymarket data files
    POLYMARKET_MARKETS_PQ = os.path.join(DATA_DIR, "polymarket_markets.parquet") if os else "./data/polymarket_markets.parquet"
    POLYMARKET_SUMMARY_PQ = os.path.join(DATA_DIR, "polymarket_summary.parquet") if os else "./data/polymarket_summary.parquet"
except Exception:
    ACTIVE_MARKETS_PQ = "./data/active_markets.parquet"
    SUMMARY_MARKETS_PQ = "./data/summary_markets.parquet"
    CANDLES_DIR = "./data/candles"
    SERIES_VOLUMES_PQ = "./data/series_volumes.parquet"
    CHANGELOG_FILE = "./data/changelog.json"
    POLYMARKET_MARKETS_PQ = "./data/polymarket_markets.parquet"
    POLYMARKET_SUMMARY_PQ = "./data/polymarket_summary.parquet"

"""
Configuration loading with collision-safe import.
Avoids conflicts with unrelated third-party 'config' modules by loading from the
project-local config.py when present; otherwise uses environment variables.
"""
API_KEY = ""
PRIVATE_KEY = ""
PRIVATE_KEY_PATH = ""

# First, try to import a local config.py next to this file
try:
    if os and os.path.exists(os.path.join(BASE_DIR, "config.py")):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("md_config", os.path.join(BASE_DIR, "config.py"))
            md_config = importlib.util.module_from_spec(spec)
            assert spec and spec.loader
            spec.loader.exec_module(md_config)
            API_KEY = getattr(md_config, "KALSHI_API_KEY_ID", "")
            PRIVATE_KEY = getattr(md_config, "KALSHI_API_PRIVATE_KEY", "")
            PRIVATE_KEY_PATH = getattr(md_config, "KALSHI_PRIVATE_KEY_PATH", "")
        except Exception:
            # Fall back to env vars if local config load fails
            API_KEY = os.getenv('KALSHI_API_KEY_ID', "") if os else ""
            PRIVATE_KEY = os.getenv('KALSHI_API_PRIVATE_KEY', "") if os else ""
            PRIVATE_KEY_PATH = os.getenv('KALSHI_PRIVATE_KEY_PATH', "") if os else ""
    else:
        # No local config file; use environment variables
        API_KEY = os.getenv('KALSHI_API_KEY_ID', "") if os else ""
        PRIVATE_KEY = os.getenv('KALSHI_API_PRIVATE_KEY', "") if os else ""
        PRIVATE_KEY_PATH = os.getenv('KALSHI_PRIVATE_KEY_PATH', "") if os else ""
except Exception:
    # Ultimate fallback
    API_KEY = ""
    PRIVATE_KEY = ""
    PRIVATE_KEY_PATH = ""

# ── Authentication helpers ─────────────────────────────────────────────
def has_portfolio_auth() -> bool:
    """Return True if both API Key ID and a private key (inline or file) are available."""
    if not OS_AVAILABLE:
        return False
    try:
        api_id_available = bool(API_KEY)
        inline_key_available = bool(PRIVATE_KEY and PRIVATE_KEY.startswith('-----BEGIN'))
        file_key_available = bool(PRIVATE_KEY_PATH and os.path.exists(PRIVATE_KEY_PATH))
        return api_id_available and (inline_key_available or file_key_available)
    except Exception:
        return False

def get_auth_status() -> dict:
    """Return a small status dict describing how auth will be performed."""
    if not OS_AVAILABLE:
        return {
            "api_key_id_present": False,
            "private_key_inline": False,
            "private_key_file": False,
            "has_portfolio_auth": False,
        }
    try:
        return {
            "api_key_id_present": bool(API_KEY),
            "private_key_inline": bool(PRIVATE_KEY and PRIVATE_KEY.startswith('-----BEGIN')),
            "private_key_file": bool(PRIVATE_KEY_PATH and os.path.exists(PRIVATE_KEY_PATH)),
            "has_portfolio_auth": has_portfolio_auth(),
        }
    except Exception:
        return {
            "api_key_id_present": False,
            "private_key_inline": False,
            "private_key_file": False,
            "has_portfolio_auth": False,
        }

# ── Enhanced DuckDB Connection Pool with Better Performance ─────────────
@safe_cache_resource()
def get_duckdb_connection():
    """Get a cached DuckDB connection with advanced optimizations"""
    if not DUCKDB_AVAILABLE:
        safe_error("DuckDB is not available. Please install it with: pip install duckdb")
        return None
        
    con = duckdb.connect(':memory:')
    
    # Enable advanced optimizations (only set once per connection)
    con.execute("SET enable_progress_bar=false")
    con.execute("SET enable_object_cache=true")
    con.execute("SET enable_http_metadata_cache=true")
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    
    # Enable DuckDB extensions for better performance
    try:
        con.execute("INSTALL http")
        con.execute("LOAD http")
    except:
        pass  # Extension might already be loaded
    
    return con

def get_fresh_duckdb_connection():
    """Get a fresh DuckDB connection for operations that need it"""
    if not DUCKDB_AVAILABLE:
        safe_error("DuckDB is not available. Please install it with: pip install duckdb")
        return None
        
    con = duckdb.connect(':memory:')
    
    # Enable advanced optimizations
    con.execute("SET enable_progress_bar=false")
    con.execute("SET enable_object_cache=true")
    con.execute("SET enable_http_metadata_cache=true")
    con.execute("SET memory_limit='2GB'")
    con.execute("SET threads=4")
    
    # Enable DuckDB extensions for better performance
    try:
        con.execute("INSTALL http")
        con.execute("LOAD http")
    except:
        pass  # Extension might already be loaded
    
    return con

@contextmanager
def duckdb_context():
    """Context manager for DuckDB operations with automatic cleanup"""
    # Always use a fresh connection to avoid caching issues
    con = get_fresh_duckdb_connection()
    if con is None:
        yield None # Return None if DuckDB is not available
        return
    try:
        yield con
    finally:
        # Always close fresh connections
        con.close()

# ── Advanced DuckDB Query Functions with Performance Hints ─────────────
def duckdb_query_optimized(query: str, params: dict = None, explain: bool = False) -> pd.DataFrame:
    """Execute optimized DuckDB query with performance monitoring"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()

        # Add query optimization hints
        if "SELECT" in query.upper() and "FROM" in query.upper():
            # Add LIMIT if not present for large queries
            if "LIMIT" not in query.upper():
                query += " LIMIT 10000"
        
        if explain:
            # Show query plan for debugging
            plan = con.execute(f"EXPLAIN {query}", params if params else []).fetchall()
            print("Query Plan:")
            for row in plan:
                print(f"  {row[0]}")
        
        if params:
            result = con.execute(query, params).df()
        else:
            result = con.execute(query).df()
        
        return result

def duckdb_write_optimized(df: pd.DataFrame, path: str, compression: str = "snappy", 
                          row_group_size: int = 100000) -> None:
    """Write DataFrame to Parquet using DuckDB with advanced optimizations"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return
        # Register DataFrame as a temporary table
        con.register("temp_df", df)
        
        # Use optimized COPY command with performance settings
        copy_query = f"""
            COPY temp_df TO '{path}' (
                FORMAT PARQUET, 
                COMPRESSION '{compression.upper()}',
                ROW_GROUP_SIZE {row_group_size}
            )
        """
        con.execute(copy_query)

def duckdb_read_optimized(path: str, columns: list = None, filters: dict = None, 
                         limit: int = None) -> pd.DataFrame:
    """Read Parquet with advanced DuckDB optimizations"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()

        # Build optimized query with performance hints
        if columns:
            cols_str = ", ".join(columns)
            query = f"SELECT {cols_str} FROM '{path}'"
        else:
            query = f"SELECT * FROM '{path}'"
        
        # Add filters if provided
        if filters:
            filter_conditions = []
            for col, value in filters.items():
                if isinstance(value, (list, tuple)):
                    filter_conditions.append(f"{col} IN {value}")
                elif isinstance(value, str):
                    filter_conditions.append(f"{col} = '{value}'")
                else:
                    filter_conditions.append(f"{col} = {value}")
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        # Add limit for performance
        if limit:
            query += f" LIMIT {limit}"
        
        # Add optimization hints
        query += " /*+ USE_SAMPLE(0.1) */"  # Use sampling for large files
        
        return con.execute(query).df()

# ── Advanced DuckDB Analytics Functions ───────────────────────────────
def duckdb_aggregate_optimized(path: str, group_by: list, agg_functions: dict, 
                              filters: dict = None) -> pd.DataFrame:
    """Perform optimized aggregations using DuckDB"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()

        # Build aggregation query
        agg_parts = []
        for col, func in agg_functions.items():
            agg_parts.append(f"{func}({col}) as {col}_{func}")
        
        query = f"""
            SELECT 
                {', '.join(group_by)},
                {', '.join(agg_parts)}
            FROM '{path}'
        """
        
        if filters:
            filter_conditions = []
            for col, value in filters.items():
                if isinstance(value, (list, tuple)):
                    filter_conditions.append(f"{col} IN {value}")
                elif isinstance(value, str):
                    filter_conditions.append(f"{col} = '{value}'")
                else:
                    filter_conditions.append(f"{col} = {value}")
            
            if filter_conditions:
                query += " WHERE " + " AND ".join(filter_conditions)
        
        query += f" GROUP BY {', '.join(group_by)}"
        
        return con.execute(query).df()

def duckdb_join_optimized(left_path: str, right_path: str, on_columns: dict, 
                         join_type: str = "INNER") -> pd.DataFrame:
    """Perform optimized joins between Parquet files using DuckDB"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()

        # Build join query
        join_conditions = []
        for left_col, right_col in on_columns.items():
            join_conditions.append(f"l.{left_col} = r.{right_col}")
        
        query = f"""
            SELECT l.*, r.*
            FROM '{left_path}' l
            {join_type} JOIN '{right_path}' r
            ON {' AND '.join(join_conditions)}
        """
        
        return con.execute(query).df()

# ── Performance Monitoring and Diagnostics ─────────────────────────────
def get_duckdb_performance_stats() -> dict:
    """Get DuckDB performance statistics and configuration"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return {
                "version": "Unknown",
                "error": "DuckDB not available",
                "connection_active": False
            }
        try:
            # Get DuckDB version and configuration
            version = con.execute("SELECT version()").fetchone()[0]
            
            # Get available system tables (safe approach)
            system_tables = []
            try:
                system_tables = con.execute("SELECT name FROM system.tables WHERE name LIKE 'system%'").df()
            except:
                pass
            
            # Get basic connection info
            connection_info = {
                "version": version,
                "system_tables_available": len(system_tables) > 0,
                "connection_active": True
            }
            
            return connection_info
            
        except Exception as e:
            return {
                "version": "Unknown",
                "error": str(e),
                "connection_active": False
            }

def analyze_parquet_performance(path: str) -> dict:
    """Analyze Parquet file performance characteristics"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return {"error": "DuckDB not available"}
        try:
            # Get file size
            file_size = os.path.getsize(path) / (1024 * 1024)  # MB
            
            # Get row count
            row_count = con.execute(f"SELECT COUNT(*) FROM '{path}'").fetchone()[0]
            
            # Get column statistics
            columns = con.execute(f"DESCRIBE '{path}'").df()
            
            # Get sample data for analysis
            sample = con.execute(f"SELECT * FROM '{path}' LIMIT 1000").df()
            
            # Calculate compression ratio
            original_size = row_count * len(columns) * 8  # Rough estimate
            compression_ratio = original_size / (file_size * 1024 * 1024)
            
            return {
                "file_size_mb": round(file_size, 2),
                "row_count": row_count,
                "column_count": len(columns),
                "columns": columns.to_dict('records'),
                "compression_ratio": round(compression_ratio, 2),
                "sample_data": sample.head(5).to_dict('records')
            }
        except Exception as e:
            return {"error": str(e)}

def optimize_parquet_storage(path: str, target_compression: str = "zstd") -> str:
    """Optimize Parquet file storage with better compression"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return "DuckDB not available"
        # Create optimized version
        optimized_path = path.replace('.parquet', f'_optimized_{target_compression}.parquet')
        
        # Read and rewrite with better compression
        query = f"""
            COPY (
                SELECT * FROM '{path}'
            ) TO '{optimized_path}' (
                FORMAT PARQUET,
                COMPRESSION '{target_compression.upper()}',
                ROW_GROUP_SIZE 50000
            )
        """
        con.execute(query)
        
        # Compare file sizes
        original_size = os.path.getsize(path) / (1024 * 1024)
        optimized_size = os.path.getsize(optimized_path) / (1024 * 1024)
        savings = ((original_size - optimized_size) / original_size) * 100
        
        print(f"Storage optimization complete:")
        print(f"  Original: {original_size:.2f} MB")
        print(f"  Optimized: {optimized_size:.2f} MB")
        print(f"  Savings: {savings:.1f}%")
        
        return optimized_path

# ── Enhanced Market Data Functions with DuckDB ───────────────────────
def get_market_stats_optimized() -> dict:
    """Get market statistics using advanced DuckDB optimizations"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return {
                "total_markets": 0,
                "active_markets": 0,
                "total_volume": 0,
                "total_open_interest": 0,
                "avg_volume": 0,
                "max_volume": 0,
                "high_volume_markets": 0
            }
        # Use optimized aggregation with sampling for large datasets
        query = """
            SELECT 
                COUNT(*) as total_markets,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_markets,
                SUM(CASE WHEN volume > 0 THEN volume ELSE 0 END) as total_volume,
                SUM(CASE WHEN open_interest > 0 THEN open_interest ELSE 0 END) as total_open_interest,
                AVG(CASE WHEN volume > 0 THEN volume ELSE NULL END) as avg_volume,
                MAX(CASE WHEN volume > 0 THEN volume ELSE 0 END) as max_volume,
                COUNT(CASE WHEN volume > 1000 THEN 1 END) as high_volume_markets
            FROM read_parquet(?) 
            /*+ USE_SAMPLE(0.1) */
        """
        result = con.execute(query, [ACTIVE_MARKETS_PQ]).fetchone()
        
        return {
            "total_markets": result[0],
            "active_markets": result[1],
            "total_volume": result[2],
            "total_open_interest": result[3],
            "avg_volume": result[4],
            "max_volume": result[5],
            "high_volume_markets": result[6]
        }

def get_top_markets_by_volume(limit: int = 10, min_volume: int = 1000) -> pd.DataFrame:
    """Get top markets by volume using advanced DuckDB optimizations"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    query = f"""
        SELECT 
            ticker,
            title,
            volume,
            yes_bid,
            no_bid,
            close_time,
            event_ticker
        FROM read_parquet('{ACTIVE_MARKETS_PQ}')
        WHERE volume >= {min_volume}
        ORDER BY volume DESC
        LIMIT {limit}
        /*+ USE_SAMPLE(0.05) */
    """
    return duckdb_query_optimized(query)

def get_markets_by_series(series_ticker: str, min_volume: int = 100) -> pd.DataFrame:
    """Get all markets for a specific series using DuckDB with filtering"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    query = """
        SELECT 
            ticker,
            title,
            volume,
            yes_bid,
            no_bid,
            close_time,
            event_ticker
        FROM read_parquet(?) 
        WHERE event_ticker = ? AND volume >= ?
        ORDER BY volume DESC
        /*+ USE_SAMPLE(0.1) */
    """
    return duckdb_query_optimized(query, [ACTIVE_MARKETS_PQ, series_ticker, min_volume])

def get_candle_data_optimized(ticker: str, hours: int = 24, use_sampling: bool = True) -> pd.DataFrame:
    """Get optimized candle data with optional sampling for performance"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    end_ts = int(datetime.datetime.now().timestamp())
    start_ts = end_ts - (hours * 3600)
    
    path = os.path.join(CANDLES_DIR, f"candles_{ticker}_1h.parquet")
    if not os.path.exists(path):
        return pd.DataFrame()
    
    # Use sampling for very large datasets
    sample_hint = "/*+ USE_SAMPLE(0.1) */" if use_sampling else ""
    
    query = f"""
        SELECT 
            end_period_ts,
            price,
            volume
        FROM '{path}'
        WHERE end_period_ts >= {start_ts} AND end_period_ts <= {end_ts}
        ORDER BY end_period_ts
        {sample_hint}
    """
    return duckdb_query_optimized(query)

# ── Batch Processing Functions ───────────────────────────────────────
def batch_process_parquets(directory: str, operation: str, **kwargs) -> dict:
    """Batch process multiple Parquet files with DuckDB"""
    results = {}
    
    if not os.path.exists(directory):
        return {"error": f"Directory {directory} does not exist"}
    
    parquet_files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
    
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return {"error": "DuckDB not available"}
        for file in parquet_files:
            file_path = os.path.join(directory, file)
            try:
                if operation == "analyze":
                    results[file] = analyze_parquet_performance(file_path)
                elif operation == "optimize":
                    results[file] = optimize_parquet_storage(file_path, **kwargs)
                elif operation == "stats":
                    results[file] = con.execute(f"SELECT COUNT(*) FROM '{file_path}'").fetchone()[0]
            except Exception as e:
                results[file] = {"error": str(e)}
    
    return results

# ── Enhanced Series Analysis with DuckDB ─────────────────────────────
def get_series_volume_trends(series_ticker: str, days: int = 7) -> pd.DataFrame:
    """Get volume trends for a series over time using DuckDB aggregations"""
    # This would require joining series data with market data
    # Implementation depends on your specific data structure
    pass

def get_market_correlation_analysis(market_tickers: list, days: int = 30) -> pd.DataFrame:
    """Analyze correlations between markets using DuckDB"""
    # This would require complex time-series analysis
    # Implementation depends on your specific needs
    pass

@safe_cache_resource()
def get_client() -> KalshiClient:
    """
    Returns a singleton KalshiClient for any non-cached calls you might still need.
    """
    # For Kalshi API, we need both the API Key ID and private key for portfolio endpoints
    # The KalshiClient will handle the authentication method automatically
    if PRIVATE_KEY and PRIVATE_KEY.startswith('-----BEGIN'):
        # We have a private key, use it for RSA signature authentication
        return KalshiClient(private_key=PRIVATE_KEY, api_key_id=API_KEY)
    elif PRIVATE_KEY_PATH and os.path.exists(PRIVATE_KEY_PATH):
        # Read private key from file
        with open(PRIVATE_KEY_PATH, 'r') as f:
            private_key_content = f.read()
        return KalshiClient(private_key=private_key_content, api_key_id=API_KEY)
    else:
        # Fall back to API Key ID for Bearer token authentication (public endpoints only)
        return KalshiClient(api_key=API_KEY)

@safe_cache_data(ttl=300)
def load_active_markets(api_key: str, page_size: int = 1000) -> pd.DataFrame:
    # ── your existing fetch + filtering logic ─────────────────
    client = KalshiClient(api_key=api_key)
    all_markets, cursor = [], None
    while True:
        resp = client.get_markets(limit=page_size, status="open", cursor=cursor)
        batch = resp.get("markets", [])
        if not batch: break
        all_markets.extend(batch)
        cursor = resp.get("cursor")
    df = pd.DataFrame(all_markets)
    if "volume" in df.columns:
        df = df[df["volume"] > 0]

    # ── write to Parquet for downstream use ────────────────────
    # use DuckDB to efficiently write Parquet
    duckdb_write_optimized(df, ACTIVE_MARKETS_PQ)
    
    return df

@safe_cache_data(ttl=60)
def load_active_markets_from_store() -> pd.DataFrame:
    # instant read from Parquet, zero API calls
    return duckdb_read_optimized(ACTIVE_MARKETS_PQ)

@safe_cache_data(ttl=300)
def get_summary_df_store() -> pd.DataFrame:
    # if you want to materialize get_summary_df into Parquet too:
    return duckdb_read_optimized(SUMMARY_MARKETS_PQ)

@safe_cache_data(ttl=300)
def get_summary_df(api_key: str, page_size: int = 1000) -> pd.DataFrame:
    """
    Builds and caches the cleaned summary table for the Markets page.
    """
    # 1) Load raw markets (cached)
    df = load_active_markets(api_key, page_size=page_size)

    # 2) Sort by 24h volume descending
    df = df.sort_values("volume", ascending=False)

    # 3) Rename & select exactly the columns you need
    df = df.rename(columns={
        "title":         "Title",
        "yes_sub_title": "Yes Subtitle",
        "no_sub_title":  "No Subtitle",
        "yes_ask":       "Yes Ask",
        "no_ask":        "No Ask",
        "last_price":    "Last Price",
        "volume":        "Volume (24h)",
        "close_time":    "Close Time",
    })[
        [
            "Title", "Yes Subtitle", "No Subtitle",
            "Yes Ask", "No Ask", "Last Price",
            "Volume (24h)", "Close Time"
        ]
    ]
    # ── write summary to Parquet ───────────────────────────────
    duckdb_write_optimized(df, SUMMARY_MARKETS_PQ)

    return df

def get_volume_columns(df: pd.DataFrame) -> tuple:
    """Returns (volume_24h_series, total_volume_series) consistently across all pages"""
    # Handle different data source structures
    if 'data_source' in df.columns:
        # Unified data - handle both Kalshi and Polymarket
        vol_24h = df.get("volume_24h", df.get("volume"))
        total_vol = df.get("volume_total", df.get("volume"))
    else:
        # Legacy Kalshi data
        vol_24h = df.get("volume_24h", df.get("volume"))
        total_vol = df.get("volume")
    
    # Ensure we never return None - provide fallbacks
    if vol_24h is None or vol_24h.empty:
        vol_24h = pd.Series(0, index=df.index)
    if total_vol is None or total_vol.empty:
        total_vol = pd.Series(0, index=df.index)
    
    return vol_24h, total_vol

def compute_stats(df: pd.DataFrame) -> dict:
    """
    Simple summary stats on a markets DataFrame.
    """
    total  = len(df)
    active = df[df.get("status") == "active"].shape[0] if "status" in df.columns else 0
    volume = int(df["volume"].sum())   if "volume" in df.columns       else 0
    oi     = int(df["open_interest"].sum()) if "open_interest" in df.columns else 0

    return {
        "total": total,
        "active": active,
        "volume": volume,
        "open_interest": oi,
    }

# ── Enhanced Event-to-Series Mapping with DuckDB ─────────────────
@safe_cache_data(ttl=3600)
def get_events_to_series_mapping(api_key: str) -> dict:
    """Optimized: Only fetch events for active markets with volume >$1k. Much faster than fetching all 55k+ events."""
    # Get the actual markets we care about first
    df_markets = load_active_markets_from_store()
    if df_markets.empty:
        return {}
    
    # Filter to markets with volume > $1000 in last week
    min_volume = 1000
    vol_24h, _ = get_volume_columns(df_markets)
    high_volume_markets = df_markets[vol_24h.fillna(0) >= min_volume]
    
    if high_volume_markets.empty:
        return {}
    
    # Get unique event tickers we actually need
    needed_events = set(high_volume_markets.get("event_ticker", pd.Series()).dropna())
    print(f"📊 Optimized: Only fetching {len(needed_events)} relevant events (vs 55k+ total)")
    
    # Only fetch the events we actually need
    client = KalshiClient(api_key=api_key)
    events_mapping = {}
    
    # Fetch events but exit early when we have what we need
    events, cursor = [], None
    while True:
        r = client.get_events(limit=200, cursor=cursor)
        batch = r.get("events", [])
        if not batch:
            break
        
        # Only keep events we actually need
        for event in batch:
            event_ticker = event.get("event_ticker")
            if event_ticker in needed_events:
                events_mapping[event_ticker] = event.get("series_ticker")
        
        cursor = r.get("cursor")
        if not cursor:
            break
            
        # Early exit if we've found all needed events (major speedup!)
        if len(events_mapping) >= len(needed_events):
            print(f"✅ Found all {len(events_mapping)} needed events early - stopping fetch")
            break
    
    return events_mapping

@safe_cache_data(ttl=600)
def load_series_list(api_key: str) -> list[dict]:
    client = KalshiClient(api_key=api_key)
    return client.get_series().get("series", [])

# ── Enhanced Candle Loading with DuckDB ──────────────────────────
@safe_cache_data(ttl=300)
def load_candles_from_store(
    ticker: str,
    granularity: str,
    start_ts: int,
    end_ts: int
) -> pd.DataFrame:
    """
    - For '1d', reads the 1h parquet, resamples to daily.
    - Otherwise reads the exact parquet.
    """
    client = KalshiClient(api_key=API_KEY)

    def read_parquet(path):
        # Optimized: only select needed columns and use efficient filtering
        query = f"""
            SELECT end_period_ts, price, volume
            FROM '{path}'
            WHERE end_period_ts >= {start_ts} AND end_period_ts <= {end_ts}
            ORDER BY end_period_ts
        """
        return duckdb_query_optimized(query)

    # --- DAILY: resample the 1h file ---
    if granularity == "1d":
        path_h = os.path.join(CANDLES_DIR, f"candles_{ticker}_1h.parquet")
        if not os.path.exists(path_h):
            return pd.DataFrame()

        df_h = read_parquet(path_h)
        if df_h.empty:
            return df_h

        # unpack & resample...
        df_h["timestamp"]   = pd.to_datetime(df_h["end_period_ts"], unit="s")
        df_h["open_price"]  = df_h["price"].map(lambda p: p["open"])
        df_h["high_price"]  = df_h["price"].map(lambda p: p["high"])
        df_h["low_price"]   = df_h["price"].map(lambda p: p["low"])
        df_h["close_price"] = df_h["price"].map(lambda p: p["close"])
        df_h["volume"]      = df_h["volume"]

        daily = (
            df_h.set_index("timestamp")
                .resample("D")
                .agg({
                    "open_price":"first",
                    "high_price":"max",
                    "low_price":"min",
                    "close_price":"last",
                    "volume":"sum"
                })
                .dropna()
                .reset_index()
        )

        daily["end_period_ts"] = daily["timestamp"].astype(int)//10**9
        daily["price"] = daily.apply(lambda r: {
            "open":  r.open_price,
            "high":  r.high_price,
            "low":   r.low_price,
            "close": r.close_price
        }, axis=1)

        return daily[["end_period_ts","price","volume"]]

    # --- HOURLY or MINUTE: direct read with fallback to live API ---
    path = os.path.join(CANDLES_DIR, f"candles_{ticker}_{granularity}.parquet")
    if not os.path.exists(path):
        payload = client.get_candlesticks(
            ticker, granularity=granularity, start_ts=start_ts, end_ts=end_ts
        )
        df_live = pd.DataFrame(payload.get("candlesticks", []))
        if not df_live.empty:
            duckdb_write_optimized(df_live, path)
        return df_live

    # existing file → read it
    return read_parquet(path)

# ── Enhanced Volume Computation with DuckDB ──────────────────────
@safe_cache_data(ttl=600)
def compute_group_volumes(api_key: str, series_list: list[dict]) -> pd.DataFrame:
    """Optimized: reuse existing markets data instead of duplicate API calls"""
    # 1) Get cached event-to-series mapping
    ev_to_sr = get_events_to_series_mapping(api_key)
    
    # 2) Reuse existing markets data (no duplicate API call)
    df_all = load_active_markets_from_store()
    if df_all.empty:
        return pd.DataFrame(columns=["series_ticker", "title", "volume_24h"])

    # 3) Tag each market with its series
    df_all["series_ticker"] = df_all["event_ticker"].map(ev_to_sr)
    df_all = df_all.dropna(subset=["series_ticker"])

    # 4) Pick the right volume column
    vol_col = "volume_24h" if "volume_24h" in df_all.columns else "volume"

    # 5) Group & sum
    grouped = (
        df_all
        .groupby("series_ticker")[vol_col]
        .sum()
        .reset_index()
        .rename(columns={vol_col: "volume_24h"})
    )

    # 6) Map in the human-readable series title
    title_map = {s["ticker"]: s["title"] for s in series_list}
    grouped["title"] = grouped["series_ticker"].map(title_map).fillna("Unknown")

    return grouped.sort_values("volume_24h", ascending=False)

@safe_cache_data(ttl=600)
def load_series_data_from_store(volume_threshold: int = 1000):
    series_list = load_series_list(API_KEY)

    # Optimized: select only needed columns and use efficient filtering
    query = f"""
      SELECT 
        series_ticker AS ticker,
        title,
        volume_24h
      FROM read_parquet('{SERIES_VOLUMES_PQ}')
      WHERE volume_24h >= {volume_threshold}
      ORDER BY volume_24h DESC
      LIMIT 1000
    """
    df = duckdb_query_optimized(query)
    return series_list, df

# ── New DuckDB Utility Functions ──────────────────────────────────
def get_market_stats_optimized() -> dict:
    """Get market statistics using DuckDB for performance"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return {
                "total_markets": 0,
                "active_markets": 0,
                "total_volume": 0,
                "total_open_interest": 0,
                "avg_volume": 0,
                "max_volume": 0
            }
        query = """
            SELECT 
                COUNT(*) as total_markets,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_markets,
                SUM(COALESCE(volume, 0)) as total_volume,
                SUM(COALESCE(open_interest, 0)) as total_open_interest,
                AVG(COALESCE(volume, 0)) as avg_volume,
                MAX(COALESCE(volume, 0)) as max_volume
            FROM read_parquet(?) 
            WHERE volume > 0
        """
        result = con.execute(query, [ACTIVE_MARKETS_PQ]).fetchone()
        
        return {
            "total_markets": result[0],
            "active_markets": result[1],
            "total_volume": result[2],
            "total_open_interest": result[3],
            "avg_volume": result[4],
            "max_volume": result[5]
        }

def get_top_markets_by_volume(limit: int = 10) -> pd.DataFrame:
    """Get top markets by volume using DuckDB"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    query = f"""
        SELECT 
            ticker,
            title,
            volume,
            yes_bid,
            no_bid,
            close_time
        FROM read_parquet('{ACTIVE_MARKETS_PQ}')
        WHERE volume > 0
        ORDER BY volume DESC
        LIMIT {limit}
    """
    return duckdb_query_optimized(query)

def get_markets_by_series(series_ticker: str) -> pd.DataFrame:
    """Get all markets for a specific series using DuckDB"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    query = """
        SELECT 
            ticker,
            title,
            volume,
            yes_bid,
            no_bid,
            close_time
        FROM read_parquet(?) 
        WHERE event_ticker = ?
        ORDER BY volume DESC
    """
    return duckdb_query_optimized(query, [ACTIVE_MARKETS_PQ, series_ticker])

def get_candle_data_optimized(ticker: str, hours: int = 24) -> pd.DataFrame:
    """Get optimized candle data for a specific time range"""
    with duckdb_context() as con:
        if con is None:
            safe_error("DuckDB connection is not available.")
            return pd.DataFrame()
    end_ts = int(datetime.datetime.now().timestamp())
    start_ts = end_ts - (hours * 3600)
    
    path = os.path.join(CANDLES_DIR, f"candles_{ticker}_1h.parquet")
    if not os.path.exists(path):
        return pd.DataFrame()
    
    query = f"""
        SELECT 
            end_period_ts,
            price,
            volume
        FROM '{path}'
        WHERE end_period_ts >= {start_ts} AND end_period_ts <= {end_ts}
        ORDER BY end_period_ts
    """
    return duckdb_query_optimized(query)

def get_volume_trends(series_ticker: str, days: int = 7) -> pd.DataFrame:
    """Get volume trends for a series over time using DuckDB"""
    # This would require aggregating data across multiple markets
    # Implementation depends on your specific needs
    pass

# ── Performance Monitoring ────────────────────────────────────────
def get_parquet_file_info() -> dict:
    """Get information about Parquet files for monitoring"""
    info = {}
    
    for file_path in [ACTIVE_MARKETS_PQ, SUMMARY_MARKETS_PQ, SERIES_VOLUMES_PQ]:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            info[os.path.basename(file_path)] = {
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "last_modified": datetime.datetime.fromtimestamp(stat.st_mtime),
                "exists": True
            }
        else:
            info[os.path.basename(file_path)] = {"exists": False}
    
    # Check candles directory
    if os.path.exists(CANDLES_DIR):
        candle_files = [f for f in os.listdir(CANDLES_DIR) if f.endswith('.parquet')]
        info['candles'] = {
            "count": len(candle_files),
            "directory": CANDLES_DIR
        }
    
    return info

# ── Utility Functions ───────────────────────────────────────────────────────

def make_ticker_clickable(ticker: str, display_text: str = None, key: str = None) -> bool:
    """
    Create a clickable ticker button that navigates to the Overview page.
    
    Args:
        ticker: The ticker symbol to navigate to
        display_text: Optional text to display (defaults to ticker)
        key: Optional unique key for the button
    
    Returns:
        True if the button was clicked, False otherwise
    """
    if display_text is None:
        display_text = ticker
    
    if key is None:
        key = f"ticker_{ticker}"
    
    # Create a button that looks like a clickable link
    if safe_button(display_text, key=key, help=f"Click to view {ticker} on Overview page"):
        # Store the selected ticker in session state
        session_state = safe_session_state()
        session_state.selected_ticker = ticker
        session_state.selected_title = display_text
        # Switch to Overview page
        safe_switch_page("pages/Overview.py")
        return True
    
    return False

def make_title_clickable(title: str, ticker: str = None, key: str = None) -> bool:
    """
    Create a clickable title button that navigates to the Overview page.
    
    Args:
        title: The title text to display and make clickable
        ticker: The ticker symbol (if available, otherwise title is used)
        key: Optional unique key for the button
    
    Returns:
        True if the button was clicked, False otherwise
    """
    if key is None:
        key = f"title_{title[:20]}_{hash(title) % 10000}"
    
    # Use ticker if available, otherwise use title
    target = ticker if ticker else title
    
    # Create a button that looks like a clickable link
    if safe_button(title, key=key, help=f"Click to view {target} on Overview page"):
        # Store the selected ticker/title in session state
        session_state = safe_session_state()
        session_state.selected_ticker = target
        session_state.selected_title = title
        # Switch to Overview page
        safe_switch_page("pages/Overview.py")
        return True
    
    return False

# ── NEW: Unified Data Access Functions ─────────────────────────────────────

def get_unified_markets(data_sources: list = None) -> pd.DataFrame:
    """
    Get markets from multiple data sources in a unified format.
    
    Args:
        data_sources: List of data sources to include. Options: ['kalshi', 'polymarket']
                     If None, returns all available sources.
    
    Returns:
        DataFrame with markets from all specified sources
    """
    if data_sources is None:
        data_sources = ['kalshi', 'polymarket']
    
    all_markets = []
    
    # Load Kalshi markets
    if 'kalshi' in data_sources and os.path.exists(ACTIVE_MARKETS_PQ):
        try:
            kalshi_df = pd.read_parquet(ACTIVE_MARKETS_PQ)
            # Add source identifier
            kalshi_df['data_source'] = 'kalshi'
            kalshi_df['source_id'] = kalshi_df.get('ticker', '')
            all_markets.append(kalshi_df)
            print(f"📊 Loaded {len(kalshi_df)} Kalshi markets")
        except Exception as e:
            print(f"⚠️ Error loading Kalshi markets: {e}")
    
    # Load Polymarket markets
    if 'polymarket' in data_sources and os.path.exists(POLYMARKET_MARKETS_PQ):
        try:
            polymarket_df = pd.read_parquet(POLYMARKET_MARKETS_PQ)
            # Polymarket data already has data_source field
            all_markets.append(polymarket_df)
            print(f"📊 Loaded {len(polymarket_df)} Polymarket markets")
        except Exception as e:
            print(f"⚠️ Error loading Polymarket markets: {e}")
    
    if not all_markets:
        print("❌ No markets loaded from any source")
        return pd.DataFrame()
    
    # Combine all markets
    combined_df = pd.concat(all_markets, ignore_index=True)
    print(f"✅ Combined {len(combined_df)} total markets")
    
    return combined_df

def get_markets_by_source(data_source: str) -> pd.DataFrame:
    """
    Get markets from a specific data source.
    
    Args:
        data_source: 'kalshi' or 'polymarket'
    
    Returns:
        DataFrame with markets from the specified source
    """
    if data_source == 'kalshi':
        if os.path.exists(ACTIVE_MARKETS_PQ):
            df = pd.read_parquet(ACTIVE_MARKETS_PQ)
            df['data_source'] = 'kalshi'
            df['source_id'] = df.get('ticker', '')
            return df
        else:
            return pd.DataFrame()
    
    elif data_source == 'polymarket':
        if os.path.exists(POLYMARKET_MARKETS_PQ):
            return pd.read_parquet(POLYMARKET_MARKETS_PQ)
        else:
            return pd.DataFrame()
    
    else:
        print(f"❌ Unknown data source: {data_source}")
        return pd.DataFrame()

def get_unified_summary(data_sources: list = None) -> pd.DataFrame:
    """
    Get market summaries from multiple data sources.
    
    Args:
        data_sources: List of data sources to include
    
    Returns:
        DataFrame with market summaries from all specified sources
    """
    if data_sources is None:
        data_sources = ['kalshi', 'polymarket']
    
    all_summaries = []
    
    # Load Kalshi summary
    if 'kalshi' in data_sources and os.path.exists(SUMMARY_MARKETS_PQ):
        try:
            kalshi_summary = pd.read_parquet(SUMMARY_MARKETS_PQ)
            kalshi_summary['data_source'] = 'kalshi'
            all_summaries.append(kalshi_summary)
        except Exception as e:
            print(f"⚠️ Error loading Kalshi summary: {e}")
    
    # Load Polymarket summary
    if 'polymarket' in data_sources and os.path.exists(POLYMARKET_SUMMARY_PQ):
        try:
            polymarket_summary = pd.read_parquet(POLYMARKET_SUMMARY_PQ)
            polymarket_summary['data_source'] = 'polymarket'
            all_summaries.append(polymarket_summary)
        except Exception as e:
            print(f"⚠️ Error loading Polymarket summary: {e}")
    
    if not all_summaries:
        return pd.DataFrame()
    
    # Combine summaries
    combined_summary = pd.concat(all_summaries, ignore_index=True)
    return combined_summary

def get_data_source_status() -> dict:
    """
    Get status of all data sources.
    
    Returns:
        Dictionary with status information for each data source
    """
    try:
        status = {}
        
        # Kalshi status
        kalshi_markets_exist = os.path.exists(ACTIVE_MARKETS_PQ)
        kalshi_summary_exist = os.path.exists(SUMMARY_MARKETS_PQ)
        
        if kalshi_markets_exist:
            try:
                kalshi_df = pd.read_parquet(ACTIVE_MARKETS_PQ)
                kalshi_count = len(kalshi_df)
                kalshi_updated = datetime.datetime.fromtimestamp(os.path.getmtime(ACTIVE_MARKETS_PQ))
            except Exception as e:
                print(f"Warning: Error reading Kalshi data: {e}")
                kalshi_count = 0
                kalshi_updated = None
        else:
            kalshi_count = 0
            kalshi_updated = None
        
        status['kalshi'] = {
            'available': kalshi_markets_exist,
            'markets_count': kalshi_count,
            'summary_available': kalshi_summary_exist,
            'last_updated': kalshi_updated
        }
        
        # Polymarket status
        polymarket_markets_exist = os.path.exists(POLYMARKET_MARKETS_PQ)
        polymarket_summary_exist = os.path.exists(POLYMARKET_SUMMARY_PQ)
        
        if polymarket_markets_exist:
            try:
                polymarket_df = pd.read_parquet(POLYMARKET_MARKETS_PQ)
                polymarket_count = len(polymarket_df)
                polymarket_updated = datetime.datetime.fromtimestamp(os.path.getmtime(POLYMARKET_MARKETS_PQ))
            except Exception as e:
                print(f"Warning: Error reading Polymarket data: {e}")
                polymarket_count = 0
                polymarket_updated = None
        else:
            polymarket_count = 0
            polymarket_updated = None
        
        status['polymarket'] = {
            'available': polymarket_markets_exist,
            'markets_count': polymarket_count,
            'summary_available': polymarket_summary_exist,
            'last_updated': polymarket_updated
        }
        
        return status
        
    except Exception as e:
        print(f"Error in get_data_source_status: {e}")
        # Return safe fallback
        return {
            'kalshi': {
                'available': False,
                'markets_count': 0,
                'summary_available': False,
                'last_updated': None
            },
            'polymarket': {
                'available': False,
                'markets_count': 0,
                'summary_available': False,
                'last_updated': None
            }
        }


