"""
Fair Value Gap (FVG) Detection Module
Detects areas of imbalance in the market where price likely returns to fill the gap
"""

import pandas as pd
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class FVGType(Enum):
    """FVG orientation"""
    BULLISH = "bullish"  # Gap up (potential pullback to fill)
    BEARISH = "bearish"  # Gap down (potential bounce to fill)


@dataclass
class FairValueGap:
    """Fair Value Gap structure"""
    gap_type: FVGType
    top: float        # Upper boundary
    bottom: float     # Lower boundary
    bar_index: int    # Where gap was created
    filled: bool = False
    
    @property
    def width(self) -> float:
        """Size of the gap"""
        return self.top - self.bottom
    
    @property
    def mid(self) -> float:
        """Mid point of gap"""
        return (self.top + self.bottom) / 2


class FVGDetector:
    """
    Fair Value Gap detector.
    
    FVGs are gaps between candles that represent market imbalances.
    - Bullish FVG: High of candle 3 > Low of candle 1 (gap above)
    - Bearish FVG: Low of candle 3 < High of candle 1 (gap below)
    """
    
    def __init__(self, min_gap_size_pct: float = 0.05):
        """
        Args:
            min_gap_size_pct: Minimum gap size as % of price (0.05 = 0.05%)
        """
        self.min_gap_size_pct = min_gap_size_pct
    
    def detect(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect FVGs from OHLCV data.
        
        Args:
            df: DataFrame with columns [open, high, low, close, volume]
        
        Returns:
            List of FairValueGap objects
        """
        if len(df) < 3:
            return []
        
        df = df.copy()
        fvgs = []
        
        # Need 3 consecutive candles to detect FVG
        for i in range(2, len(df)):
            candle1 = df.iloc[i-2]
            candle2 = df.iloc[i-1]
            candle3 = df.iloc[i]
            
            # Detect Bullish FVG
            # Candle 1 closes, Candle 2 gaps up (low > candle1 high), Candle 3 closes above candle 2
            if candle2['low'] > candle1['high'] and candle3['high'] > candle1['high']:
                gap_size_pct = ((candle2['low'] - candle1['high']) / candle1['high']) * 100
                
                if gap_size_pct >= self.min_gap_size_pct:
                    fvg = FairValueGap(
                        gap_type=FVGType.BULLISH,
                        top=candle2['low'],
                        bottom=candle1['high'],
                        bar_index=i-1
                    )
                    fvgs.append(fvg)
            
            # Detect Bearish FVG
            # Candle 1 closes, Candle 2 gaps down (high < candle1 low), Candle 3 closes below candle 2
            if candle2['high'] < candle1['low'] and candle3['low'] < candle1['low']:
                gap_size_pct = ((candle1['low'] - candle2['high']) / candle1['low']) * 100
                
                if gap_size_pct >= self.min_gap_size_pct:
                    fvg = FairValueGap(
                        gap_type=FVGType.BEARISH,
                        top=candle1['low'],
                        bottom=candle2['high'],
                        bar_index=i-1
                    )
                    fvgs.append(fvg)
        
        # Mark filled FVGs
        fvgs = self._mark_filled(df, fvgs)
        
        return fvgs
    
    @staticmethod
    def _mark_filled(df: pd.DataFrame, fvgs: List[FairValueGap]) -> List[FairValueGap]:
        """Mark FVGs that have been filled by price"""
        for fvg in fvgs:
            # Check if price has filled the gap
            for i in range(fvg.bar_index, len(df)):
                candle = df.iloc[i]
                
                if fvg.gap_type == FVGType.BULLISH:
                    # Gap is filled if price touches or goes below bottom
                    if candle['low'] <= fvg.bottom:
                        fvg.filled = True
                        break
                else:
                    # Gap is filled if price touches or goes above top
                    if candle['high'] >= fvg.top:
                        fvg.filled = True
                        break
        
        return fvgs
    
    def to_dict(self, fvgs: List[FairValueGap]) -> List[Dict]:
        """Convert FVGs to dictionary format"""
        return [
            {
                'type': fvg.gap_type.value,
                'top': float(fvg.top),
                'bottom': float(fvg.bottom),
                'mid': float(fvg.mid),
                'width': float(fvg.width),
                'width_pct': float((fvg.width / fvg.mid) * 100),
                'filled': fvg.filled,
                'bar_index': fvg.bar_index
            }
            for fvg in fvgs
        ]
