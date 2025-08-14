#!/usr/bin/env python3
"""
Parquet Storage Optimization Script

This script optimizes existing Parquet files by:
1. Converting from Snappy to ZSTD compression
2. Optimizing row group sizes
3. Analyzing compression ratios
4. Providing storage savings reports
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import time

# ── Add project root to path so we can import utils ─────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, ROOT)

import duckdb
from utils import (
    DATA_DIR,
    CANDLES_DIR,
    analyze_parquet_performance,
    optimize_parquet_storage,
    batch_process_parquets
)

# ── Configure logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(DATA_DIR, 'storage_optimization.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StorageOptimizer:
    """Optimize Parquet file storage with advanced compression"""
    
    def __init__(self, data_dir: str, target_compression: str = "zstd"):
        self.data_dir = data_dir
        self.target_compression = target_compression
        self.optimization_stats = {
            "files_processed": 0,
            "total_original_size": 0,
            "total_optimized_size": 0,
            "total_savings": 0,
            "errors": []
        }
    
    def analyze_directory(self, directory: str) -> dict:
        """Analyze all Parquet files in a directory"""
        logger.info(f"🔍 Analyzing directory: {directory}")
        
        if not os.path.exists(directory):
            logger.warning(f"Directory {directory} does not exist")
            return {}
        
        parquet_files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
        logger.info(f"Found {len(parquet_files)} Parquet files")
        
        analysis_results = {}
        
        for filename in parquet_files:
            file_path = os.path.join(directory, filename)
            try:
                perf_info = analyze_parquet_performance(file_path)
                analysis_results[filename] = perf_info
                logger.info(f"  → {filename}: {perf_info['file_size_mb']:.2f} MB, {perf_info['row_count']:,} rows")
            except Exception as e:
                logger.error(f"  → Error analyzing {filename}: {e}")
                analysis_results[filename] = {"error": str(e)}
        
        return analysis_results
    
    def optimize_file(self, file_path: str, backup: bool = True) -> dict:
        """Optimize a single Parquet file"""
        try:
            # Analyze original file
            original_perf = analyze_parquet_performance(file_path)
            original_size = original_perf['file_size_mb']
            
            logger.info(f"🔄 Optimizing {os.path.basename(file_path)}...")
            logger.info(f"  → Original: {original_size:.2f} MB, {original_perf['row_count']:,} rows")
            
            # Create backup if requested
            if backup:
                backup_path = file_path.replace('.parquet', '_backup.parquet')
                import shutil
                shutil.copy2(file_path, backup_path)
                logger.info(f"  → Backup created: {os.path.basename(backup_path)}")
            
            # Optimize with ZSTD compression
            optimized_path = optimize_parquet_storage(file_path, self.target_compression)
            
            # Analyze optimized file
            optimized_perf = analyze_parquet_performance(optimized_path)
            optimized_size = optimized_perf['file_size_mb']
            
            # Calculate savings
            savings = original_size - optimized_size
            savings_percent = (savings / original_size) * 100
            
            # Replace original with optimized version
            os.replace(optimized_path, file_path)
            
            # Update statistics
            self.optimization_stats["files_processed"] += 1
            self.optimization_stats["total_original_size"] += original_size
            self.optimization_stats["total_optimized_size"] += optimized_size
            self.optimization_stats["total_savings"] += savings
            
            logger.info(f"  ✅ Optimized: {optimized_size:.2f} MB")
            logger.info(f"  💾 Savings: {savings:.2f} MB ({savings_percent:.1f}%)")
            
            return {
                "success": True,
                "original_size": original_size,
                "optimized_size": optimized_size,
                "savings": savings,
                "savings_percent": savings_percent
            }
            
        except Exception as e:
            error_msg = f"Error optimizing {os.path.basename(file_path)}: {e}"
            logger.error(error_msg)
            self.optimization_stats["errors"].append(error_msg)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def optimize_directory(self, directory: str, backup: bool = True, dry_run: bool = False) -> dict:
        """Optimize all Parquet files in a directory"""
        logger.info(f"🚀 Starting optimization of directory: {directory}")
        
        if not os.path.exists(directory):
            logger.error(f"Directory {directory} does not exist")
            return {}
        
        parquet_files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
        
        if not parquet_files:
            logger.info("No Parquet files found to optimize")
            return {}
        
        logger.info(f"Found {len(parquet_files)} Parquet files to optimize")
        
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No files will be modified")
        
        results = {}
        
        for filename in parquet_files:
            file_path = os.path.join(directory, filename)
            
            if dry_run:
                # Just analyze in dry run mode
                try:
                    perf_info = analyze_parquet_performance(file_path)
                    results[filename] = {
                        "dry_run": True,
                        "current_size": perf_info['file_size_mb'],
                        "row_count": perf_info['row_count']
                    }
                    logger.info(f"  → {filename}: {perf_info['file_size_mb']:.2f} MB (would optimize)")
                except Exception as e:
                    logger.error(f"  → Error analyzing {filename}: {e}")
                    results[filename] = {"error": str(e)}
            else:
                # Actually optimize the file
                result = self.optimize_file(file_path, backup=backup)
                results[filename] = result
        
        return results
    
    def print_summary(self):
        """Print optimization summary"""
        logger.info("📊 Optimization Summary")
        logger.info("=" * 50)
        
        if self.optimization_stats["files_processed"] > 0:
            total_savings = self.optimization_stats["total_savings"]
            total_original = self.optimization_stats["total_original_size"]
            savings_percent = (total_savings / total_original) * 100
            
            logger.info(f"Files processed: {self.optimization_stats['files_processed']}")
            logger.info(f"Total original size: {total_original:.2f} MB")
            logger.info(f"Total optimized size: {self.optimization_stats['total_optimized_size']:.2f} MB")
            logger.info(f"Total storage saved: {total_savings:.2f} MB ({savings_percent:.1f}%)")
        else:
            logger.info("No files were processed")
        
        if self.optimization_stats["errors"]:
            logger.info(f"Errors encountered: {len(self.optimization_stats['errors'])}")
            for error in self.optimization_stats["errors"]:
                logger.error(f"  → {error}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Optimize Parquet file storage")
    parser.add_argument(
        "--data-dir", 
        default=DATA_DIR,
        help="Directory containing Parquet files to optimize"
    )
    parser.add_argument(
        "--candles-dir",
        default=CANDLES_DIR,
        help="Directory containing candle Parquet files"
    )
    parser.add_argument(
        "--compression",
        default="zstd",
        choices=["zstd", "gzip", "snappy"],
        help="Target compression algorithm"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup files before optimization"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze files without making changes"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze files, don't optimize"
    )
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = StorageOptimizer(args.data_dir, args.compression)
    
    try:
        if args.analyze_only:
            # Just analyze main data files
            logger.info("🔍 Analysis mode - analyzing main data files")
            main_analysis = optimizer.analyze_directory(args.data_dir)
            
            # Analyze candles directory if it exists
            if os.path.exists(args.candles_dir):
                logger.info("🔍 Analyzing candles directory")
                candles_analysis = optimizer.analyze_directory(args.candles_dir)
                
                # Combine results
                all_analysis = {**main_analysis, **candles_analysis}
            else:
                all_analysis = main_analysis
            
            logger.info(f"📊 Analysis complete. Analyzed {len(all_analysis)} files")
            
        else:
            # Optimize main data files
            logger.info("🚀 Starting optimization of main data files")
            main_results = optimizer.optimize_directory(
                args.data_dir, 
                backup=args.backup, 
                dry_run=args.dry_run
            )
            
            # Optimize candles directory if it exists and not dry run
            if os.path.exists(args.candles_dir) and not args.dry_run:
                logger.info("🚀 Starting optimization of candles directory")
                candles_results = optimizer.optimize_directory(
                    args.candles_dir,
                    backup=args.backup,
                    dry_run=args.dry_run
                )
                
                # Combine results
                all_results = {**main_results, **candles_results}
            else:
                all_results = main_results
            
            # Print summary
            optimizer.print_summary()
            
            logger.info(f"🎉 Optimization complete. Processed {len(all_results)} files")
        
    except KeyboardInterrupt:
        logger.info("Optimization interrupted by user")
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
