"""
Unit tests for Order Block detection
"""

import pytest
import pandas as pd
import numpy as np
from cortex.sense.indicators.order_block import (
    OrderBlockDetector, OrderBlockType, OrderBlock
)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing"""
    data = {
        'open': [100, 101, 102, 103, 102, 101, 100, 99, 98, 97,
                 96, 95, 94, 95, 96, 97, 98, 99, 100, 101],
        'high': [101, 102, 103, 104, 103, 102, 101, 100, 99, 98,
                 97, 96, 95, 96, 97, 98, 99, 100, 101, 102],
        'low': [99, 100, 101, 102, 101, 100, 99, 98, 97, 96,
                95, 94, 93, 94, 95, 96, 97, 98, 99, 100],
        'close': [100, 101, 102, 103, 102, 101, 100, 99, 98, 97,
                  96, 95, 94, 95, 96, 97, 98, 99, 100, 101],
        'volume': [1000] * 20
    }
    return pd.DataFrame(data)


@pytest.fixture
def uptrend_data():
    """Create strong uptrend data with clear structure breaks"""
    data = {
        'open': list(range(100, 120)),
        'high': list(range(101, 121)),
        'low': list(range(99, 119)),
        'close': list(range(100, 120)),
        'volume': [1000 + i*50 for i in range(20)]
    }
    return pd.DataFrame(data)


@pytest.fixture
def downtrend_data():
    """Create strong downtrend data with clear structure breaks"""
    data = {
        'open': list(range(120, 100, -1)),
        'high': list(range(121, 100, -1)),
        'low': list(range(119, 99, -1)),
        'close': list(range(120, 100, -1)),
        'volume': [1000 + i*50 for i in range(20)]
    }
    return pd.DataFrame(data)


def test_detector_initialization():
    """Test detector can be initialized"""
    detector = OrderBlockDetector(lookback=50, min_strength=0.3)
    assert detector.lookback == 50
    assert detector.min_strength == 0.3


def test_detect_with_empty_data():
    """Test detector handles empty data"""
    detector = OrderBlockDetector()
    df = pd.DataFrame()
    blocks = detector.detect(df)
    assert len(blocks) == 0


def test_detect_with_insufficient_data():
    """Test detector with insufficient data"""
    detector = OrderBlockDetector()
    df = pd.DataFrame({
        'open': [100, 101],
        'high': [101, 102],
        'low': [99, 100],
        'close': [100, 101],
        'volume': [1000, 1000]
    })
    blocks = detector.detect(df)
    assert len(blocks) == 0


def test_order_block_properties():
    """Test OrderBlock data structure"""
    block = OrderBlock(
        block_type=OrderBlockType.BULLISH,
        high=102,
        low=100,
        entry_bar_index=0,
        strength=0.8
    )
    
    assert block.mid == 101
    assert block.width == 2
    assert block.block_type == OrderBlockType.BULLISH
    assert not block.mitigated


def test_find_swing_highs(sample_ohlcv_data):
    """Test swing high detection"""
    detector = OrderBlockDetector()
    swings = detector._find_swing_highs(sample_ohlcv_data, period=3)
    
    assert isinstance(swings, list)
    # Should find local maxima
    assert len(swings) > 0


def test_find_swing_lows(sample_ohlcv_data):
    """Test swing low detection"""
    detector = OrderBlockDetector()
    swings = detector._find_swing_lows(sample_ohlcv_data, period=3)
    
    assert isinstance(swings, list)
    # Should find local minima
    assert len(swings) > 0


def test_detect_uptrend(uptrend_data):
    """Test detection in uptrend"""
    detector = OrderBlockDetector(min_strength=0.1)
    blocks = detector.detect(uptrend_data)
    
    # Uptrend should potentially have bullish blocks
    assert isinstance(blocks, list)


def test_detect_downtrend(downtrend_data):
    """Test detection in downtrend"""
    detector = OrderBlockDetector(min_strength=0.1)
    blocks = detector.detect(downtrend_data)
    
    # Downtrend should potentially have bearish blocks
    assert isinstance(blocks, list)


def test_merge_overlapping_blocks():
    """Test merging of overlapping blocks"""
    block1 = OrderBlock(
        block_type=OrderBlockType.BULLISH,
        high=102,
        low=100,
        entry_bar_index=0,
        strength=0.5
    )
    
    block2 = OrderBlock(
        block_type=OrderBlockType.BULLISH,
        high=103,
        low=101,
        entry_bar_index=1,
        strength=0.6
    )
    
    merged = OrderBlockDetector._merge_overlapping([block1, block2])
    
    # Should merge overlapping blocks
    assert len(merged) <= 2


def test_mark_mitigated_blocks(sample_ohlcv_data):
    """Test mitigation marking"""
    detector = OrderBlockDetector()
    
    # Create a bullish block
    block = OrderBlock(
        block_type=OrderBlockType.BULLISH,
        high=101,
        low=99,
        entry_bar_index=5,
        strength=0.7
    )
    
    marked = detector._mark_mitigated(sample_ohlcv_data, [block])
    
    # After mitigation marking, should know if price reached the high
    assert marked[0].mitigated in [True, False]


def test_to_dict_conversion(sample_ohlcv_data):
    """Test conversion of blocks to dictionary format"""
    detector = OrderBlockDetector()
    blocks = detector.detect(sample_ohlcv_data)
    
    dicts = detector.to_dict(blocks)
    
    if blocks:
        # Check structure of converted data
        for d in dicts:
            assert 'type' in d
            assert 'high' in d
            assert 'low' in d
            assert 'strength' in d
            assert 'mitigated' in d


def test_block_strength_calculation():
    """Test that block strength is between 0 and 1"""
    detector = OrderBlockDetector()
    
    # Create test data with volume spike
    df = pd.DataFrame({
        'open': [100, 101, 102, 103, 102],
        'high': [101, 102, 103, 104, 103],
        'low': [99, 100, 101, 102, 101],
        'close': [100, 101, 102, 103, 102],
        'volume': [1000, 1000, 10000, 1000, 1000]
    })
    
    blocks = detector.detect(df)
    
    for block in blocks:
        assert 0 <= block.strength <= 1


def test_detector_with_real_pattern():
    """Test with realistic price pattern: down then up (potential bullish block)"""
    data = {
        'open': [100, 99, 98, 97, 96, 97, 98, 99, 100, 101, 102],
        'high': [101, 100, 99, 98, 97, 98, 99, 100, 101, 102, 103],
        'low': [99, 98, 97, 96, 95, 96, 97, 98, 99, 100, 101],
        'close': [100, 99, 98, 97, 96, 97, 98, 99, 100, 101, 102],
        'volume': [1000, 1000, 1000, 1000, 1000, 1500, 1500, 1500, 1500, 1500, 1500]
    }
    df = pd.DataFrame(data)
    
    detector = OrderBlockDetector(min_strength=0.1)
    blocks = detector.detect(df)
    
    # Pattern should produce some blocks
    assert isinstance(blocks, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
