# Cortex v2 - Enterprise Trading Bot Framework

A production-ready, fully modular and event-driven autonomous trading system built in Python. Designed for institutional-grade risk management, multi-pair monitoring, and AI-powered decision making.

## Table of Contents

- [Key Features](#key-features)
- [Core Modules](#core-modules)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Architecture Overview](#architecture-overview)
- [Testing and Quality Assurance](#testing-and-quality-assurance)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Risk Disclaimers](#risk-disclaimers)
- [License](#license)

## Key Features

### Architecture

- **Event-Driven (Pub/Sub)**: Components communicate via a decoupled event bus to ensure high-speed processing and reliability.
- **Fully Async**: asyncio-based concurrent processing allows for monitoring 10+ trading pairs simultaneously without thread blocking.
- **Modular Design**: Swap components (AI models, strategies, or exchanges) without modifying the core engine code.
- **Enterprise Logging**: Structured JSON logging enables advanced monitoring, debugging, and integration with external dashboards like Grafana or ELK stack.

## Core Modules

### SENSE (Data and Analysis)

- **Multi-Exchange Ready**: Currently optimized for Binance; extensible to any exchange via a standardized DataProvider interface.
- **Order Block Detection**: Algorithms to identify institutional accumulation and distribution zones.
- **Fair Value Gap (FVG)**: Automated detection of market imbalances and liquidity voids.
- **CVD Tracking**: Cumulative Volume Delta analysis to measure aggressive buying vs. selling pressure.
- **Technical Indicators**: Full integration with TA-Lib for RSI, MACD, Bollinger Bands, and Moving Averages.

### BRAIN (Decision Engine)

- **AI Integration**: Native support for HuggingFace Inference API (Amazon Chronos for forecasting and FinBERT for sentiment analysis).
- **Intelligent Fallback**: Automatically reverts to rule-based technical analysis if AI APIs encounter latency or downtime.
- **Hybrid Strategy**: Weighted decision-making that combines AI probability scores with technical confirmations.
- **State Machine**: Maintains market context (Trend, Range, Volatility) per individual trading pair.

### RISK and VAULT (Protection)

- **Portfolio-Level Risk**: Centralized manager to cap total exposure across all open positions.
- **Drawdown Protection**: Hard-stop logic to pause trading activity if maximum drawdown thresholds are breached.
- **Daily Loss Limits**: Automatic circuit breakers based on daily loss thresholds.
- **Dynamic Position Sizing**: Volatility-adjusted sizing based on Risk/Reward ratios.
- **Correlation Analysis**: Prevents over-exposure by identifying and limiting trades in highly correlated assets.

### EXEC (Order Execution)

- **Execution Logic**: Configurable Limit and Market order types with slippage protection.
- **Trailing Stops**: Dynamic profit protection that adjusts based on price movement.
- **Lifecycle Management**: Real-time tracking and monitoring of order states from placement to settlement.

## Prerequisites

- **Python**: 3.9 or higher
- **Package Manager**: pip or poetry
- **Binance Account**: API credentials for live or paper trading
- **HuggingFace Account**: API token for AI-powered features (optional but recommended)
- **System**: Linux, macOS, or Windows with 2GB+ RAM

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/iulianipro/-Cortex-v2---Trading-Bot-Framework
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
# HF_TOKEN=your_hugging_face_token
```

### 3. Run the Bot

```bash
python main.py
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Binance API Configuration
API_KEY=your_binance_api_key
API_SECRET=your_binance_api_secret

# HuggingFace API (optional, for AI features)
HF_TOKEN=your_hugging_face_token

# Paper Trading (recommended for testing)
PAPER_TRADING=true

# Risk Configuration
MAX_DRAWDOWN=0.15           # 15% maximum drawdown
DAILY_LOSS_LIMIT=0.10       # 10% daily loss limit
MAX_POSITION_SIZE=0.05      # 5% per position

# Trading Pairs (comma-separated)
TRADING_PAIRS=BTCUSDT,ETHUSDT,BNBUSDT

# Logging Level
LOG_LEVEL=INFO
```

### YAML Configuration

Edit `config.yaml` for advanced settings:
- Risk thresholds and position sizing rules
- Trading pair whitelists and blacklists
- AI model selection and fallback strategies
- Data provider and exchange settings

Refer to `config.example.yaml` for full documentation.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  CORTEX BOT (Main Orchestrator)              │
└──────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌──────────────┐            ┌──────────────────┐
    │  EVENT BUS   │            │ CONFIG LOADER    │
    │  (Pub/Sub)   │            │  (YAML/ENV)      │
    └──────────────┘            └──────────────────┘
            │
    ┌───────┼───────┬───────────┬──────────────┐
    ▼       ▼       ▼           ▼              ▼
┌─────┐ ┌─────┐ ┌──────────┐ ┌──────────┐ ┌────────┐
│SENSE│ │BRAIN│ │RISK &    │ │VAULT     │ │EXEC    │
│     │ │     │ │PORTFOLIO │ │(Storage) │ │        │
│ ├─OB│ ├─AI  │ ├─Global   │ ├─History │ ├─Market │
│ ├─FVG│├─TA  │ │RiskMgr   │ ├─State   │ ├─Limit  │
│ ├─CVD│├─Hyb │ ├─PosSizing │ │DB       │ └─Trailing
│ └─TA│ └─SM  │ └─DDMonr   │ └─────────┘   
└─────┘ └─────┘ └──────────┘
```

## Testing and Quality Assurance

### Run Full Test Suite

```bash
pytest tests/ -v
```

### Run Specific Component Tests

```bash
# Test order block detection
pytest tests/test_order_blocks.py -v

# Test risk management
pytest tests/test_risk_management.py -v

# Test execution engine
pytest tests/test_execution.py -v
```

### Generate Coverage Report

```bash
pytest tests/ --cov=cortex --cov-report=html
open htmlcov/index.html
```

## Monitoring and Logging

All system events are logged as structured JSON to facilitate machine readability and integration with monitoring systems like Grafana, ELK Stack, or Datadog.

### Example Log Entry

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
# Live stream JSON logs
tail -f logs/cortex.log | jq .

# Filter by component
grep "cortex.sense" logs/cortex.log | jq .
```

## Troubleshooting

### Issue: Connection Refused to Binance API

**Solution**: Verify your API credentials in `.env` and ensure your IP is whitelisted in Binance API settings.

### Issue: HuggingFace API Rate Limiting

**Solution**: The bot will automatically fall back to technical analysis. Increase the `HF_REQUEST_TIMEOUT` in `config.yaml` or upgrade your HuggingFace plan.

### Issue: Insufficient Balance for Position Sizing

**Solution**: Reduce `MAX_POSITION_SIZE` in `.env` or add funds to your trading account. Paper trading mode is enabled by default for testing.

### Issue: High Memory Usage

**Solution**: Reduce the number of `TRADING_PAIRS` or increase the data aggregation interval in `config.yaml`.

### Issue: Module Import Errors

**Solution**: Ensure your virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt --upgrade
```

For more help, check the [GitHub Issues](https://github.com/iulianipro/-Cortex-v2---Trading-Bot-Framework/issues) page.

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:
- All tests pass (`pytest tests/ -v`)
- Code follows PEP 8 style guide
- New features include unit tests
- Documentation is updated

For detailed contributing guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Risk Disclaimers

⚠️ **IMPORTANT - READ CAREFULLY**

This software is provided **AS-IS** for educational and research purposes. Trading cryptocurrencies carries substantial financial risk.

### Key Warnings

1. **Paper Trading is Enabled by Default**: The bot runs in simulation mode (`paper_trading: true`) by default. **DO NOT enable live trading without extensive testing.**

2. **No Guarantee of Profitability**: Past performance does not guarantee future results. Market conditions change rapidly, and AI models can fail unexpectedly.

3. **Test Extensively**: Before committing real capital:
   - Run the bot in paper trading mode for at least 2 weeks
   - Backtest your strategy across multiple market conditions
   - Monitor logs and metrics closely
   - Start with minimal position sizes

4. **API Risk**: Your Binance API keys provide access to your trading account. Store them securely and rotate them regularly.

5. **Network Risk**: Internet connectivity issues may cause missed trades or delayed order cancellations. Always set appropriate stop losses.

6. **Technical Risk**: Bugs or crashes are possible. The developers assume no liability for losses.

### Legal Notice

Automated trading may be subject to regulations in your jurisdiction. Consult a financial advisor before deploying this bot with real capital.

**By using this software, you acknowledge and accept all associated risks.**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Questions?** Open an issue on [GitHub](https://github.com/iulianipro/-Cortex-v2---Trading-Bot-Framework/issues) or check out the documentation in the `/docs` folder.
