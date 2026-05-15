#!/usr/bin/env python3
"""
Cortex v2 Trading Bot - Main Entry Point

This is the primary script to start the trading bot in production or paper trading mode.
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from cortex.bot import CortexBot
from cortex.utils.logger import get_logger
from cortex.utils.config_loader import ConfigLoader

logger = get_logger(__name__)


class BotRunner:
    """Main bot runner with graceful shutdown handling."""
    
    def __init__(self):
        self.bot: Optional[CortexBot] = None
        self.shutdown_event = asyncio.Event()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def run(self):
        """Main run loop with error handling and recovery."""
        try:
            # Load configuration
            config_path = Path("config/config.yaml")
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                logger.error("Please copy config/config.yaml.example to config/config.yaml and configure it")
                sys.exit(1)
            
            config = ConfigLoader.load_config(str(config_path))
            
            # Check for environment variables
            env_file = Path(".env")
            if not env_file.exists():
                logger.warning("No .env file found. Make sure API credentials are set in environment variables")
                logger.warning("Copy .env.example to .env and configure your API keys")
            
            # Display startup banner
            self._print_banner(config)
            
            # Initialize bot
            logger.info("Initializing Cortex v2 Trading Bot...")
            self.bot = CortexBot(config)
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # Start the bot
            logger.info("Starting bot...")
            bot_task = asyncio.create_task(self.bot.start())
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Graceful shutdown
            logger.info("Shutting down bot gracefully...")
            await self.bot.stop()
            
            # Wait for bot task to complete
            try:
                await asyncio.wait_for(bot_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Bot shutdown timed out, forcing exit")
                bot_task.cancel()
            
            logger.info("Bot stopped successfully")
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
            if self.bot:
                await self.bot.stop()
        
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
            if self.bot:
                await self.bot.stop()
            sys.exit(1)
    
    def _print_banner(self, config: dict):
        """Print startup banner with configuration summary."""
        mode = "PAPER TRADING" if config.get("execution", {}).get("paper_trading", True) else "LIVE TRADING"
        risk_profile = config.get("risk", {}).get("max_portfolio_risk_percent", 10)
        strategy_mode = config.get("strategy", {}).get("mode", "technical_only")
        
        banner = f"""
╔═══════════════════════════════════════════════════════════════╗
║                   CORTEX v2 TRADING BOT                       ║
║                  Autonomous Trading System                     ║
╚═══════════════════════════════════════════════════════════════╝

  Mode:             {mode}
  Strategy:         {strategy_mode.upper()}
  Max Portfolio Risk: {risk_profile}%
  Trading Pairs:    {', '.join(config.get('trading', {}).get('symbols', ['BTC/USDT']))}
  
  Event-Driven Architecture: ✓
  Risk Management:          ✓
  Multi-Pair Monitoring:    ✓
  
  Press Ctrl+C to stop gracefully
  
═══════════════════════════════════════════════════════════════
"""
        print(banner)
        logger.info("Configuration loaded successfully")


def main():
    """Main entry point."""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("ERROR: Python 3.8 or higher is required")
            sys.exit(1)
        
        # Create and run bot
        runner = BotRunner()
        asyncio.run(runner.run())
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
