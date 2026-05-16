"""
Decision Engine - BRAIN Module

Combines technical analysis and AI signals to make trading decisions.
Supports multiple modes: technical_only, ai_only, hybrid.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ..core.base_component import DecisionEngine, Signal
from ..core.event_bus import EventBus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CortexDecisionEngine(DecisionEngine):
    """
    Main decision engine that processes signals and generates trading decisions.
    
    Modes:
    - technical_only: Use only technical indicators (OB, FVG, CVD)
    - ai_only: Use only AI model predictions
    - hybrid: Combine both technical and AI with configurable weights
    """
    
    def __init__(self, config: dict, event_bus: EventBus):
        """
        Initialize decision engine.
        
        Args:
            config: Configuration dictionary with strategy settings
            event_bus: Event bus for communication
        """
        self.config = config
        self.event_bus = event_bus
        self.strategy_config = config.get("strategy", {})
        self.mode = self.strategy_config.get("mode", "technical_only")
        
        # Weights for hybrid mode
        self.technical_weight = self.strategy_config.get("technical_weight", 0.6)
        self.ai_weight = self.strategy_config.get("ai_weight", 0.4)
        
        # Confidence thresholds
        self.min_confidence = self.strategy_config.get("min_confidence", 0.65)
        self.min_technical_score = self.strategy_config.get("min_technical_score", 0.6)
        self.min_ai_score = self.strategy_config.get("min_ai_score", 0.7)
        
        # Store latest signals
        self.technical_signals: Dict[str, Dict] = {}
        self.ai_signals: Dict[str, Dict] = {}
        
        # Subscribe to events
        self._subscribe_to_events()
        
        logger.info(f"Decision engine initialized in {self.mode} mode")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events."""
        self.event_bus.subscribe("technical_analysis_complete", self._on_technical_analysis)
        self.event_bus.subscribe("ai_prediction_complete", self._on_ai_prediction)
    
    async def _on_technical_analysis(self, data: dict):
        """Handle technical analysis results."""
        symbol = data.get("symbol")
        if symbol:
            self.technical_signals[symbol] = data
            logger.debug(f"Received technical analysis for {symbol}")
            
            # If in technical_only mode, generate signal immediately
            if self.mode == "technical_only":
                await self._process_technical_signal(symbol, data)
    
    async def _on_ai_prediction(self, data: dict):
        """Handle AI prediction results."""
        symbol = data.get("symbol")
        if symbol:
            self.ai_signals[symbol] = data
            logger.debug(f"Received AI prediction for {symbol}")
            
            # If in ai_only mode, generate signal immediately
            if self.mode == "ai_only":
                await self._process_ai_signal(symbol, data)
    
    async def _process_technical_signal(self, symbol: str, data: dict):
        """Process technical-only signal."""
        score = self._calculate_technical_score(data)
        
        if score >= self.min_technical_score:
            signal = self._create_signal_from_technical(symbol, data, score)
            await self.generate_signal(signal)
    
    async def _process_ai_signal(self, symbol: str, data: dict):
        """Process AI-only signal."""
        confidence = data.get("confidence", 0)
        
        if confidence >= self.min_ai_score:
            signal = self._create_signal_from_ai(symbol, data, confidence)
            await self.generate_signal(signal)
    
    def _calculate_technical_score(self, data: dict) -> float:
        """
        Calculate overall technical score from multiple indicators.
        
        Returns:
            Score between 0 and 1
        """
        scores = []
        
        # Order Block strength
        ob_data = data.get("order_blocks", {})
        if ob_data:
            ob_strength = ob_data.get("strength", 0)
            scores.append(ob_strength / 100.0)  # Normalize to 0-1
        
        # FVG confidence
        fvg_data = data.get("fvg", {})
        if fvg_data:
            fvg_strength = fvg_data.get("strength", 0)
            scores.append(fvg_strength / 100.0)
        
        # CVD trend strength
        cvd_data = data.get("cvd", {})
        if cvd_data:
            cvd_signal = cvd_data.get("signal", "neutral")
            if cvd_signal == "strong_bullish":
                scores.append(0.9)
            elif cvd_signal == "bullish":
                scores.append(0.7)
            elif cvd_signal == "bearish":
                scores.append(0.3)
            elif cvd_signal == "strong_bearish":
                scores.append(0.1)
            else:
                scores.append(0.5)
        
        # Calculate weighted average
        if not scores:
            return 0.0
        
        return sum(scores) / len(scores)
    
    def _create_signal_from_technical(self, symbol: str, data: dict, score: float) -> Signal:
        """Create trading signal from technical analysis."""
        # Determine direction based on indicators
        direction = self._determine_direction_technical(data)
        
        # Get entry price from order blocks or current price
        entry_price = data.get("current_price", 0)
        ob_data = data.get("order_blocks", {})
        if ob_data and ob_data.get("bullish_blocks"):
            entry_price = ob_data["bullish_blocks"][0].get("price", entry_price)
        
        signal = Signal(
            symbol=symbol,
            direction=direction,
            confidence=score,
            entry_price=entry_price,
            stop_loss=self._calculate_stop_loss(entry_price, direction, data),
            take_profit=self._calculate_take_profit(entry_price, direction, data),
            timeframe=data.get("timeframe", "1h"),
            reason=self._generate_technical_reason(data),
            metadata={
                "mode": "technical",
                "indicators": {
                    "order_blocks": ob_data,
                    "fvg": data.get("fvg", {}),
                    "cvd": data.get("cvd", {})
                }
            }
        )
        
        return signal
    
    def _create_signal_from_ai(self, symbol: str, data: dict, confidence: float) -> Signal:
        """Create trading signal from AI prediction."""
        direction = data.get("prediction", "neutral")
        entry_price = data.get("current_price", 0)
        
        signal = Signal(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=data.get("stop_loss", entry_price * 0.98),
            take_profit=data.get("take_profit", entry_price * 1.03),
            timeframe=data.get("timeframe", "1h"),
            reason=data.get("reason", "AI model prediction"),
            metadata={
                "mode": "ai",
                "model": data.get("model", "unknown"),
                "features": data.get("features", {})
            }
        )
        
        return signal
    
    def _determine_direction_technical(self, data: dict) -> str:
        """Determine trade direction from technical indicators."""
        bullish_score = 0
        bearish_score = 0
        
        # Order blocks
        ob_data = data.get("order_blocks", {})
        if ob_data.get("bullish_blocks"):
            bullish_score += 1
        if ob_data.get("bearish_blocks"):
            bearish_score += 1
        
        # CVD
        cvd_data = data.get("cvd", {})
        cvd_signal = cvd_data.get("signal", "neutral")
        if "bullish" in cvd_signal:
            bullish_score += 1
        elif "bearish" in cvd_signal:
            bearish_score += 1
        
        # FVG
        fvg_data = data.get("fvg", {})
        if fvg_data.get("bullish_gaps"):
            bullish_score += 0.5
        if fvg_data.get("bearish_gaps"):
            bearish_score += 0.5
        
        if bullish_score > bearish_score:
            return "long"
        elif bearish_score > bullish_score:
            return "short"
        else:
            return "neutral"
    
    def _calculate_stop_loss(self, entry: float, direction: str, data: dict) -> float:
        """Calculate stop loss based on technical levels."""
        atr_multiplier = self.strategy_config.get("atr_stop_multiplier", 1.5)
        default_stop_pct = 0.02  # 2% default
        
        if direction == "long":
            return entry * (1 - default_stop_pct)
        elif direction == "short":
            return entry * (1 + default_stop_pct)
        else:
            return entry
    
    def _calculate_take_profit(self, entry: float, direction: str, data: dict) -> float:
        """Calculate take profit based on risk-reward ratio."""
        risk_reward = self.strategy_config.get("risk_reward_ratio", 2.0)
        stop_loss = self._calculate_stop_loss(entry, direction, data)
        risk = abs(entry - stop_loss)
        
        if direction == "long":
            return entry + (risk * risk_reward)
        elif direction == "short":
            return entry - (risk * risk_reward)
        else:
            return entry
    
    def _generate_technical_reason(self, data: dict) -> str:
        """Generate human-readable reason for the signal."""
        reasons = []
        
        ob_data = data.get("order_blocks", {})
        if ob_data.get("bullish_blocks"):
            reasons.append(f"Bullish OB at {ob_data['bullish_blocks'][0].get('price', 'N/A')}")
        
        cvd_data = data.get("cvd", {})
        if cvd_data.get("signal") and cvd_data["signal"] != "neutral":
            reasons.append(f"CVD: {cvd_data['signal']}")
        
        fvg_data = data.get("fvg", {})
        if fvg_data.get("bullish_gaps") or fvg_data.get("bearish_gaps"):
            reasons.append("FVG detected")
        
        return " | ".join(reasons) if reasons else "Technical confluence"
    
    async def generate_signal(self, signal: Signal):
        """
        Generate and publish trading signal.
        
        Args:
            signal: Trading signal to publish
        """
        logger.info(f"Signal generated: {signal.symbol} {signal.direction} @ {signal.entry_price} "
                   f"(confidence: {signal.confidence:.2%})")
        
        # Publish signal event
        await self.event_bus.publish("signal_generated", {
            "signal": signal,
            "timestamp": datetime.now().isoformat()
        })
    
    async def process_market_data(self, symbol: str, data: dict):
        """
        Process market data and generate signals based on mode.
        
        Args:
            symbol: Trading pair symbol
            data: Market data dictionary
        """
        if self.mode == "hybrid":
            # Wait for both technical and AI signals
            tech_signal = self.technical_signals.get(symbol)
            ai_signal = self.ai_signals.get(symbol)
            
            if tech_signal and ai_signal:
                await self._process_hybrid_signal(symbol, tech_signal, ai_signal)
        
        # For technical_only and ai_only, signals are processed in event handlers
    
    async def _process_hybrid_signal(self, symbol: str, tech_data: dict, ai_data: dict):
        """Combine technical and AI signals using weighted approach."""
        tech_score = self._calculate_technical_score(tech_data)
        ai_confidence = ai_data.get("confidence", 0)
        
        # Weighted combination
        combined_score = (tech_score * self.technical_weight) + (ai_confidence * self.ai_weight)
        
        if combined_score >= self.min_confidence:
            # Determine direction by consensus
            tech_direction = self._determine_direction_technical(tech_data)
            ai_direction = ai_data.get("prediction", "neutral")
            
            # Only signal if both agree
            if tech_direction == ai_direction and tech_direction != "neutral":
                signal = Signal(
                    symbol=symbol,
                    direction=tech_direction,
                    confidence=combined_score,
                    entry_price=tech_data.get("current_price", 0),
                    stop_loss=self._calculate_stop_loss(
                        tech_data.get("current_price", 0),
                        tech_direction,
                        tech_data
                    ),
                    take_profit=self._calculate_take_profit(
                        tech_data.get("current_price", 0),
                        tech_direction,
                        tech_data
                    ),
                    timeframe=tech_data.get("timeframe", "1h"),
                    reason=f"Hybrid: {self._generate_technical_reason(tech_data)} + AI",
                    metadata={
                        "mode": "hybrid",
                        "technical_score": tech_score,
                        "ai_confidence": ai_confidence,
                        "combined_score": combined_score
                    }
                )
                
                await self.generate_signal(signal)
                
                # Clear signals after processing
                self.technical_signals.pop(symbol, None)
                self.ai_signals.pop(symbol, None)
