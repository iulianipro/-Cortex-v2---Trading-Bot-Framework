"""
Global Risk Manager
Ensures portfolio-wide risk constraints are respected
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cortex.core.base_component import RiskManager, Signal
from cortex.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PortfolioState:
    """Current portfolio state"""
    total_balance: float
    available_balance: float
    positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_balance: float = 0.0
    trades_today: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    @property
    def total_exposed(self) -> float:
        """Total capital in positions"""
        return sum(p.get('notional', 0) for p in self.positions.values())
    
    @property
    def exposure_pct(self) -> float:
        """Portfolio exposure as percentage"""
        if self.total_balance == 0:
            return 0
        return self.total_exposed / self.total_balance
    
    @property
    def win_rate(self) -> float:
        """Win rate of completed trades"""
        total = self.winning_trades + self.losing_trades
        if total == 0:
            return 0
        return self.winning_trades / total
    
    @property
    def daily_pnl(self) -> float:
        """Daily P&L"""
        return self.realized_pnl + self.unrealized_pnl


class GlobalRiskManager(RiskManager):
    """
    Portfolio-level risk manager.
    
    Features:
    - Maximum portfolio exposure limits
    - Drawdown monitoring and protection
    - Per-pair correlation analysis
    - Dynamic position sizing
    - Daily trade limits
    """
    
    def __init__(self, 
                 max_portfolio_risk: float = 0.05,  # 5%
                 max_drawdown: float = 0.10,  # 10%
                 max_positions: int = 10,
                 max_daily_loss: float = 0.02,  # 2%
                 max_trades_per_day: int = 20):
        super().__init__("GlobalRiskManager")
        
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown = max_drawdown
        self.max_positions = max_positions
        self.max_daily_loss = max_daily_loss
        self.max_trades_per_day = max_trades_per_day
        
        self.portfolio_state = PortfolioState(
            total_balance=0,
            available_balance=0,
            peak_balance=0
        )
        
        self.position_correlations: Dict[str, Dict[str, float]] = {}
    
    async def start(self):
        """Start risk manager"""
        self._is_running = True
        logger.info("Global Risk Manager started")
    
    async def stop(self):
        """Stop risk manager"""
        self._is_running = False
        logger.info("Global Risk Manager stopped")
    
    async def evaluate_risk(self, signal: Signal, 
                          portfolio_state: Dict[str, Any]) -> bool:
        """
        Comprehensive risk evaluation before trade execution.
        
        Checks:
        1. Portfolio exposure limit
        2. Drawdown protection
        3. Daily loss limit
        4. Daily trade count
        5. Correlation risk
        6. Available balance
        """
        # Update portfolio state
        self.update_portfolio(portfolio_state)
        
        # Run all risk checks
        checks = {
            'exposure_limit': await self._check_exposure_limit(signal),
            'drawdown_protection': await self._check_drawdown_protection(),
            'daily_loss_limit': await self._check_daily_loss_limit(),
            'trade_count_limit': await self._check_trade_count_limit(),
            'correlation_risk': await self._check_correlation_risk(signal),
            'balance_available': await self._check_balance_available(signal)
        }
        
        # Log evaluation
        await self.emit_event("risk_evaluation", {
            "symbol": signal.symbol,
            "checks": checks,
            "passed": all(checks.values())
        })
        
        # Return overall result
        return all(checks.values())
    
    async def _check_exposure_limit(self, signal: Signal) -> bool:
        """
        Check if new position would exceed portfolio exposure limit.
        
        Example: If max_portfolio_risk=5%, portfolio can't have >5% of balance
        in total open positions
        """
        signal_notional = signal.entry_price * 1.0  # Assume 1 unit for now
        new_exposure = self.portfolio_state.total_exposed + signal_notional
        new_exposure_pct = new_exposure / self.portfolio_state.total_balance
        
        passed = new_exposure_pct <= self.max_portfolio_risk
        
        if not passed:
            logger.warning(
                f"Exposure limit check failed: "
                f"{new_exposure_pct:.2%} > {self.max_portfolio_risk:.2%}"
            )
        
        return passed
    
    async def _check_drawdown_protection(self) -> bool:
        """
        Check if current or potential drawdown exceeds limit.
        Prevents trading during heavy losses.
        """
        if self.portfolio_state.peak_balance == 0:
            return True
        
        current_dd = (
            (self.portfolio_state.peak_balance - self.portfolio_state.total_balance) / 
            self.portfolio_state.peak_balance
        )
        
        passed = current_dd <= self.max_drawdown
        
        if not passed:
            logger.warning(
                f"Drawdown protection triggered: {current_dd:.2%} > {self.max_drawdown:.2%}"
            )
        
        return passed
    
    async def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss exceeds limit"""
        daily_loss_pct = abs(self.portfolio_state.realized_pnl) / self.portfolio_state.total_balance
        
        passed = daily_loss_pct <= self.max_daily_loss
        
        if not passed:
            logger.warning(
                f"Daily loss limit triggered: {daily_loss_pct:.2%} > {self.max_daily_loss:.2%}"
            )
        
        return passed
    
    async def _check_trade_count_limit(self) -> bool:
        """Check if daily trade count exceeds limit"""
        passed = self.portfolio_state.trades_today < self.max_trades_per_day
        
        if not passed:
            logger.warning(
                f"Trade count limit reached: {self.portfolio_state.trades_today} >= {self.max_trades_per_day}"
            )
        
        return passed
    
    async def _check_correlation_risk(self, signal: Signal) -> bool:
        """
        Check if new position has excessive correlation with existing positions.
        Prevents accumulation of similar trades.
        """
        # Simplified: allow if less than 3 correlated positions
        correlated_positions = 0
        
        for symbol, corr in self.position_correlations.get(signal.symbol, {}).items():
            if symbol in self.portfolio_state.positions and corr > 0.7:
                correlated_positions += 1
        
        passed = correlated_positions < 3
        
        if not passed:
            logger.warning(f"High correlation risk detected for {signal.symbol}")
        
        return passed
    
    async def _check_balance_available(self, signal: Signal) -> bool:
        """Check if sufficient balance available for position"""
        required_balance = signal.entry_price * 1.0  # Assume 1 unit
        
        passed = self.portfolio_state.available_balance >= required_balance
        
        if not passed:
            logger.warning(f"Insufficient balance for {signal.symbol}")
        
        return passed
    
    def update_portfolio(self, state: Dict[str, Any]):
        """Update internal portfolio state"""
        self.portfolio_state.total_balance = state.get('total_balance', 0)
        self.portfolio_state.available_balance = state.get('available_balance', 0)
        self.portfolio_state.positions = state.get('positions', {})
        self.portfolio_state.realized_pnl = state.get('realized_pnl', 0)
        self.portfolio_state.unrealized_pnl = state.get('unrealized_pnl', 0)
        self.portfolio_state.trades_today = state.get('trades_today', 0)
        self.portfolio_state.winning_trades = state.get('winning_trades', 0)
        self.portfolio_state.losing_trades = state.get('losing_trades', 0)
        
        # Update peak for drawdown calculation
        if self.portfolio_state.total_balance > self.portfolio_state.peak_balance:
            self.portfolio_state.peak_balance = self.portfolio_state.total_balance
        
        # Calculate max drawdown
        if self.portfolio_state.peak_balance > 0:
            dd = (self.portfolio_state.peak_balance - self.portfolio_state.total_balance) / self.portfolio_state.peak_balance
            if dd > self.portfolio_state.max_drawdown:
                self.portfolio_state.max_drawdown = dd
    
    def get_position_size(self, signal: Signal, 
                         risk_amount: float) -> float:
        """
        Calculate position size based on risk management rules.
        
        Args:
            signal: Trading signal with entry/stop levels
            risk_amount: Amount willing to risk
        
        Returns:
            Position size (quantity)
        """
        risk_per_unit = abs(signal.entry_price - signal.stop_loss)
        
        if risk_per_unit == 0:
            return 0
        
        position_size = risk_amount / risk_per_unit
        
        # Cap position size based on available balance
        max_position = self.portfolio_state.available_balance / signal.entry_price
        
        return min(position_size, max_position * 0.95)  # Never use 100%
    
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """Get current portfolio statistics"""
        return {
            'total_balance': self.portfolio_state.total_balance,
            'available_balance': self.portfolio_state.available_balance,
            'total_exposed': self.portfolio_state.total_exposed,
            'exposure_pct': self.portfolio_state.exposure_pct,
            'daily_pnl': self.portfolio_state.daily_pnl,
            'win_rate': self.portfolio_state.win_rate,
            'max_drawdown': self.portfolio_state.max_drawdown,
            'trades_today': self.portfolio_state.trades_today
        }
