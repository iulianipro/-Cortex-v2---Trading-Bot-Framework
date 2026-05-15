"""
CORTEX v2 - Complete Example: End-to-End Trading Bot
This example shows how all components work together
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from cortex.bot import CortexBot
from cortex.core.event_bus import get_event_bus, Event
from cortex.sense.indicators.order_block import OrderBlockDetector
from cortex.sense.indicators.fvg_detector import FVGDetector
from cortex.sense.indicators.cvd_calculator import CVDCalculator
from cortex.core.base_component import Signal
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# EXAMPLE 1: Simple Data Analysis Pipeline
# ============================================================================

async def example_data_analysis():
    """
    Demonstrate how SENSE module analyzes market data
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Data Analysis Pipeline (SENSE Module)")
    print("="*70)
    
    # Create sample market data
    df = pd.DataFrame({
        'open': np.random.uniform(40000, 45000, 100),
        'high': np.random.uniform(40000, 45000, 100),
        'low': np.random.uniform(40000, 45000, 100),
        'close': np.random.uniform(40000, 45000, 100),
        'volume': np.random.uniform(100, 1000, 100)
    })
    
    # Sort by date
    df = df.sort_index()
    
    # Initialize detectors
    ob_detector = OrderBlockDetector(lookback=50, min_strength=0.3)
    fvg_detector = FVGDetector(min_gap_size_pct=0.05)
    cvd_calc = CVDCalculator()
    
    # Run analysis
    print("\n[DETECTING ORDER BLOCKS]")
    order_blocks = ob_detector.detect(df)
    print(f"Found {len(order_blocks)} order blocks")
    for ob in order_blocks[:3]:
        print(f"  - {ob.block_type.value.upper()}: {ob.low:.0f} - {ob.high:.0f} (strength: {ob.strength:.2f})")
    
    print("\n[DETECTING FAIR VALUE GAPS]")
    fvgs = fvg_detector.detect(df)
    print(f"Found {len(fvgs)} fair value gaps")
    for fvg in fvgs[:3]:
        print(f"  - {fvg.gap_type.value.upper()}: {fvg.bottom:.0f} - {fvg.top:.0f}")
    
    print("\n[CALCULATING CVD]")
    cvd = cvd_calc.calculate_from_ohlcv(df)
    print(f"CVD range: {cvd.min():.0f} to {cvd.max():.0f}")
    
    # Check for accumulation/distribution
    is_accumulating = cvd_calc.detect_accumulation(cvd)
    is_distributing = cvd_calc.detect_distribution(cvd)
    print(f"Accumulation signal: {is_accumulating}")
    print(f"Distribution signal: {is_distributing}")


# ============================================================================
# EXAMPLE 2: Event Bus Communication
# ============================================================================

async def example_event_bus():
    """
    Demonstrate event-driven architecture
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Event Bus (Decoupled Communication)")
    print("="*70)
    
    event_bus = get_event_bus()
    
    # Define event handlers
    async def on_signal_generated(event):
        data = event.data
        print(f"\n[SIGNAL HANDLER] Received BUY signal for {data['symbol']}")
        print(f"  Confidence: {data['confidence']:.2%}")
        print(f"  Entry: {data['entry_price']:.2f}")
        print(f"  Stop: {data['stop_loss']:.2f}")
    
    async def on_market_update(event):
        data = event.data
        print(f"[MARKET UPDATE] {data['symbol']} - Price: {data.get('price', 'N/A')}")
    
    # Subscribe handlers to events
    await event_bus.subscribe("signal_generated", on_signal_generated)
    await event_bus.subscribe("market_update", on_market_update)
    
    # Start event bus
    bus_task = asyncio.create_task(event_bus.start())
    
    # Simulate events
    print("\n[Simulating market events...]")
    
    # Market update event
    await event_bus.publish(Event(
        event_type="market_update",
        timestamp=datetime.utcnow(),
        source="data_fetcher",
        data={
            "symbol": "BTCUSDT",
            "price": 42500.50,
            "timestamp": datetime.utcnow().isoformat()
        }
    ))
    
    await asyncio.sleep(0.5)
    
    # Signal generated event
    await event_bus.publish(Event(
        event_type="signal_generated",
        timestamp=datetime.utcnow(),
        source="brain_ai",
        data={
            "symbol": "BTCUSDT",
            "signal_type": "BUY",
            "confidence": 0.78,
            "entry_price": 42500.50,
            "stop_loss": 41225.0,
            "take_profit": 43775.0
        }
    ))
    
    await asyncio.sleep(1)
    
    # Stop bus
    await event_bus.stop()
    bus_task.cancel()
    try:
        await bus_task
    except asyncio.CancelledError:
        pass


# ============================================================================
# EXAMPLE 3: Risk Management
# ============================================================================

async def example_risk_management():
    """
    Demonstrate portfolio risk management
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Risk Management (RISK Module)")
    print("="*70)
    
    from cortex.risk.global_risk_manager import GlobalRiskManager
    
    # Create risk manager
    risk_mgr = GlobalRiskManager(
        max_portfolio_risk=0.05,  # 5%
        max_drawdown=0.10,        # 10%
        max_daily_loss=0.02,      # 2%
        max_trades_per_day=20
    )
    await risk_mgr.start()
    
    # Simulate portfolio state
    portfolio_state = {
        'total_balance': 100000,
        'available_balance': 95000,
        'positions': {
            'BTCUSDT': {
                'quantity': 0.5,
                'entry_price': 40000,
                'notional': 20000
            }
        },
        'realized_pnl': 500,
        'unrealized_pnl': -1000,
        'trades_today': 3,
        'winning_trades': 2,
        'losing_trades': 1
    }
    
    risk_mgr.update_portfolio(portfolio_state)
    
    # Print portfolio stats
    stats = risk_mgr.get_portfolio_stats()
    print("\n[Portfolio Statistics]")
    print(f"  Total Balance: ${stats['total_balance']:,.0f}")
    print(f"  Available: ${stats['available_balance']:,.0f}")
    print(f"  Exposure: {stats['exposure_pct']:.2%}")
    print(f"  Daily P&L: ${stats['daily_pnl']:,.0f}")
    print(f"  Win Rate: {stats['win_rate']:.2%}")
    print(f"  Max DD: {stats['max_drawdown']:.2%}")
    print(f"  Trades Today: {stats['trades_today']}")
    
    # Test risk evaluation
    print("\n[Risk Evaluation for New Trade]")
    signal = Signal(
        symbol="ETHUSDT",
        timestamp=datetime.utcnow(),
        signal_type="BUY",
        confidence=0.75,
        entry_price=2500.0,
        stop_loss=2425.0,
        take_profit=2575.0,
        reason="Order block + bullish divergence",
        source="hybrid_strategy"
    )
    
    risk_approved = await risk_mgr.evaluate_risk(signal, portfolio_state)
    print(f"Risk Approved: {risk_approved}")
    
    await risk_mgr.stop()


# ============================================================================
# EXAMPLE 4: Complete Bot Flow
# ============================================================================

async def example_complete_bot():
    """
    Show how a complete trading cycle works
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Complete Bot Flow (All Modules)")
    print("="*70)
    
    print("\n[1. INITIALIZATION]")
    bot = CortexBot("config/config.yaml")
    try:
        await bot.initialize()
        print("✓ Bot initialized successfully")
        print(f"  Trading pairs: {bot.active_symbols}")
    except FileNotFoundError as e:
        print(f"✗ Note: Config file not found (expected in demo): {e}")
        print("  In production, ensure config/config.yaml exists")
        return
    
    print("\n[2. COMPONENT STATUS]")
    status = bot.get_status()
    print(f"  Running: {status['running']}")
    print(f"  Symbols: {status['symbols']}")
    print(f"  Strategy: {status['config'].get('strategy', 'N/A')}")
    
    print("\n[3. TRADING CYCLE]")
    print("  [SENSE] → Fetching market data")
    print("  [SENSE] → Calculating indicators")
    print("  [BRAIN] → Generating signals")
    print("  [RISK]  → Evaluating portfolio risk")
    print("  [EXEC]  → Placing orders")
    print("  [EXEC]  → Managing positions")
    
    await bot.stop()
    print("\n✓ Bot shutdown complete")


# ============================================================================
# MAIN: Run all examples
# ============================================================================

async def main():
    """Run all examples"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  CORTEX v2 - COMPLETE EXAMPLES".center(68) + "█")
    print("█" + "  Enterprise Trading Bot Framework".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    try:
        # Run examples
        await example_data_analysis()
        await asyncio.sleep(1)
        
        await example_event_bus()
        await asyncio.sleep(1)
        
        await example_risk_management()
        await asyncio.sleep(1)
        
        await example_complete_bot()
        
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  All examples completed successfully!".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
    
    except Exception as e:
        logger.error(f"Example error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================================
# HOW TO RUN THIS EXAMPLE:
# ============================================================================
# 
# $ python example_complete.py
#
# This will demonstrate:
#   1. Order block & FVG detection on sample data
#   2. Event bus pub/sub communication
#   3. Portfolio risk management
#   4. Complete trading bot initialization
#
# Note: For real trading, update config/config.yaml with your API credentials
# ============================================================================
