# CORTEX v2 - Quick Reference Guide

## 🚀 Quick Start (5 minutes)

```bash
# 1. Setup
git clone <repo>
cd cortex_v2
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys
# Edit config/config.yaml for trading settings

# 3. Run
python main.py  # Paper trading by default
```

## 📦 Project Structure

```
cortex_v2/
├── cortex/                    # Main package
│   ├── core/                  # Core framework
│   │   ├── event_bus.py       # Pub/Sub system
│   │   └── base_component.py  # Abstract interfaces
│   │
│   ├── sense/                 # Data & Analysis Layer
│   │   ├── indicators/
│   │   │   ├── order_block.py    # OB detection
│   │   │   ├── fvg_detector.py   # FVG detection
│   │   │   └── cvd_calculator.py # CVD analysis
│   │   └── pipeline.py           # Data processing
│   │
│   ├── brain/                 # Decision Engine
│   │   └── strategies/        # Signal generation
│   │
│   ├── risk/                  # Risk Management
│   │   └── global_risk_manager.py # Portfolio protection
│   │
│   ├── exec/                  # Order Execution
│   │   └── order_executor.py  # Place trades
│   │
│   ├── utils/                 # Utilities
│   │   ├── logger.py          # JSON logging
│   │   └── config_loader.py   # Configuration
│   │
│   └── bot.py                 # Main orchestrator
│
├── config/
│   ├── config.yaml            # Main configuration
│   └── .env.example           # API credentials template
│
├── tests/
│   ├── test_order_blocks.py   # Unit tests
│   └── integration_test.py     # End-to-end tests
│
└── example_complete.py        # Usage examples
```

## 🔑 Key Components

### 1. SENSE - Market Analysis
```python
from cortex.sense.indicators import OrderBlockDetector, FVGDetector

detector = OrderBlockDetector()
blocks = detector.detect(df)  # Returns list of OrderBlock objects
```

### 2. BRAIN - Decision Making
```python
async def brain_decide(symbol, market_data, analysis):
    # Combine AI + Technical Analysis
    # Return trading Signal
    return Signal(...)
```

### 3. RISK - Portfolio Protection
```python
from cortex.risk import GlobalRiskManager

risk_mgr = GlobalRiskManager(
    max_portfolio_risk=0.05,
    max_drawdown=0.10
)
approved = await risk_mgr.evaluate_risk(signal, portfolio_state)
```

### 4. EXEC - Order Execution
```python
# Place order (market, limit, or trailing stop)
order = await executor.execute(signal)
```

## 🎛️ Configuration

### Minimal Setup (config.yaml)
```yaml
api_key: "${API_KEY}"              # From .env
api_secret: "${API_SECRET}"        # From .env
trading_pairs: ["BTCUSDT", "ETHUSDT"]
max_portfolio_risk: 0.05
strategy_type: "hybrid"            # hybrid, ai_only, technical_only
```

### Risk Parameters
```yaml
max_portfolio_risk: 0.05           # 5% of portfolio at risk
max_drawdown: 0.10                 # 10% max drawdown
position_size_pct: 0.02            # 2% risk per trade
max_daily_loss: 0.02               # 2% daily loss limit
```

### Strategy Choice
```yaml
# Option 1: Hybrid (AI + Technical)
strategy_type: "hybrid"
ai_model: "chronos"
confidence_threshold: 0.65

# Option 2: AI Only
strategy_type: "ai_only"

# Option 3: Technical Only (No AI)
strategy_type: "technical_only"
ai_enabled: false
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_order_blocks.py -v

# With coverage
pytest tests/ --cov=cortex
```

## 📊 Monitoring

### Check Event History
```python
event_bus = get_event_bus()
history = event_bus.get_event_history("signal_generated", limit=100)
```

### View Logs
```bash
# Real-time JSON logs
tail -f logs/cortex.log | jq '.'

# Filter by signal events
grep "signal_generated" logs/cortex.log | jq '.data'
```

### Portfolio Stats
```python
stats = risk_mgr.get_portfolio_stats()
print(f"Exposure: {stats['exposure_pct']:.2%}")
print(f"Win Rate: {stats['win_rate']:.2%}")
print(f"Daily P&L: ${stats['daily_pnl']:,.0f}")
```

## 🔄 Event Types

| Event | Source | Purpose |
|-------|--------|---------|
| `market_update` | Data Fetcher | New market data received |
| `analysis_complete` | Sense Module | Indicators calculated |
| `signal_generated` | Brain Module | Trading signal created |
| `risk_approved` | Risk Manager | Signal passed risk checks |
| `order_placed` | Order Executor | Trade executed |
| `position_closed` | Order Manager | Position closed |

## ⚙️ Extending Cortex

### Add Custom Indicator
```python
# cortex/sense/indicators/my_indicator.py
class MyIndicator(AnalysisModule):
    async def analyze(self, data):
        # Your analysis logic
        return {"result": value}
```

### Add Custom Strategy
```python
# cortex/brain/strategies/my_strategy.py
class MyStrategy(DecisionEngine):
    async def decide(self, symbol, data, analysis):
        # Generate signals
        return Signal(...)
```

### Add Custom Exchange
```python
# cortex/sense/my_exchange_client.py
class MyExchangeClient(DataProvider):
    async def fetch_ohlcv(self, symbol, interval):
        # Fetch data from your exchange
        pass
```

## ⚠️ Important Notes

1. **Paper Trading**: Enabled by default (`paper_trading: true`)
2. **Test First**: Always test with small positions
3. **Monitor Logs**: Check logs for errors and signals
4. **Risk Management**: Never trade with money you can't afford to lose
5. **API Limits**: Respect exchange rate limits

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| No signals | Check indicator parameters, lower confidence threshold |
| High slippage | Use limit orders instead of market |
| API errors | Verify credentials, check rate limits |
| Memory issues | Reduce lookback period, use fewer pairs |
| Slow processing | Check for blocking I/O, use async properly |

## 📚 Documentation

- `README.md` - Project overview
- `IMPLEMENTATION_GUIDE.md` - Detailed implementation examples
- `example_complete.py` - Complete working example
- `tests/` - Test examples and patterns

## 🎯 Next Steps

1. **Setup**: Install and configure
2. **Test**: Run examples and tests
3. **Backtest**: Test strategy with historical data
4. **Paper Trade**: Use paper trading for 2-4 weeks
5. **Live**: Start with small position sizes
6. **Monitor**: Check logs and metrics daily
7. **Iterate**: Adjust parameters based on results

## 📞 Support Resources

- Python Async: `https://docs.python.org/3/library/asyncio.html`
- Pandas: `https://pandas.pydata.org/`
- Event-Driven Design: `https://en.wikipedia.org/wiki/Event-driven_architecture`
- Smart Money Concepts: Order Blocks, FVG, CSA

---

**Cortex v2 is production-ready. Deploy with confidence!**

Last Updated: 2024-01-15
