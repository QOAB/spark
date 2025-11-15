"""
Market Data Service.
Fetches OHLCV data and ticker information from Binance via ccxt.
"""
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime
from typing import Dict, Optional
from ..config import settings


class MarketDataService:
    """Market data service using ccxt for Binance integration."""
    
    def __init__(self):
        """Initialize ccxt exchange instance."""
        self.exchange = ccxt.binance({
            'apiKey': settings.EXCHANGE_API_KEY,
            'secret': settings.EXCHANGE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
        
        # Use testnet if enabled
        if settings.EXCHANGE_TESTNET:
            self.exchange.set_sandbox_mode(True)
            # Override with testnet URL
            self.exchange.urls['api'] = {
                'public': 'https://testnet.binance.vision/api/v3',
                'private': 'https://testnet.binance.vision/api/v3',
            }
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from exchange.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
            limit: Number of candles to fetch
            since: Unix timestamp to fetch from
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            raise Exception(f"Error fetching OHLCV data: {str(e)}")
    
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker information.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
        
        Returns:
            Dict with ticker data (bid, ask, last, etc.)
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            raise Exception(f"Error fetching ticker: {str(e)}")
    
    async def get_balance(self, currency: str = "USDT") -> float:
        """
        Get account balance for specific currency.
        
        Args:
            currency: Currency symbol (e.g., 'USDT', 'BTC')
        
        Returns:
            Available balance
        """
        try:
            balance = await self.exchange.fetch_balance()
            return float(balance.get(currency, {}).get('free', 0.0))
        except Exception as e:
            raise Exception(f"Error fetching balance: {str(e)}")
    
    async def close(self):
        """Close exchange connection."""
        await self.exchange.close()
