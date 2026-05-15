"""
CVD (Cumulative Volume Delta) Calculator
Tracks volume imbalances to identify accumulation/distribution pressure
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CVDPoint:
    """Single CVD data point"""
    timestamp: int
    cvd: float
    volume: float
    price: float
    bar_index: int


class CVDCalculator:
    """
    Cumulative Volume Delta Calculator.
    
    CVD = Σ(Buy Volume - Sell Volume)
    
    Detection Methods:
    - Positive CVD trending up: Accumulation (bullish pressure)
    - Negative CVD trending down: Distribution (bearish pressure)
    - CVD divergence from price: Potential reversal signal
    """
    
    def __init__(self):
        self.cvd_history: List[CVDPoint] = []
    
    def calculate_from_trades(self, trades: List[Dict]) -> pd.DataFrame:
        """
        Calculate CVD from individual trade data (buy/sell volume).
        
        Args:
            trades: List of trade dictionaries with keys:
                   {'timestamp', 'price', 'volume', 'is_buy'}
        
        Returns:
            DataFrame with CVD values
        """
        if not trades:
            return pd.DataFrame()
        
        df_trades = pd.DataFrame(trades)
        
        # Separate buy and sell volumes
        df_trades['buy_volume'] = df_trades.apply(
            lambda row: row['volume'] if row['is_buy'] else 0,
            axis=1
        )
        df_trades['sell_volume'] = df_trades.apply(
            lambda row: row['volume'] if not row['is_buy'] else 0,
            axis=1
        )
        
        # Calculate cumulative
        df_trades['cvd'] = (
            df_trades['buy_volume'].cumsum() - 
            df_trades['sell_volume'].cumsum()
        )
        
        return df_trades[['timestamp', 'price', 'cvd']]
    
    def calculate_from_ohlcv(self, df: pd.DataFrame) -> pd.Series:
        """
        Estimate CVD from OHLCV data (approximation when trade data unavailable).
        
        Method: Close > Open → bullish, Close < Open → bearish
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Series with approximate CVD values
        """
        if len(df) == 0:
            return pd.Series()
        
        df = df.copy()
        
        # Estimate volume direction based on close vs open
        df['volume_delta'] = df.apply(
            lambda row: row['volume'] if row['close'] > row['open'] else -row['volume'],
            axis=1
        )
        
        # Calculate cumulative volume delta
        cvd = df['volume_delta'].cumsum()
        
        return cvd
    
    def detect_accumulation(self, cvd: pd.Series, 
                           lookback: int = 50,
                           threshold_percentile: float = 75) -> bool:
        """
        Detect if CVD shows accumulation pattern.
        
        Args:
            cvd: CVD series
            lookback: Bars to look back
            threshold_percentile: CVD strength threshold
        
        Returns:
            True if accumulation detected
        """
        if len(cvd) < lookback:
            return False
        
        recent_cvd = cvd.iloc[-lookback:]
        
        # Check if CVD is trending up (positive slope)
        slope = (recent_cvd.iloc[-1] - recent_cvd.iloc[0]) / lookback
        
        # Check if current CVD is above percentile
        strength = np.percentile(recent_cvd.abs().values, threshold_percentile)
        is_strong = abs(recent_cvd.iloc[-1]) > strength
        
        return slope > 0 and is_strong and recent_cvd.iloc[-1] > 0
    
    def detect_distribution(self, cvd: pd.Series,
                           lookback: int = 50,
                           threshold_percentile: float = 75) -> bool:
        """
        Detect if CVD shows distribution pattern.
        
        Args:
            cvd: CVD series
            lookback: Bars to look back
            threshold_percentile: CVD strength threshold
        
        Returns:
            True if distribution detected
        """
        if len(cvd) < lookback:
            return False
        
        recent_cvd = cvd.iloc[-lookback:]
        
        # Check if CVD is trending down (negative slope)
        slope = (recent_cvd.iloc[-1] - recent_cvd.iloc[0]) / lookback
        
        # Check if current CVD is below percentile
        strength = np.percentile(recent_cvd.abs().values, threshold_percentile)
        is_strong = abs(recent_cvd.iloc[-1]) > strength
        
        return slope < 0 and is_strong and recent_cvd.iloc[-1] < 0
    
    def detect_cvd_divergence(self, price: pd.Series, 
                             cvd: pd.Series,
                             lookback: int = 20) -> Optional[str]:
        """
        Detect divergences between price and CVD.
        
        Bullish divergence: Price makes lower low, CVD makes higher low
        Bearish divergence: Price makes higher high, CVD makes lower high
        
        Args:
            price: Price series (usually close)
            cvd: CVD series
            lookback: Bars to analyze
        
        Returns:
            'bullish', 'bearish', or None
        """
        if len(price) < lookback or len(cvd) < lookback:
            return None
        
        recent_price = price.iloc[-lookback:]
        recent_cvd = cvd.iloc[-lookback:]
        
        # Find local lows and highs
        price_min_idx = recent_price.argmin()
        price_max_idx = recent_price.argmax()
        cvd_min_idx = recent_cvd.argmin()
        cvd_max_idx = recent_cvd.argmax()
        
        # Bullish divergence
        if (price_min_idx > lookback // 2 and cvd_min_idx < lookback // 2):
            # Current price low is lower than past, but CVD low is higher
            if (recent_price.iloc[price_min_idx] < recent_price.iloc[0] and
                recent_cvd.iloc[cvd_min_idx] > recent_cvd.iloc[0]):
                return 'bullish'
        
        # Bearish divergence
        if (price_max_idx > lookback // 2 and cvd_max_idx < lookback // 2):
            # Current price high is higher than past, but CVD high is lower
            if (recent_price.iloc[price_max_idx] > recent_price.iloc[0] and
                recent_cvd.iloc[cvd_max_idx] < recent_cvd.iloc[0]):
                return 'bearish'
        
        return None
