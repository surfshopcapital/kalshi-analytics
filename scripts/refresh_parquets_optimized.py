#!/usr/bin/env python3
"""
Optimized Parquet Refresh Script with Advanced DuckDB Features

This script provides enhanced performance through:
- Advanced DuckDB optimizations
- Better compression algorithms
- Performance monitoring
- Batch processing capabilities
- Storage optimization
"""

import os
import sys
import time
import logging
from pathlib import Path

# ── Stub out Streamlit decorators so utils can import safely ─────
import streamlit as _st
_st.cache_data     = lambda *args, **kwargs: (lambda f: f)
_st.cache_resource = lambda f: f

# ── Add project root to path so we can import utils ─────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

import pandas as pd
import duckdb
from datetime import datetime, timedelta

from utils import (
    DATA_DIR,
    ACTIVE_MARKETS_PQ,
    SUMMARY_MARKETS_PQ,
    SERIES_VOLUMES_PQ, 
    CANDLES_DIR,
    API_KEY,
    get_client,
    load_series_list,
    compute_group_volumes,
    # New optimized functions
    duckdb_query_optimized,
    duckdb_write_optimized,
    duckdb_read_optimized,
    duckdb_aggregate_optimized,
    analyze_parquet_performance,
    optimize_parquet_storage,
    batch_process_parquets,
    get_duckdb_performance_stats,
)

# ── Configure logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DATA_DIR, 'refresh_optimized.log'), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ── Ensure data directories exist ────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CANDLES_DIR, exist_ok=True)

class OptimizedParquetRefresher:
    """Advanced Parquet refresh with DuckDB optimizations"""
    
    def __init__(self, api_key: str, min_volume: int = 1000):
        self.api_key = api_key
        self.min_volume = min_volume
        self.client = get_client()
        self.start_time = time.time()
        
        # Performance tracking
        self.stats = {
            "markets_processed": 0,
            "candles_processed": 0,
            "storage_saved_mb": 0,
            "processing_time": 0
        }
    
    def log_performance_stats(self):
        """Log current performance statistics"""
        elapsed = time.time() - self.start_time
        logger.info(f"Performance Stats:")
        logger.info(f"  Markets processed: {self.stats['markets_processed']}")
        logger.info(f"  Candles processed: {self.stats['candles_processed']}")
        logger.info(f"  Storage saved: {self.stats['storage_saved_mb']:.2f} MB")
        logger.info(f"  Processing time: {elapsed:.2f} seconds")
        
        # Log DuckDB performance stats
        try:
            db_stats = get_duckdb_performance_stats()
            if db_stats.get('connection_active'):
                logger.info(f"DuckDB Version: {db_stats.get('version', 'Unknown')}")
            else:
                logger.warning(f"DuckDB connection issue: {db_stats.get('error', 'Unknown error')}")
        except Exception as e:
            logger.warning(f"Could not get DuckDB stats: {e}")
    
    def refresh_active_markets_optimized(self, page_size: int = 1000) -> pd.DataFrame:
        """Refresh active markets with enhanced DuckDB optimizations"""
        logger.info(f"🔄 Refreshing active markets with volume >= ${self.min_volume:,}…")
        
        all_markets = []
        cursor = None
        batch_count = 0
        
        while True:
            try:
                resp = self.client.get_markets(limit=page_size, status="open", cursor=cursor)
                batch = resp.get("markets", [])
                all_markets.extend(batch)
                batch_count += 1
                
                cursor = resp.get("cursor")
                logger.info(f"  → Batch {batch_count}: {len(batch)} markets, cursor: {cursor!r}")
                
                if not cursor:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching markets batch {batch_count}: {e}")
                break
        
        if not all_markets:
            logger.error("No markets fetched")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_markets)
        
        # Filter to markets with volume >= min_volume 
        if "volume" in df.columns:
            original_count = len(df)
            df = df[df["volume"] >= self.min_volume]
            logger.info(f"  → Filtered {original_count} → {len(df)} markets with volume >= ${self.min_volume:,}")
        
        # Use optimized DuckDB write with better compression
        duckdb_write_optimized(df, ACTIVE_MARKETS_PQ, compression="zstd", row_group_size=50000)
        
        # Analyze performance of the written file
        try:
            perf_info = analyze_parquet_performance(ACTIVE_MARKETS_PQ)
            logger.info(f"  → File analysis: {perf_info['file_size_mb']:.2f} MB, {perf_info['row_count']:,} rows")
        except Exception as e:
            logger.warning(f"Could not analyze file performance: {e}")
        
        self.stats["markets_processed"] = len(df)
        logger.info(f"  ✅ Wrote {len(df)} high-volume markets to {ACTIVE_MARKETS_PQ}")
        return df
    
    def refresh_summary_optimized(self, df_active: pd.DataFrame) -> pd.DataFrame:
        """Build summary table with DuckDB optimizations"""
        logger.info("📊 Building optimized summary table…")
        
        # Use DuckDB for the transformation
        with duckdb.connect(':memory:') as con:
            con.register("markets", df_active)
            
            query = """
                SELECT 
                    title as "Title",
                    yes_sub_title as "Yes Subtitle",
                    no_sub_title as "No Subtitle",
                    yes_ask as "Yes Ask",
                    no_ask as "No Ask",
                    last_price as "Last Price",
                    volume as "Volume (24h)",
                    close_time as "Close Time"
                FROM markets
                WHERE volume >= ?
                ORDER BY volume DESC
            """
            
            df = con.execute(query, [self.min_volume]).df()
        
        # Write with optimized compression
        duckdb_write_optimized(df, SUMMARY_MARKETS_PQ, compression="zstd", row_group_size=25000)
        logger.info(f"  ✅ Wrote {len(df)} rows to {SUMMARY_MARKETS_PQ}")
        return df
    
    def write_series_volumes_optimized(self) -> pd.DataFrame:
        """Build series volumes with enhanced performance"""
        logger.info("📈 Building optimized series volumes…")
        
        series_list = load_series_list(self.api_key)
        df_series = compute_group_volumes(self.api_key, series_list)
        
        if not df_series.empty:
            # Use optimized write with better compression
            duckdb_write_optimized(df_series, SERIES_VOLUMES_PQ, compression="zstd", row_group_size=10000)
            
            # Analyze performance
            try:
                perf_info = analyze_parquet_performance(SERIES_VOLUMES_PQ)
                logger.info(f"  → Series volumes: {perf_info['file_size_mb']:.2f} MB, {perf_info['row_count']:,} rows")
            except Exception as e:
                logger.warning(f"Could not analyze series volumes: {e}")
        
        logger.info(f"  ✅ Wrote {len(df_series)} rows to {SERIES_VOLUMES_PQ}")
        return df_series
    
    def get_high_volume_tickers_optimized(self, days: int = 30, granularity: str = "1h") -> list[str]:
        """Get tickers with minimum volume using DuckDB optimizations"""
        parquet_glob = os.path.join(CANDLES_DIR, f"candles_*_{granularity}.parquet")
        cutoff_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # Use optimized DuckDB query with sampling for large datasets
        query = f"""
            SELECT 
                regexp_extract(filename, 'candles_(.*)_{granularity}\\.parquet', 1) AS ticker,
                SUM(volume) AS vol_30d
            FROM read_parquet('{parquet_glob}')
            WHERE end_period_ts >= {cutoff_ts}
            GROUP BY ticker
            HAVING SUM(volume) > {self.min_volume}
            ORDER BY vol_30d DESC
            /*+ USE_SAMPLE(0.05) */
        """
        
        try:
            df = duckdb_query_optimized(query)
            logger.info(f"→ {len(df)} tickers exceed {self.min_volume:,} in last {days} days")
            return df["ticker"].tolist()
        except Exception as e:
            logger.error(f"Error getting high volume tickers: {e}")
            return []
    
    def refresh_candles_optimized(self, days: int = 30, granularity: str = "1h"):
        """Refresh candlesticks with enhanced performance and storage optimization"""
        logger.info(f"🕯️ Refreshing {days}d/{granularity} candles for volume > {self.min_volume:,}…")
        
        # Get high-volume tickers
        tickers = self.get_high_volume_tickers_optimized(days, granularity)
        if not tickers:
            logger.warning("  → No tickers meet the threshold; nothing to do.")
            return
        
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
        
        # Process tickers with progress tracking
        for i, ticker in enumerate(tickers, 1):
            try:
                logger.info(f"  → Processing {ticker} ({i}/{len(tickers)})")
                
                payload = self.client.get_candlesticks(
                    ticker,
                    granularity=granularity,
                    start_ts=start_ts,
                    end_ts=end_ts,
                )
                
                df_c = pd.DataFrame(payload.get("candlesticks", []))
                if df_c.empty:
                    logger.warning(f"    → No data for {ticker}; skipped.")
                    continue
                
                # Write with optimized compression
                path = os.path.join(CANDLES_DIR, f"candles_{ticker}_{granularity}.parquet")
                duckdb_write_optimized(df_c, path, compression="zstd", row_group_size=25000)
                
                # Track statistics
                self.stats["candles_processed"] += len(df_c)
                
                logger.info(f"    ✅ Wrote {len(df_c)} rows for {ticker}")
                
                # Small delay to be respectful to the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"    → Error processing {ticker}: {e}")
                continue
        
        logger.info("🕯️ Candles refresh complete.")
    
    def optimize_existing_storage(self):
        """Optimize existing Parquet files for better compression"""
        logger.info("💾 Optimizing existing Parquet storage...")
        
        files_to_optimize = [
            ACTIVE_MARKETS_PQ,
            SUMMARY_MARKETS_PQ,
            SERIES_VOLUMES_PQ
        ]
        
        total_savings = 0
        
        for file_path in files_to_optimize:
            if os.path.exists(file_path):
                try:
                    logger.info(f"  → Optimizing {os.path.basename(file_path)}...")
                    
                    # Analyze current file
                    current_perf = analyze_parquet_performance(file_path)
                    current_size = current_perf['file_size_mb']
                    
                    # Optimize with ZSTD compression
                    optimized_path = optimize_parquet_storage(file_path, "zstd")
                    
                    # Calculate savings
                    optimized_perf = analyze_parquet_performance(optimized_path)
                    optimized_size = optimized_perf['file_size_mb']
                    savings = current_size - optimized_size
                    total_savings += savings
                    
                    # Replace original with optimized version
                    os.replace(optimized_path, file_path)
                    
                    logger.info(f"    ✅ Saved {savings:.2f} MB ({savings/current_size*100:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"    → Error optimizing {file_path}: {e}")
        
        self.stats["storage_saved_mb"] = total_savings
        logger.info(f"💾 Storage optimization complete. Total savings: {total_savings:.2f} MB")
    
    def run_full_refresh(self):
        """Run the complete optimized refresh process"""
        logger.info("🚀 Starting optimized Parquet refresh...")
        
        try:
            # 1. Refresh active markets
            df_active = self.refresh_active_markets_optimized()
            if df_active.empty:
                logger.error("Failed to refresh active markets")
                return
            
            # 2. Build summary table
            df_summary = self.refresh_summary_optimized(df_active)
            
            # 3. Build series volumes
            self.write_series_volumes_optimized()
            
            # 4. Refresh candlesticks
            self.refresh_candles_optimized(days=30, granularity="1h")
            
            # 5. Optimize storage
            self.optimize_existing_storage()
            
            # 6. Log final statistics
            self.log_performance_stats()
            
            logger.info("🎉 All optimized refresh steps complete!")
            
        except Exception as e:
            logger.error(f"Error during refresh: {e}")
            raise

def main():
    """Main execution function"""
    # Configuration
    MIN_VOLUME = 1000
    
    # Create and run refresher
    refresher = OptimizedParquetRefresher(API_KEY, min_volume=MIN_VOLUME)
    
    try:
        refresher.run_full_refresh()
    except KeyboardInterrupt:
        logger.info("Refresh interrupted by user")
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
