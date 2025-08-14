# kalshi_client.py

import os, requests
import math
import time
import base64
from requests.adapters import HTTPAdapter, Retry
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

class KalshiClient:
    def __init__(self, api_key=None, api_key_id=None, private_key=None):
         """
         A client for Kalshi's API with support for both public and authenticated endpoints.
         """
         # Handle different initialization patterns
         if api_key and api_key.startswith('-----BEGIN'):
             # api_key is actually a private key
             self.private_key = api_key
             self.api_key_id = api_key_id
             self.api_key = None
         elif private_key:
             # Check if private_key is a file path or actual key content
             if os.path.isfile(private_key):
                 # It's a file path, read the file
                 try:
                     with open(private_key, 'r') as f:
                         self.private_key = f.read().strip()
                 except Exception as e:
                     raise ValueError(f"Failed to read private key file {private_key}: {e}")
             else:
                 # It's the actual private key content
                 self.private_key = private_key
             self.api_key_id = api_key_id
             self.api_key = None
         else:
             # Regular API key (for Bearer token auth)
             self.api_key = api_key or os.getenv("KALSHI_API_KEY", "")
             self.private_key = None
             self.api_key_id = api_key_id
         
         # Use the elections API base URL that was working before
         self.base_url = "https://api.elections.kalshi.com"
         
         # Set up headers based on authentication method
         if self.api_key and not self.private_key:
             # Bearer token authentication
             self.headers = {"Authorization": f"Bearer {self.api_key}"}
         else:
             # RSA signature authentication (no default headers)
             self.headers = {}

         # create a single Session with retries on 429/5xx
         self.session = requests.Session()
         retries = Retry(
             total=5,
             backoff_factor=1,
             status_forcelist=[429, 500, 502, 503, 504],
             allowed_methods=["GET", "POST", "PUT", "DELETE"]
         )
         adapter = HTTPAdapter(max_retries=retries)
         self.session.mount("https://", adapter)
         self.session.mount("http://", adapter)
         
         # Update session headers if we have them
         if self.headers:
             self.session.headers.update(self.headers)

    def load_private_key_from_file(self, file_path):
        """Load the private key stored in a file - following user's methodology"""
        with open(file_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,  # or provide a password if your key is encrypted
                backend=default_backend()
            )
        return private_key

    def sign_pss_text(self, private_key: rsa.RSAPrivateKey, text: str) -> str:
        """Sign text with private key using PSS padding - following user's methodology"""
        message = text.encode('utf-8')
        try:
            signature = private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH
                ),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode('utf-8')
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    def _get_private_key(self):
        """Convert the private key string to a private key object"""
        try:
            # The private key should be a PEM-formatted private key
            private_key_data = self.private_key.encode('utf-8')
            private_key = serialization.load_pem_private_key(
                private_key_data,
                password=None
            )
            return private_key
        except Exception as e:
            raise ValueError(f"Failed to load private key: {e}")

    def _sign_request(self, method: str, path: str) -> dict:
        """Generate authentication headers for authenticated endpoints - following user's methodology"""
        if not self.private_key and not self.api_key:
            raise ValueError("Either private key or API key required for authenticated endpoints")
        
        # Check if we have a proper private key (PEM format) for RSA signature
        if self.private_key and self.private_key.startswith('-----BEGIN'):
            try:
                if not self.api_key_id:
                    raise ValueError("API Key ID required for RSA signature authentication")
                
                # Load private key from file if it's a file path
                if os.path.isfile(self.private_key):
                    private_key = self.load_private_key_from_file(self.private_key)
                else:
                    private_key = self._get_private_key()
                
                # Generate timestamp in milliseconds as per user's methodology
                current_time = time.time()
                timestamp = int(current_time * 1000)
                timestamp_str = str(timestamp)
                
                # Create message to sign: timestamp + method + path (exactly as user specified)
                msg_string = timestamp_str + method + path
                
                # Sign the message using user's methodology
                signature = self.sign_pss_text(private_key, msg_string)
                
                return {
                    "KALSHI-ACCESS-KEY": self.api_key_id,
                    "KALSHI-ACCESS-SIGNATURE": signature,
                    "KALSHI-ACCESS-TIMESTAMP": timestamp_str,
                }
            except Exception as e:
                print(f"RSA signature failed: {e}. Falling back to Bearer token.")
                # Fall back to Bearer token if RSA signing fails
                if self.api_key:
                    return {"Authorization": f"Bearer {self.api_key}"}
                else:
                    raise ValueError(f"RSA signature failed and no fallback API key available: {e}")
        else:
            # Use Bearer token authentication
            if not self.api_key:
                raise ValueError("API key required for Bearer token authentication")
            return {"Authorization": f"Bearer {self.api_key}"}

    def _get_api_key_id(self):
        """Get the API key ID from the /api_keys endpoint"""
        try:
            # For the initial API keys call, we need to use basic authentication
            # The API key we have is actually the private key, so we need to get the public key ID first
            
            # Try to use the API key as a Bearer token for the initial call
            # This is a workaround - in production you'd want proper key management
            temp_headers = {"Authorization": f"Bearer {self.api_key}"}
            
            resp = self.session.get(f"{self.base_url}/trade-api/v2/api_keys", headers=temp_headers, timeout=10)
            
            if resp.status_code == 401:
                # If Bearer auth fails, the API key might be a private key
                # In this case, we'll need to create a proper key pair or use a different approach
                raise ValueError("API key appears to be a private key. Please provide the public API key ID.")
            
            resp.raise_for_status()
            
            api_keys_data = resp.json()
            if api_keys_data.get("api_keys"):
                # Use the first API key ID
                self.api_key_id = api_keys_data["api_keys"][0]["api_key_id"]
            else:
                raise ValueError("No API keys found")
                
        except Exception as e:
            # If we can't get the API key ID, we'll use the API key as-is for now
            # This is a fallback for development/testing
            print(f"Could not get API key ID: {e}. Using API key as-is.")
            self.api_key_id = self.api_key

    def get_markets(self, limit=100, status=None, cursor=None, **filters):
         """
         GET /trade-api/v2/markets
         """
         params = {"limit": limit}
         if status:  params["status"] = status
         if cursor:  params["cursor"] = cursor
         # Pull in any other keyword args (e.g., series_ticker, event_ticker)
         params.update(filters)
         resp = self.session.get(f"{self.base_url}/trade-api/v2/markets", params=params, timeout=10)
         resp.raise_for_status()
         return resp.json()

    def get_market(self, ticker):
        """
        GET /trade-api/v2/markets/{ticker}
        """
        resp = self.session.get(f"{self.base_url}/trade-api/v2/markets/{ticker}", timeout=10)
        resp.raise_for_status()
        return resp.json().get("market", {})

    def get_event(self, event_ticker: str) -> dict:
        """
        GET /trade-api/v2/events/{event_ticker}
        """
        resp = self.session.get(
            f"{self.base_url}/trade-api/v2/events/{event_ticker}",
            timeout=10
        )
        resp.raise_for_status()
        # The API returns { "event": { … } }
        return resp.json().get("event", {})    

    def get_events(self, limit: int = 200, cursor: str | None = None, with_nested_markets: bool = False) -> dict:
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        if with_nested_markets:
            params["with_nested_markets"] = "true"
        resp = self.session.get(f"{self.base_url}/trade-api/v2/events", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    

    def get_candlesticks(self, ticker, granularity="1h", start_ts=None, end_ts=None):
        """
        GET /trade-api/v2/series/{series_ticker}/markets/{ticker}/candlesticks
        Uses integer period_interval (1, 60, or 1440).
        """
        # map string → integer
        mapping = {"1m": 1, "1h": 60, "1d": 1440}
        period = mapping.get(granularity)
        if period is None:
            raise ValueError(f"Invalid granularity: {granularity}")

        # discover the series this market belongs to
        market = self.get_market(ticker)
        event  = self.get_event(market["event_ticker"])
        series = event["series_ticker"]

        url    = f"{self.base_url}/trade-api/v2/series/{series}/markets/{ticker}/candlesticks"
        # 3) Chunking logic
        max_intervals = 5000
        period_secs   = period * 60
        all_candles = []
        chunk_start = start_ts

        while chunk_start < end_ts:
            chunk_end = min(end_ts, chunk_start + period_secs * max_intervals)
            params = {
                "period_interval": period,
                "start_ts":        chunk_start,
                "end_ts":          chunk_end,
            }
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()

            data = resp.json().get("candlesticks", [])
            if not data:
                break
            all_candles.extend(data)

            # advance just past the last returned period
            last_ts = data[-1].get("end_period_ts")
            if last_ts is None or last_ts <= chunk_start:
                break
            chunk_start = last_ts + period_secs

        return {"candlesticks": all_candles}

    def get_series(self, category: str = None, include_product_metadata: bool = False) -> dict:
        """
        GET /trade-api/v2/series
        """
        params = {}
        if category:
            params["category"] = category
        if include_product_metadata:
            params["include_product_metadata"] = "true"
        
        resp = self.session.get(f"{self.base_url}/trade-api/v2/series", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_api_keys(self) -> dict:
        """
        GET /trade-api/v2/api_keys
        Get the user's API keys
        """
        headers = self._sign_request("GET", "/trade-api/v2/api_keys")
        resp = self.session.get(f"{self.base_url}/trade-api/v2/api_keys", headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_portfolio_balance(self) -> dict:
        """
        GET /trade-api/v2/portfolio/balance
        Get the user's portfolio balance
        """
        try:
            # Portfolio endpoints are under /trade-api/v2/portfolio/* (exactly as user specified)
            headers = self._sign_request("GET", "/trade-api/v2/portfolio/balance")
            print(f"Portfolio balance headers: {headers}")
            
            resp = self.session.get(f"{self.base_url}/trade-api/v2/portfolio/balance", headers=headers, timeout=10)
            print(f"Portfolio balance response status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("Authentication failed. Response:", resp.text)
                raise ValueError("Authentication failed. Check your API key and permissions.")
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error in get_portfolio_balance: {e}")
            raise

    def get_portfolio_positions(self, limit: int = 100, cursor: str = None) -> dict:
        """
        GET /trade-api/v2/portfolio/positions
        Get the user's portfolio positions
        """
        try:
            # Portfolio endpoints are under /trade-api/v2/portfolio/* (exactly as user specified)
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            
            headers = self._sign_request("GET", "/trade-api/v2/portfolio/positions")
            print(f"Portfolio positions headers: {headers}")
            
            resp = self.session.get(f"{self.base_url}/trade-api/v2/portfolio/positions", params=params, headers=headers, timeout=10)
            print(f"Portfolio positions response status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("Authentication failed. Response:", resp.text)
                raise ValueError("Authentication failed. Check your API key and permissions.")
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error in get_portfolio_positions: {e}")
            raise

    def get_portfolio_orders(self, limit: int = 100, cursor: str = None) -> dict:
        """
        GET /trade-api/v2/portfolio/orders
        Get the user's portfolio orders
        """
        try:
            # Portfolio endpoints are under /trade-api/v2/portfolio/orders (exactly as user specified)
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            
            headers = self._sign_request("GET", "/trade-api/v2/portfolio/orders")
            print(f"Portfolio orders headers: {headers}")
            
            resp = self.session.get(f"{self.base_url}/trade-api/v2/portfolio/orders", params=params, headers=headers, timeout=10)
            print(f"Portfolio orders response status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("Authentication failed. Response:", resp.text)
                raise ValueError("Authentication failed. Check your API key and permissions.")
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error in get_portfolio_orders: {e}")
            raise

    def get_portfolio_fills(self, limit: int = 100, cursor: str = None, ticker: str = None, 
                           order_id: str = None, min_ts: int = None, max_ts: int = None, 
                           use_dollars: bool = False) -> dict:
        """
        GET /trade-api/v2/portfolio/fills
        Get the user's portfolio fills (executed trades)
        """
        try:
            # Portfolio endpoints are under /trade-api/v2/portfolio/* (exactly as user specified)
            params = {"limit": limit}
            if cursor:
                params["cursor"] = cursor
            if ticker:
                params["ticker"] = ticker
            if order_id:
                params["order_id"] = order_id
            if min_ts:
                params["min_ts"] = min_ts
            if max_ts:
                params["max_ts"] = max_ts
            if use_dollars:
                params["use_dollars"] = "true"
            
            headers = self._sign_request("GET", "/trade-api/v2/portfolio/fills")
            print(f"Portfolio fills headers: {headers}")
            
            resp = self.session.get(f"{self.base_url}/trade-api/v2/portfolio/fills", params=params, headers=headers, timeout=10)
            print(f"Portfolio fills response status: {resp.status_code}")
            
            if resp.status_code == 401:
                print("Authentication failed. Response:", resp.text)
                raise ValueError("Authentication failed. Check your API key and permissions.")
            
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error in get_portfolio_fills: {e}")
            raise