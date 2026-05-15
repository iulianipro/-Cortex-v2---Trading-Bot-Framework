"""
Configuration management system
Loads settings from config.yaml and .env files
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class TradingConfig:
    """Trading configuration settings"""
    
    # API Configuration
    exchange_name: str
    api_key: str
    api_secret: str
    
    # Trading Pairs
    trading_pairs: list
    
    # Risk Parameters
    max_portfolio_risk: float  # e.g., 0.05 (5%)
    max_drawdown: float  # e.g., 0.10 (10%)
    position_size_pct: float  # Risk per trade as % of portfolio
    
    # AI/Strategy
    ai_enabled: bool
    ai_model: str  # "chronos", "finbert", or "technical"
    strategy_type: str  # "hybrid", "ai_only", "technical_only"
    confidence_threshold: float  # AI confidence minimum
    
    # Execution
    order_type: str  # "market" or "limit"
    limit_offset_pct: float  # Offset from current price for limit orders
    use_trailing_stop: bool
    trailing_stop_pct: float
    
    # Monitoring
    check_interval_seconds: float
    log_level: str
    
    # Data Sources
    data_sources: Dict[str, Any]


class ConfigLoader:
    """Load and validate configuration from YAML and environment"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._config: Optional[Dict] = None
    
    def load(self) -> TradingConfig:
        """
        Load configuration from YAML and environment variables.
        Environment variables override YAML settings.
        """
        # Load YAML
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
        
        # Override with environment variables
        self._override_from_env()
        
        # Validate
        self._validate()
        
        # Build config object
        return self._build_config()
    
    def _override_from_env(self):
        """Override config values with environment variables"""
        env_overrides = {
            'exchange_name': 'EXCHANGE_NAME',
            'api_key': 'API_KEY',
            'api_secret': 'API_SECRET',
            'max_portfolio_risk': 'MAX_PORTFOLIO_RISK',
            'ai_enabled': 'AI_ENABLED',
            'check_interval_seconds': 'CHECK_INTERVAL',
        }
        
        for config_key, env_key in env_overrides.items():
            env_value = os.getenv(env_key)
            if env_value:
                # Handle boolean conversion
                if env_key == 'AI_ENABLED':
                    env_value = env_value.lower() in ('true', '1', 'yes')
                # Handle float conversion
                elif env_key in ('MAX_PORTFOLIO_RISK', 'CHECK_INTERVAL'):
                    env_value = float(env_value)
                
                self._config[config_key] = env_value
    
    def _validate(self):
        """Validate configuration values"""
        required_fields = [
            'api_key', 'api_secret', 'trading_pairs',
            'max_portfolio_risk', 'strategy_type'
        ]
        
        for field in required_fields:
            if field not in self._config or self._config[field] is None:
                raise ValueError(f"Missing required config field: {field}")
        
        # Validate ranges
        if not 0 < self._config['max_portfolio_risk'] < 1:
            raise ValueError("max_portfolio_risk must be between 0 and 1")
        
        if self._config['strategy_type'] not in ['hybrid', 'ai_only', 'technical_only']:
            raise ValueError("Invalid strategy_type")
    
    def _build_config(self) -> TradingConfig:
        """Build TradingConfig object from loaded config"""
        cfg = self._config
        
        return TradingConfig(
            exchange_name=cfg.get('exchange_name', 'binance'),
            api_key=cfg['api_key'],
            api_secret=cfg['api_secret'],
            trading_pairs=cfg.get('trading_pairs', []),
            max_portfolio_risk=cfg.get('max_portfolio_risk', 0.05),
            max_drawdown=cfg.get('max_drawdown', 0.10),
            position_size_pct=cfg.get('position_size_pct', 0.02),
            ai_enabled=cfg.get('ai_enabled', True),
            ai_model=cfg.get('ai_model', 'chronos'),
            strategy_type=cfg.get('strategy_type', 'hybrid'),
            confidence_threshold=cfg.get('confidence_threshold', 0.65),
            order_type=cfg.get('order_type', 'limit'),
            limit_offset_pct=cfg.get('limit_offset_pct', 0.001),
            use_trailing_stop=cfg.get('use_trailing_stop', True),
            trailing_stop_pct=cfg.get('trailing_stop_pct', 0.02),
            check_interval_seconds=cfg.get('check_interval_seconds', 60),
            log_level=cfg.get('log_level', 'INFO'),
            data_sources=cfg.get('data_sources', {})
        )
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Return default configuration template"""
        return {
            'exchange_name': 'binance',
            'api_key': '${API_KEY}',
            'api_secret': '${API_SECRET}',
            'trading_pairs': ['BTCUSDT', 'ETHUSDT'],
            'max_portfolio_risk': 0.05,
            'max_drawdown': 0.10,
            'position_size_pct': 0.02,
            'ai_enabled': True,
            'ai_model': 'chronos',
            'strategy_type': 'hybrid',
            'confidence_threshold': 0.65,
            'order_type': 'limit',
            'limit_offset_pct': 0.001,
            'use_trailing_stop': True,
            'trailing_stop_pct': 0.02,
            'check_interval_seconds': 60,
            'log_level': 'INFO',
            'data_sources': {
                'binance': {
                    'name': 'Binance',
                    'kline_interval': '1m'
                }
            }
        }
