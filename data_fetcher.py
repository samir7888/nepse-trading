"""
NEPSE Data Fetcher Module
Handles all API interactions with NEPSE API
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from config import BASE_URL, API_ENDPOINTS, API_TIMEOUTS, ALTERNATIVE_URLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NepseDataFetcher:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NEPSE-Trading-System/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
            'Cache-Control': 'no-cache'
        })
        
        # Configure connection pooling for better performance
        self.session.verify = True  # Enable SSL verification
        
        # Set connection pool parameters
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # Configure session with retries and timeouts
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_companies_list(self) -> List[Dict]:
        """Fetch list of all companies from NEPSE"""
        max_retries = 3
        timeouts = API_TIMEOUTS['medium']  # Use configurable timeouts
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{API_ENDPOINTS['companies']}"
                timeout = timeouts[attempt]
                logger.info(f"Fetching companies list (attempt {attempt + 1}/{max_retries}, timeout: {timeout}s)...")
                
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                companies = response.json()
                logger.info(f"Successfully fetched {len(companies)} companies")
                return companies
                
            except requests.exceptions.Timeout:
                logger.warning(f"Attempt {attempt + 1} timed out after {timeout}s")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All attempts timed out. API may be slow or unavailable.")
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Attempt {attempt + 1} failed: Connection error")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Connection failed after {max_retries} attempts. Check internet connection.")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch companies after {max_retries} attempts")
                    
            except Exception as e:
                logger.error(f"Unexpected error fetching companies: {e}")
                break
        
        logger.warning("API unavailable - will use sample data for demonstration")
        return []
    
    def get_top_companies(self, count: int = 50) -> List[Dict]:
        """Get top companies by market cap or volume"""
        companies = self.get_companies_list()
        if not companies:
            logger.warning("No companies data from API, using sample data for testing")
            return self._get_sample_companies(count)
        
        # Filter active companies only
        active_companies = [
            company for company in companies 
            if company.get('status', '').upper() == 'ACTIVE'
        ]
        
        if not active_companies:
            active_companies = companies  # Fallback to all companies
        
        # Sort by different criteria based on available data
        try:
            # Try to get price volume data to sort by market activity
            price_volume_data = self._get_price_volume_for_sorting()
            if price_volume_data:
                # Create a mapping of symbols to their trading data
                symbol_to_data = {item.get('symbol'): item for item in price_volume_data}
                
                # Sort companies by trading activity (volume * price)
                def get_trading_score(company):
                    symbol = company.get('symbol', '')
                    trading_data = symbol_to_data.get(symbol, {})
                    volume = float(trading_data.get('totalTradeQuantity', 0) or 0)
                    price = float(trading_data.get('lastTradedPrice', 0) or 0)
                    return volume * price
                
                sorted_companies = sorted(active_companies, key=get_trading_score, reverse=True)
            else:
                # Fallback: sort alphabetically by symbol
                sorted_companies = sorted(active_companies, key=lambda x: x.get('symbol', ''))
                
        except Exception as e:
            logger.warning(f"Error sorting companies: {e}")
            # Final fallback: sort alphabetically
            sorted_companies = sorted(active_companies, key=lambda x: x.get('symbol', ''))
        
        return sorted_companies[:count]
    
    def _get_price_volume_for_sorting(self) -> List[Dict]:
        """Get price volume data for sorting companies"""
        try:
            url = f"{self.base_url}{API_ENDPOINTS['price_volume']}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Could not fetch price volume data for sorting: {e}")
            return []
    
    def _get_sample_companies(self, count: int = 50) -> List[Dict]:
        """Generate sample company data for testing when API is unavailable"""
        sample_companies = [
            {'symbol': 'NABIL', 'name': 'Nabil Bank Limited'},
            {'symbol': 'SCB', 'name': 'Standard Chartered Bank Nepal Limited'},
            {'symbol': 'HBL', 'name': 'Himalayan Bank Limited'},
            {'symbol': 'EBL', 'name': 'Everest Bank Limited'},
            {'symbol': 'BOKL', 'name': 'Bank of Kathmandu Limited'},
            {'symbol': 'NICA', 'name': 'NIC Asia Bank Limited'},
            {'symbol': 'MBL', 'name': 'Machhapuchchhre Bank Limited'},
            {'symbol': 'LBL', 'name': 'Laxmi Bank Limited'},
            {'symbol': 'KBL', 'name': 'Kumari Bank Limited'},
            {'symbol': 'SANIMA', 'name': 'Sanima Bank Limited'},
            {'symbol': 'CBL', 'name': 'Civil Bank Limited'},
            {'symbol': 'PRVU', 'name': 'Prabhu Bank Limited'},
            {'symbol': 'PCBL', 'name': 'Prime Commercial Bank Limited'},
            {'symbol': 'LBBL', 'name': 'Lumbini Bikas Bank Limited'},
            {'symbol': 'ADBL', 'name': 'Agriculture Development Bank Limited'},
            {'symbol': 'HIDCL', 'name': 'Hydroelectricity Investment and Development Company Limited'},
            {'symbol': 'NICL', 'name': 'Nepal Insurance Company Limited'},
            {'symbol': 'NLICL', 'name': 'Nepal Life Insurance Company Limited'},
            {'symbol': 'PICL', 'name': 'Premier Insurance Company Limited'},
            {'symbol': 'LGIL', 'name': 'Lumbini General Insurance Company Limited'},
            {'symbol': 'NLIC', 'name': 'National Life Insurance Company Limited'},
            {'symbol': 'SLICL', 'name': 'Sagarmatha Insurance Company Limited'},
            {'symbol': 'GILB', 'name': 'Global IME Laghubitta Bittiya Sanstha Limited'},
            {'symbol': 'GBLBS', 'name': 'Garima Bikas Bank Limited'},
            {'symbol': 'KLBSL', 'name': 'Kalika Laghubitta Bittiya Sanstha Limited'},
        ]
        
        # Extend the list to reach the requested count
        extended_companies = []
        for i in range(count):
            base_company = sample_companies[i % len(sample_companies)]
            extended_companies.append({
                'symbol': f"{base_company['symbol']}{'' if i < len(sample_companies) else str(i//len(sample_companies))}",
                'name': base_company['name'],
                'marketCap': 1000000000 - i * 10000000,  # Decreasing market cap
                'volume': 100000 - i * 1000
            })
        
        return extended_companies[:count]
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get current stock data for a symbol from PriceVolume endpoint"""
        try:
            # Get all price volume data and filter for the symbol
            url = f"{self.base_url}{API_ENDPOINTS['price_volume']}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                # Find the specific symbol in the list
                for item in data:
                    if item.get('symbol') == symbol:
                        return item
            
            logger.warning(f"Symbol {symbol} not found in price volume data")
            return None
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 1095) -> pd.DataFrame:
        """Get historical data for a symbol using local backend DailyScripPriceGraph endpoint"""
        max_retries = 2
        timeouts = API_TIMEOUTS['long']  # Use longer timeouts for historical data
        
        for attempt in range(max_retries):
            try:
                # Local backend uses URL path parameter for symbol
                url = f"{self.base_url}{API_ENDPOINTS['historical']}/{symbol}"
                timeout = timeouts[attempt] if attempt < len(timeouts) else timeouts[-1]
                logger.info(f"Fetching historical data for {symbol} (attempt {attempt + 1}/{max_retries}, timeout: {timeout}s)...")
                
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                data = response.json()
                if not data or not isinstance(data, list):
                    logger.warning(f"No historical data from local backend for {symbol}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        return self._generate_sample_historical_data(symbol, days)
                
                # Convert the time-series data from local backend
                # Local backend returns [[timestamp, value], [timestamp, value], ...]
                df_data = []
                for item in data:
                    if isinstance(item, list) and len(item) >= 2:
                        timestamp = item[0]
                        price = item[1]
                        
                        # Convert timestamp to datetime
                        if isinstance(timestamp, (int, float)):
                            # Unix timestamp in milliseconds
                            date = pd.to_datetime(timestamp, unit='ms')
                        else:
                            # Try to parse as string
                            date = pd.to_datetime(timestamp)
                        
                        df_data.append({
                            'date': date,
                            'close': float(price),
                            'open': float(price),  # Use close as open (approximation)
                            'high': float(price) * 1.02,  # Approximate high (2% above close)
                            'low': float(price) * 0.98,   # Approximate low (2% below close)
                            'volume': 1000  # Default volume
                        })
                
                if not df_data:
                    logger.warning(f"Could not parse historical data for {symbol}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        return self._generate_sample_historical_data(symbol, days)
                
                df = pd.DataFrame(df_data)
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                
                # Filter to requested number of days
                if len(df) > days:
                    df = df.tail(days)
                
                logger.info(f"Fetched {len(df)} historical records for {symbol} from local backend")
                return df
                
            except requests.exceptions.Timeout:
                logger.warning(f"Historical data request for {symbol} timed out after {timeout}s")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error fetching historical data for {symbol}")
                logger.warning("Make sure local backend server is running: cd backend/example && python NepseServer.py")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    
            except Exception as e:
                logger.warning(f"Error fetching historical data for {symbol}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        logger.info(f"Using sample data for {symbol} - local backend unavailable")
        return self._generate_sample_historical_data(symbol, days)
    
    def _generate_sample_historical_data(self, symbol: str, days: int = 1095) -> pd.DataFrame:
        """Generate realistic sample historical data for testing"""
        import numpy as np
        
        # Create date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Remove weekends (NEPSE doesn't trade on weekends)
        dates = dates[dates.weekday < 5]
        
        # Generate realistic price data with trends
        np.random.seed(hash(symbol) % 2**32)  # Consistent data for same symbol
        
        # Base price varies by symbol
        base_price = 100 + (hash(symbol) % 500)
        
        # Generate price movements with trend
        returns = np.random.normal(0.001, 0.02, len(dates))  # Slight upward bias
        
        # Add some momentum periods (simulate ATH scenarios)
        momentum_periods = np.random.choice(len(dates), size=max(1, len(dates)//100), replace=False)
        for period in momentum_periods:
            start_idx = max(0, period - 30)
            end_idx = min(len(dates), period + 30)
            returns[start_idx:end_idx] += np.random.normal(0.005, 0.01, end_idx - start_idx)
        
        # Calculate prices
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC data
        df = pd.DataFrame(index=dates)
        df['close'] = prices
        
        # Generate realistic OHLC relationships
        daily_volatility = np.random.uniform(0.01, 0.05, len(dates))
        df['high'] = df['close'] * (1 + daily_volatility * np.random.uniform(0.5, 1.0, len(dates)))
        df['low'] = df['close'] * (1 - daily_volatility * np.random.uniform(0.5, 1.0, len(dates)))
        df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0]) * (1 + np.random.normal(0, 0.01, len(dates)))
        
        # Ensure OHLC relationships are correct
        df['high'] = np.maximum.reduce([df['open'], df['high'], df['low'], df['close']])
        df['low'] = np.minimum.reduce([df['open'], df['high'], df['low'], df['close']])
        
        # Generate volume
        base_volume = 1000 + (hash(symbol) % 10000)
        volume_multiplier = 1 + np.abs(returns) * 10  # Higher volume on big moves
        df['volume'] = (base_volume * volume_multiplier * np.random.uniform(0.5, 2.0, len(dates))).astype(int)
        
        # Round prices to 2 decimal places
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].round(2)
        
        logger.info(f"Generated {len(df)} sample historical records for {symbol}")
        return df
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        max_retries = 3
        timeouts = [30, 60, 90]  # Increased timeouts for slow API
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}{API_ENDPOINTS['market_status']}"
                timeout = timeouts[attempt]
                logger.info(f"Checking market status (attempt {attempt + 1}/{max_retries}, timeout: {timeout}s)...")
                
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Market status: {result.get('isOpen', 'UNKNOWN')}")
                return result
                
            except requests.exceptions.Timeout:
                logger.warning(f"Market status check timed out after {timeout}s")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error checking market status")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.warning(f"Error fetching market status: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        logger.warning("Could not fetch market status - API may be unavailable")
        return {"isOpen": "UNKNOWN", "asOf": "", "id": 0}
    
    def get_current_market_data(self) -> Dict[str, Dict]:
        """Get current market data for all symbols"""
        try:
            url = f"{self.base_url}{API_ENDPOINTS['price_volume']}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                # Convert list to dictionary with symbol as key
                market_data = {}
                for item in data:
                    symbol = item.get('symbol')
                    if symbol:
                        # Map NEPSE API fields to our expected format
                        # Try multiple field names for compatibility
                        last_price = (item.get('lastTradedPrice') or 
                                    item.get('ltp') or 
                                    item.get('closePrice') or 0)
                        
                        market_data[symbol] = {
                            'close': last_price,
                            'high': item.get('highPrice', last_price),
                            'low': item.get('lowPrice', last_price),
                            'open': item.get('openPrice', last_price),
                            'volume': (item.get('totalTradeQuantity') or 
                                     item.get('shareTraded') or 
                                     item.get('volume') or 0),
                            'previousClose': item.get('previousClose', 0),
                            'percentageChange': item.get('percentageChange', 0),
                            # Debug info
                            'raw_data': item  # Include raw data for debugging
                        }
                return market_data
            
            return {}
        except Exception as e:
            logger.error(f"Error fetching current market data: {e}")
            return {}
    
    def batch_fetch_historical_data(self, symbols: List[str], delay: float = 1.0) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for multiple symbols with rate limiting"""
        historical_data = {}
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Fetching data for {symbol} ({i+1}/{len(symbols)})")
            
            df = self.get_historical_data(symbol)
            if not df.empty:
                historical_data[symbol] = df
            
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
        
        return historical_data