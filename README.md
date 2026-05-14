Cortex v2 - Enterprise Trading Bot Framework
A production-ready, fully modular and event-driven autonomous trading system built in Python. Designed for institutional-grade risk management, multi-pair monitoring, and AI-powered decision making with automatic fallback to technical analysis.

Key Features
Architecture
Event-Driven (Pub/Sub): Components communicate via a decoupled event bus to ensure high-speed processing and reliability.

Fully Async: asyncio-based concurrent processing allows for monitoring 10+ trading pairs simultaneously without thread blocking.

Modular Design: Swap components (AI models, strategies, or exchanges) without modifying the core engine code.

Enterprise Logging: Structured JSON logging enables advanced monitoring, debugging, and integration with external dashboards like Grafana or ELK stack.

Core Modules
SENSE (Data and Analysis)
Multi-Exchange Ready: Currently optimized for Binance; extensible to any exchange via a standardized DataProvider interface.

Order Block Detection: Algorithms to identify institutional accumulation and distribution zones.

Fair Value Gap (FVG): Automated detection of market imbalances and liquidity voids.

CVD Tracking: Cumulative Volume Delta analysis to measure aggressive buying vs. selling pressure.

Technical Indicators: Full integration with TA-Lib for RSI, MACD, Bollinger Bands, and Moving Averages.

BRAIN (Decision Engine)
AI Integration: Native support for HuggingFace Inference API (Amazon Chronos for forecasting and FinBERT for sentiment analysis).

Intelligent Fallback: Automatically reverts to rule-based technical analysis if AI APIs encounter latency or downtime.

Hybrid Strategy: Weighted decision-making that combines AI probability scores with technical confirmations.

State Machine: Maintains market context (Trend, Range, Volatility) per individual trading pair.

RISK and VAULT (Protection)
Portfolio-Level Risk: Centralized manager to cap total exposure across all open positions.

Drawdown Protection: Hard-stop logic to pause trading activity if maximum drawdown thresholds are breached.

Daily Loss Limits: Automatic circuit breakers based on daily loss thresholds.

Dynamic Position Sizing: Volatility-adjusted sizing based on Risk/Reward ratios.

Correlation Analysis: Prevents over-exposure by identifying and limiting trades in highly correlated assets.

EXEC (Order Execution)
Execution Logic: Configurable Limit and Market order types with slippage protection.

Trailing Stops: Dynamic profit protection that adjusts based on price movement.

Lifecycle Management: Real-time tracking and monitoring of order states from placement to settlement.

Quick Start
1. Setup Environment
Bash
# Clone the repository
git clone https://github.com/iulianipro/-Cortex-v2---Trading-Bot-Framework
cd cortex_v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
2. Configure Credentials
Bash
# Copy .env template
cp .env.example .env

# Edit .env with your credentials
# API_KEY=your_binance_api_key
# API_SECRET=your_binance_api_secret
# HF_TOKEN=your_hugging_face_token
3. Run the Bot
Bash
python main.py
Architecture Overview
Plaintext
┌─────────────────────────────────────────────────────────────────┐
│                    CORTEX BOT (Main Orchestrator)               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌──────────────┐        ┌──────────────┐
            │  EVENT BUS   │        │ CONFIG LOADER│
            │  (Pub/Sub)   │        │  (YAML/ENV)  │
            └──────────────┘        └──────────────┘
                    │
        ┌───────────┼───────────┬───────────────────────┐
        ▼           ▼           ▼                       ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐       ┌──────────────┐
    │ SENSE   │ │ BRAIN   │ │ RISK &   │       │ EXEC         │
    │         │ │         │ │ VAULT    │       │              │
    │ ├─ OB   │ │ ├─ AI   │ │ ├─ Global│       │ ├─ Market    │
    │ ├─ FVG  │ │ ├─ TA   │ │ │ RiskMgr│       │ ├─ Limit     │
    │ ├─ CVD  │ │ └─ Hybrid│ │ ├─ PosSiz│       │ └─ Trailing  │
    │ └─ TA   │ │         │ │ └─ DDMonr│       │              │
    └─────────┘ └─────────┘ └──────────┘       └──────────────┘
Testing and Quality Assurance
Bash
# Execute full test suite
pytest tests/ -v

# Run specific component tests
pytest tests/test_order_blocks.py -v

# Generate coverage report
pytest tests/ --cov=cortex --cov-report=html
Monitoring and Logging
All system events are logged as structured JSON to facilitate machine readability:

JSON
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "cortex.sense.order_block",
  "message": "Bullish order block detected",
  "data": {
    "symbol": "BTCUSDT",
    "strength": 0.78,
    "price_level": 42500.50
  }
}
Risk Disclaimers
Important: Paper trading is enabled by default (paper_trading: true). It is strongly recommended to perform extensive forward testing in a simulated environment before committing real capital. Automated trading bots can fail due to API connectivity issues, market slippage, or unforeseen volatility. Never trade with funds you cannot afford to lose.

License
This project is licensed under the MIT License - see the LICENSE file for details.
