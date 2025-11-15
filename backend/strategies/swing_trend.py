"""
Swing Trend Baseline Strategy.
Uses EMA crossover, RSI, and price breakouts with ATR-based stops.
"""
import pandas as pd
import talib
from typing import Optional, Dict
from ..config import settings


class SwingTrendStrategy:
    """Swing Trend Baseline strategy implementation."""
    
    def __init__(self):
        """Initialize strategy with parameters from settings."""
        self.ema_fast = settings.EMA_FAST
        self.ema_slow = settings.EMA_SLOW
        self.rsi_length = settings.RSI_LENGTH
        self.lookback = settings.LOOKBACK
        self.atr_length = settings.ATR_LENGTH
        self.rr_ratio = settings.RR_RATIO
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators.
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        
        Returns:
            DataFrame with added indicator columns
        """
        # Make copy to avoid modifying original
        df = df.copy()
        
        # Convert to numpy arrays for TA-Lib
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # Calculate EMAs
        df['ema_fast'] = talib.EMA(close, timeperiod=self.ema_fast)
        df['ema_slow'] = talib.EMA(close, timeperiod=self.ema_slow)
        
        # Calculate RSI
        df['rsi'] = talib.RSI(close, timeperiod=self.rsi_length)
        
        # Calculate ATR
        df['atr'] = talib.ATR(high, low, close, timeperiod=self.atr_length)
        
        # Calculate highest high and lowest low for breakout detection
        df['highest_high'] = df['high'].rolling(window=self.lookback).max()
        df['lowest_low'] = df['low'].rolling(window=self.lookback).min()
        
        # Determine trend
        df['uptrend'] = df['ema_fast'] > df['ema_slow']
        df['downtrend'] = df['ema_fast'] < df['ema_slow']
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Generate trading signal based on strategy rules.
        
        Args:
            df: DataFrame with OHLCV data and indicators
        
        Returns:
            Dict with signal details or None if no signal
            {
                'side': 'long' or 'short',
                'entry': entry price,
                'stop': stop loss price,
                'tp': take profit price
            }
        """
        # Calculate indicators if not already present
        if 'ema_fast' not in df.columns:
            df = self.calculate_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Check for missing data
        if pd.isna(latest['ema_fast']) or pd.isna(latest['rsi']) or pd.isna(latest['atr']):
            return None
        
        # Long signal conditions:
        # 1. Uptrend (EMA fast > EMA slow)
        # 2. RSI > 50 (bullish momentum)
        # 3. Close breaks above highest high of last N bars
        if (
            latest['uptrend'] and
            latest['rsi'] > 50 and
            latest['close'] > previous['highest_high']
        ):
            entry_price = latest['close']
            atr = latest['atr']
            
            # Stop loss: 2 * ATR below entry
            stop_loss = entry_price - (2 * atr)
            
            # Take profit: risk-reward ratio * risk distance
            risk_distance = entry_price - stop_loss
            take_profit = entry_price + (self.rr_ratio * risk_distance)
            
            return {
                'side': 'long',
                'entry': float(entry_price),
                'stop': float(stop_loss),
                'tp': float(take_profit),
                'atr': float(atr),
                'rsi': float(latest['rsi'])
            }
        
        # Short signal conditions:
        # 1. Downtrend (EMA fast < EMA slow)
        # 2. RSI < 50 (bearish momentum)
        # 3. Close breaks below lowest low of last N bars
        if (
            latest['downtrend'] and
            latest['rsi'] < 50 and
            latest['close'] < previous['lowest_low']
        ):
            entry_price = latest['close']
            atr = latest['atr']
            
            # Stop loss: 2 * ATR above entry
            stop_loss = entry_price + (2 * atr)
            
            # Take profit: risk-reward ratio * risk distance
            risk_distance = stop_loss - entry_price
            take_profit = entry_price - (self.rr_ratio * risk_distance)
            
            return {
                'side': 'short',
                'entry': float(entry_price),
                'stop': float(stop_loss),
                'tp': float(take_profit),
                'atr': float(atr),
                'rsi': float(latest['rsi'])
            }
        
        return None
