"""
Base component classes for modular architecture
All components inherit from these to ensure consistency
"""

import abc
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from cortex.core.event_bus import Event, get_event_bus, emit_event


@dataclass
class MarketData:
    """Market data point"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_asset_volume: Optional[float] = None


@dataclass
class Signal:
    """Trading signal"""
    symbol: str
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    source: str  # Which module generated this


class BaseComponent(abc.ABC):
    """Abstract base class for all Cortex components"""
    
    def __init__(self, name: str):
        self.name = name
        self._is_running = False
    
    @abc.abstractmethod
    async def start(self):
        """Start the component"""
        pass
    
    @abc.abstractmethod
    async def stop(self):
        """Stop the component"""
        pass
    
    @property
    def is_running(self) -> bool:
        """Check if component is running"""
        return self._is_running
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to the event bus"""
        await emit_event(event_type, self.name, data)


class DataProvider(BaseComponent):
    """Abstract base for data providers (exchanges, APIs, etc.)"""
    
    @abc.abstractmethod
    async def fetch_ohlcv(self, symbol: str, interval: str, limit: int = 100) -> list:
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Timeframe (e.g., '1m', '5m', '1h')
            limit: Number of candles to fetch
        
        Returns:
            List of OHLCV data
        """
        pass
    
    @abc.abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker info"""
        pass


class AnalysisModule(BaseComponent):
    """Abstract base for analysis modules (indicators, detectors, etc.)"""
    
    @abc.abstractmethod
    async def analyze(self, data: Any) -> Dict[str, Any]:
        """
        Analyze data and return results.
        
        Returns:
            Dictionary with analysis results
        """
        pass


class DecisionEngine(BaseComponent):
    """Abstract base for decision-making engines (AI, rules, etc.)"""
    
    @abc.abstractmethod
    async def decide(self, symbol: str, market_data: MarketData, 
                    analysis: Dict[str, Any]) -> Optional[Signal]:
        """
        Make trading decision based on analysis.
        
        Args:
            symbol: Trading pair
            market_data: Current market data
            analysis: Analysis results from modules
        
        Returns:
            Trading signal or None
        """
        pass


class RiskManager(BaseComponent):
    """Abstract base for risk management"""
    
    @abc.abstractmethod
    async def evaluate_risk(self, signal: Signal, 
                          portfolio_state: Dict[str, Any]) -> bool:
        """
        Evaluate if signal should be executed based on risk parameters.
        
        Args:
            signal: Proposed trading signal
            portfolio_state: Current portfolio state
        
        Returns:
            True if risk is acceptable, False otherwise
        """
        pass


class OrderExecutor(BaseComponent):
    """Abstract base for order execution"""
    
    @abc.abstractmethod
    async def execute(self, signal: Signal) -> Dict[str, Any]:
        """
        Execute trading signal.
        
        Args:
            signal: Signal to execute
        
        Returns:
            Order result dictionary
        """
        pass
