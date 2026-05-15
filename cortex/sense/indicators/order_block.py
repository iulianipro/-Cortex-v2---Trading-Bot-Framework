"""
Order Block Detection Module
Detects institutional accumulation/distribution zones based on smart money concepts
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class OrderBlockType(Enum):
    """Types of order blocks"""
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class OrderBlock:
    """Order block data structure"""
    block_type: OrderBlockType
    high: float
    low: float
    entry_bar_index: int
    strength: float  # 0-1, based on breaking structure
    mitigated: bool = False
    mitigation_price: Optional[float] = None
    
    @property
    def mid(self) -> float:
        """Mid-point of order block"""
        return (self.high + self.low) / 2
    
    @property
    def width(self) -> float:
        """Width of order block"""
        return self.high - self.low


class OrderBlockDetector:
    """
    Detects Order Blocks - zones where institutional traders accumulated/distributed.
    
    Algorithm:
    1. Find swing highs and lows
    2. Detect breaking of these swings (imbalance)
    3. Identify the candle(s) that created the swing (order block)
    4. Track if order blocks are mitigated by price
    """
    
    def __init__(self, lookback: int = 50, min_strength: float = 0.3):
        """
        Args:
            lookback: Number of candles to look back for swings
            min_strength: Minimum strength threshold (0-1)
        """
        self.lookback = lookback
        self.min_strength = min_strength
    
    def detect(self, df: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect order blocks from OHLCV data.
        
        Args:
            df: DataFrame with columns [open, high, low, close, volume]
        
        Returns:
            List of detected OrderBlock objects
        """
        if len(df) < 10:
            return []
        
        df = df.copy()
        order_blocks = []
        
        # Find swing highs and lows
        swing_highs = self._find_swing_highs(df, period=5)
        swing_lows = self._find_swing_lows(df, period=5)
        
        # Detect breaking structure
        for i in range(10, len(df)):
            # Check for bullish order block (break of previous swing low)
            bullish_ob = self._detect_bullish_block(df, swing_lows, i)
            if bullish_ob and bullish_ob.strength >= self.min_strength:
                order_blocks.append(bullish_ob)
            
            # Check for bearish order block (break of previous swing high)
            bearish_ob = self._detect_bearish_block(df, swing_highs, i)
            if bearish_ob and bearish_ob.strength >= self.min_strength:
                order_blocks.append(bearish_ob)
        
        # Merge overlapping blocks and mark mitigated ones
        order_blocks = self._merge_overlapping(order_blocks)
        order_blocks = self._mark_mitigated(df, order_blocks)
        
        return order_blocks
    
    @staticmethod
    def _find_swing_highs(df: pd.DataFrame, period: int = 5) -> List[Tuple[int, float]]:
        """Find swing highs (local maxima)"""
        swings = []
        for i in range(period, len(df) - period):
            high = df.iloc[i]['high']
            if all(df.iloc[i - period + j]['high'] <= high for j in range(period)):
                if all(df.iloc[i + period - j]['high'] <= high for j in range(1, period)):
                    swings.append((i, high))
        return swings
    
    @staticmethod
    def _find_swing_lows(df: pd.DataFrame, period: int = 5) -> List[Tuple[int, float]]:
        """Find swing lows (local minima)"""
        swings = []
        for i in range(period, len(df) - period):
            low = df.iloc[i]['low']
            if all(df.iloc[i - period + j]['low'] >= low for j in range(period)):
                if all(df.iloc[i + period - j]['low'] >= low for j in range(1, period)):
                    swings.append((i, low))
        return swings
    
    def _detect_bullish_block(self, df: pd.DataFrame, 
                             swing_lows: List[Tuple[int, float]], 
                             current_idx: int) -> Optional[OrderBlock]:
        """Detect bullish order block (break of swing low)"""
        if not swing_lows:
            return None
        
        # Get most recent swing low before current bar
        recent_swing = None
        for idx, low in swing_lows:
            if idx < current_idx - 5:
                recent_swing = (idx, low)
        
        if not recent_swing:
            return None
        
        swing_idx, swing_low = recent_swing
        current_low = df.iloc[current_idx]['low']
        
        # If current bar breaks below swing low
        if current_low < swing_low:
            # Order block is the swing candle(s)
            block_high = df.iloc[swing_idx:swing_idx+2]['high'].max()
            block_low = swing_low
            
            # Calculate strength based on volume and range
            volume_strength = min(
                df.iloc[current_idx]['volume'] / df.iloc[swing_idx]['volume'],
                1.0
            )
            range_strength = (block_high - block_low) / df.iloc[swing_idx]['close']
            strength = (volume_strength * 0.4 + range_strength * 0.6)
            
            return OrderBlock(
                block_type=OrderBlockType.BULLISH,
                high=block_high,
                low=block_low,
                entry_bar_index=swing_idx,
                strength=min(strength, 1.0)
            )
        
        return None
    
    def _detect_bearish_block(self, df: pd.DataFrame,
                             swing_highs: List[Tuple[int, float]],
                             current_idx: int) -> Optional[OrderBlock]:
        """Detect bearish order block (break of swing high)"""
        if not swing_highs:
            return None
        
        # Get most recent swing high before current bar
        recent_swing = None
        for idx, high in swing_highs:
            if idx < current_idx - 5:
                recent_swing = (idx, high)
        
        if not recent_swing:
            return None
        
        swing_idx, swing_high = recent_swing
        current_high = df.iloc[current_idx]['high']
        
        # If current bar breaks above swing high
        if current_high > swing_high:
            # Order block is the swing candle(s)
            block_high = swing_high
            block_low = df.iloc[swing_idx:swing_idx+2]['low'].min()
            
            # Calculate strength
            volume_strength = min(
                df.iloc[current_idx]['volume'] / df.iloc[swing_idx]['volume'],
                1.0
            )
            range_strength = (block_high - block_low) / df.iloc[swing_idx]['close']
            strength = (volume_strength * 0.4 + range_strength * 0.6)
            
            return OrderBlock(
                block_type=OrderBlockType.BEARISH,
                high=block_high,
                low=block_low,
                entry_bar_index=swing_idx,
                strength=min(strength, 1.0)
            )
        
        return None
    
    @staticmethod
    def _merge_overlapping(blocks: List[OrderBlock]) -> List[OrderBlock]:
        """Merge overlapping order blocks"""
        if not blocks:
            return blocks
        
        merged = []
        blocks_sorted = sorted(blocks, key=lambda b: b.entry_bar_index)
        
        current = blocks_sorted[0]
        for block in blocks_sorted[1:]:
            # Check if blocks overlap
            if block.low <= current.high and block.high >= current.low:
                # Merge
                current = OrderBlock(
                    block_type=current.block_type,
                    high=max(current.high, block.high),
                    low=min(current.low, block.low),
                    entry_bar_index=current.entry_bar_index,
                    strength=max(current.strength, block.strength)
                )
            else:
                merged.append(current)
                current = block
        
        merged.append(current)
        return merged
    
    @staticmethod
    def _mark_mitigated(df: pd.DataFrame, blocks: List[OrderBlock]) -> List[OrderBlock]:
        """Mark order blocks that have been mitigated by price"""
        for block in blocks:
            # Check if price has reached the opposite end of the block
            if block.block_type == OrderBlockType.BULLISH:
                # Block is mitigated if price reaches above the high
                if any(df.iloc[i]['high'] > block.high for i in range(block.entry_bar_index, len(df))):
                    block.mitigated = True
                    block.mitigation_price = block.high
            else:
                # Block is mitigated if price reaches below the low
                if any(df.iloc[i]['low'] < block.low for i in range(block.entry_bar_index, len(df))):
                    block.mitigated = True
                    block.mitigation_price = block.low
        
        return blocks
    
    def to_dict(self, blocks: List[OrderBlock]) -> List[Dict]:
        """Convert order blocks to dictionary format"""
        return [
            {
                'type': block.block_type.value,
                'high': float(block.high),
                'low': float(block.low),
                'mid': float(block.mid),
                'width': float(block.width),
                'strength': float(block.strength),
                'mitigated': block.mitigated,
                'entry_bar_index': block.entry_bar_index
            }
            for block in blocks
        ]
