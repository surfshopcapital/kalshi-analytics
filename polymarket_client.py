# polymarket_client.py

import requests
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import time

class PolymarketClient:
    def __init__(self):
        """
        A client for Polymarket's Gamma API for fetching market data.
        No authentication required for public endpoints.
        """
        self.base_url = "https://gamma-api.polymarket.com"
        
        # Set up session with retries
        self.session = requests.Session()
        retries = requests.adapters.Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        
        # Rate limiting - be respectful
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Simple rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_markets(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all markets from Polymarket.
        
        Args:
            limit: Optional limit on number of markets to return
            
        Returns:
            List of market dictionaries
        """
        self._rate_limit()
        
        try:
            response = self.session.get(f"{self.base_url}/markets", timeout=30)
            response.raise_for_status()
            markets = response.json()
            
            if limit:
                markets = markets[:limit]
            
            return markets
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Polymarket markets: {e}")
            return []
    
    def get_markets_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Fetch markets filtered by category.
        
        Args:
            category: Category to filter by (e.g., 'US-current-affairs', 'crypto')
            
        Returns:
            List of markets in the specified category
        """
        all_markets = self.get_markets()
        return [m for m in all_markets if m.get('category') == category]
    
    def get_active_markets(self) -> List[Dict[str, Any]]:
        """
        Fetch only active (non-closed) markets.
        
        Returns:
            List of active markets
        """
        all_markets = self.get_markets()
        # Filter for markets that are not closed
        active_markets = [m for m in all_markets if not m.get('closed', True)]
        
        print(f"📊 Found {len(active_markets)} active markets out of {len(all_markets)} total")
        return active_markets
    
    def get_markets_by_status(self, status: str = 'open') -> List[Dict[str, Any]]:
        """
        Fetch markets by specific status.
        
        Args:
            status: Market status ('open', 'closed', 'inactive')
            
        Returns:
            List of markets with the specified status
        """
        all_markets = self.get_markets()
        
        if status == 'open':
            # Open markets are those that are not closed
            return [m for m in all_markets if not m.get('closed', True)]
        elif status == 'closed':
            # Closed markets
            return [m for m in all_markets if m.get('closed', False)]
        else:
            # Return all markets
            return all_markets
    
    def get_high_volume_markets(self, min_volume: float = 1000.0) -> List[Dict[str, Any]]:
        """
        Fetch markets with volume above a threshold.
        
        Args:
            min_volume: Minimum volume threshold
            
        Returns:
            List of high-volume markets
        """
        all_markets = self.get_markets()
        return [m for m in all_markets if m.get('volumeNum', 0) >= min_volume]

def normalize_polymarket_market(market: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize Polymarket market data to a common format.
    
    Args:
        market: Raw Polymarket market data
        
    Returns:
        Normalized market data
    """
    # Parse outcomes (they come as JSON strings)
    outcomes = []
    outcome_prices = {}
    
    try:
        if isinstance(market.get('outcomes'), str):
            outcomes = json.loads(market.get('outcomes', '[]'))
        if isinstance(market.get('outcomePrices'), str):
            outcome_prices = json.loads(market.get('outcomePrices', '[]'))
    except json.JSONDecodeError:
        outcomes = []
        outcome_prices = {}
    
    # Convert outcome prices to dict if it's a list
    if isinstance(outcome_prices, list) and len(outcomes) == len(outcome_prices):
        outcome_prices = dict(zip(outcomes, outcome_prices))
    
    # Parse dates
    open_time = None
    close_time = None
    
    try:
        if market.get('createdAt'):
            open_time = datetime.fromisoformat(market['createdAt'].replace('Z', '+00:00'))
        if market.get('endDate'):
            close_time = datetime.fromisoformat(market['endDate'].replace('Z', '+00:00'))
    except (ValueError, TypeError):
        pass
    
    # Determine status
    if market.get('closed'):
        status = 'closed'
    elif market.get('active'):
        status = 'open'
    else:
        status = 'inactive'
    
    # Normalize the data
    normalized = {
        'market_id': str(market.get('id', '')),
        'title': market.get('question', ''),
        'category': market.get('category', ''),
        'outcomes': outcomes,
        'outcome_prices': outcome_prices,
        'last_price': float(market.get('lastTradePrice', 0)),
        'yes_bid': float(market.get('bestBid', 0)),
        'yes_ask': float(market.get('bestAsk', 0)),
        'volume_24h': float(market.get('volume24hr', 0)),
        'volume_1wk': float(market.get('volume1wk', 0)),
        'volume_1mo': float(market.get('volume1mo', 0)),
        'volume_total': float(market.get('volumeNum', 0)),
        'liquidity': float(market.get('liquidityNum', 0)),
        'close_time': close_time,
        'open_time': open_time,
        'status': status,
        'closed': bool(market.get('closed', False)),
        'price_change_1h': float(market.get('oneHourPriceChange', 0)),
        'price_change_24h': float(market.get('oneDayPriceChange', 0)),
        'price_change_1w': float(market.get('oneWeekPriceChange', 0)),
        'spread': float(market.get('spread', 0)),
        'data_source': 'polymarket',
        'source_id': str(market.get('id', '')),
        'slug': market.get('slug', ''),
        'description': market.get('description', ''),
        'market_type': market.get('marketType', ''),
    }
    
    return normalized

def get_client() -> PolymarketClient:
    """
    Get a Polymarket client instance.
    Similar to the get_client() function in utils.py for Kalshi.
    
    Returns:
        PolymarketClient instance
    """
    return PolymarketClient()

def fetch_and_normalize_polymarket_markets(
    min_volume: float = 1000.0,
    limit: Optional[int] = None,
    active_only: bool = False
) -> pd.DataFrame:
    """
    Fetch Polymarket markets and normalize them to a DataFrame.
    
    Args:
        min_volume: Minimum volume threshold
        limit: Optional limit on number of markets
        active_only: If True, fetch only active (non-closed) markets
        
    Returns:
        DataFrame with normalized market data
    """
    client = get_client()
    
    # Fetch markets based on parameters
    if active_only:
        print("🎯 Fetching only ACTIVE Polymarket markets...")
        markets = client.get_active_markets()
    elif min_volume > 0:
        print(f"📊 Fetching Polymarket markets with volume >= ${min_volume:,}...")
        markets = client.get_high_volume_markets(min_volume)
    else:
        print(f"📊 Fetching all Polymarket markets (limit: {limit or 'none'})...")
        markets = client.get_markets(limit)
    
    print(f"📥 Raw markets fetched: {len(markets)}")
    
    # Normalize each market
    normalized_markets = []
    for market in markets:
        try:
            normalized = normalize_polymarket_market(market)
            normalized_markets.append(normalized)
        except Exception as e:
            print(f"Error normalizing market {market.get('id', 'unknown')}: {e}")
            continue
    
    # Convert to DataFrame
    if normalized_markets:
        df = pd.DataFrame(normalized_markets)
        print(f"✅ Normalized {len(df)} markets successfully")
        return df
    else:
        print("❌ No markets were normalized successfully")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test the client
    print("🧪 Testing Polymarket Client...")
    
    client = get_client()
    markets = client.get_markets(limit=3)
    
    print(f"📊 Fetched {len(markets)} markets")
    
    if markets:
        # Test normalization
        normalized = normalize_polymarket_market(markets[0])
        print(f"✅ Normalization successful")
        print(f"📋 Normalized fields: {list(normalized.keys())}")
        
        # Test DataFrame creation
        df = fetch_and_normalize_polymarket_markets(limit=5)
        print(f"📊 DataFrame created: {df.shape}")
        print(f"📋 DataFrame columns: {list(df.columns)}")
