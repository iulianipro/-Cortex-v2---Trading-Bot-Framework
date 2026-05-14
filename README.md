# Cortex v2 - Enterprise Trading Bot Framework
*A production-ready, enterprise-grade autonomous trading bot framework with complete architecture, implementation, testing, and documentation.
**A production-ready, fully modular and event-driven autonomous trading system** built in Python. Designed for institutional-grade risk management, multi-pair monitoring, and AI-powered decision making with automatic fallback to technical analysis.

##  Key Features

### Architecture
- **Event-Driven (Pub/Sub)**: Components communicate via decoupled event bus
- **Fully Async**: `asyncio`-based concurrent processing for 10+ trading pairs simultaneously
- **Modular Design**: Swap components (AI models, strategies, exchanges) without touching core code
- **Enterprise Logging**: Structured JSON logging for monitoring, debugging, and external dashboards (Grafana)

### Core Modules

#### SENSE (Data & Analysis)
- **Multi-Exchange Ready**: Binance today, add any exchange in 15 minutes
- **Order Block Detection**: Identifies institutional accumulation/distribution zones
- **Fair Value Gap (FVG)**: Detects market imbalances
- **CVD Tracking**: Cumulative Volume Delta for volume analysis
- **TA Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, etc.

#### BRAIN (Decision Engine)
- **AI Integration**: HuggingFace API (Chronos for forecasting, FinBERT for sentiment)
- **Intelligent Fallback**: Auto-switches to technical analysis if AI API fails
- **Hybrid Strategy**: Combines AI confidence with technical signals
- **State Machine**: Tracks market context per trading pair

#### RISK & VAULT (Protection)
- **Portfolio-Level Risk**: Caps total exposure (e.g., max 5% at risk)
- **Drawdown Protection**: Pauses trading if max DD exceeded
- **Daily Loss Limits**: Stops trading after daily loss threshold
- **Position Sizing**: Dynamic sizing based on risk/reward
- **Correlation Analysis**: Prevents accumulation of correlated trades

#### EXEC (Order Execution)
- **Limit vs Market**: Configurable order types
- **Trailing Stops**: Dynamic profit protection
- **Multi-Pair Execution**: Async order placement across pairs
- **Order Lifecycle Management**: Tracking and monitoring

##  Quick Start

### 1. Setup Environment

```bash
# Clone/download the project
cd cortex_v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
# Copy .env template
cp .env.example .env

# Edit .env with your credentials
# API_KEY=your_binance_api_key
# API_SECRET=your_binance_api_secret
```

### 3. Configure Trading Parameters

```bash
# Edit config/config.yaml
# - Set trading_pairs (BTCUSDT, ETHUSDT, etc.)
# - Adjust risk parameters (max_portfolio_risk, max_drawdown)
# - Choose strategy (hybrid, ai_only, technical_only)
```

### 4. Run the Bot

```bash
python main.py
```

##  Architecture Overview

```
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
```

##  Event Flow Example

```
[Market Data Received]
        ↓
[SENSE: Calculate Indicators]
        ↓ emit: "analysis_complete"
[BRAIN: Generate Signals]
        ↓ emit: "signal_generated"
[RISK: Evaluate Portfolio Risk]
        ↓ emit: "risk_approved" / "risk_rejected"
[EXEC: Place Order]
        ↓ emit: "order_placed"
[Monitor: Trailing Stop & Position Management]
```

##  Configuration Examples

### Aggressive Strategy
```yaml
strategy_type: "ai_only"
ai_model: "chronos"
confidence_threshold: 0.60
max_portfolio_risk: 0.10
position_size_pct: 0.05
```

### Conservative Strategy
```yaml
strategy_type: "hybrid"
ai_model: "finbert"
confidence_threshold: 0.75
max_portfolio_risk: 0.03
position_size_pct: 0.01
max_drawdown: 0.05
```

### Technical-Only (No AI)
```yaml
strategy_type: "technical_only"
ai_enabled: false
max_portfolio_risk: 0.05
position_size_pct: 0.02
```

##  Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_order_blocks.py -v

# Run with coverage
pytest tests/ --cov=cortex --cov-report=html
```

### Test Coverage
- ✅ Order Block detection (pattern recognition)
- ✅ FVG calculation and tracking
- ✅ Risk manager constraints
- ✅ Signal generation logic
- ✅ Configuration loading
- ✅ Event bus communication

## 📈 Monitoring & Logging

All events are logged as structured JSON:

```json
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
```

### View Logs
```bash
# Tail in real-time
tail -f logs/cortex.log | jq '.'

# Filter by event type
grep "signal_generated" logs/cortex.log | jq '.data'
```

### Export to Grafana (Future)
The JSON structure supports Prometheus metrics export for dashboard integration.

## 🔧 Extending the Bot

### Add a New Exchange

1. Create `cortex/sense/YOUR_EXCHANGE_client.py`
2. Implement `DataProvider` interface
3. Update `config.yaml` with new exchange settings

### Add a New Indicator

1. Create `cortex/sense/indicators/YOUR_indicator.py`
2. Implement analysis logic
3. Emit indicator results as events

### Add a New Strategy

1. Create `cortex/brain/strategies/YOUR_strategy.py`
2. Implement `DecisionEngine` interface
3. Configure in `config.yaml` → `strategy_type`

##  Risk Disclaimers

- **Paper trading** is enabled by default (`paper_trading: true` in config)
- **Test thoroughly** before enabling real trading
- **Monitor constantly** - bots can fail unexpectedly
- **Use small position sizes** initially
- **Never trade with money you can't afford to lose**

##  Documentation

- `ARCHITECTURE.md` - Detailed system design
- `MODULES.md` - Individual component documentation
- `API.md` - Event and method signatures
- `TROUBLESHOOTING.md` - Common issues and solutions

##  Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

##  License
MIT License - See LICENSE file

##  Support

- **Issues**: Report bugs on GitHub
- **Discussions**: Share ideas and get help
- **Documentation**: Check the docs/ folder

##  Learning Resources

- Smart Money Concepts (SMC) - Order Blocks & FVG
- Technical Analysis Basics - RSI, MACD, Moving Averages
- Risk Management - Position Sizing & Portfolio Theory
- Python Async - Asyncio, Pub/Sub patterns

---

**Cortex v2** - Build, backtest, and deploy trading bots with enterprise-grade reliability.
