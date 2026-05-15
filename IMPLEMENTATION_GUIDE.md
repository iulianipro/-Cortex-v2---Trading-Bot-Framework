# Cortex v2 - Implementation Guide & Advanced Usage

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Component Integration](#component-integration)
3. [Advanced Configuration](#advanced-configuration)
4. [Deployment](#deployment)
5. [Troubleshooting](#troubleshooting)

---

## Core Concepts

### 1. Event-Driven Architecture

Every action in Cortex is an **event**. Components emit events and listen to events they care about.

```python
from cortex.core.event_bus import emit_event, get_event_bus

# Emit an event
await emit_event(
    event_type="signal_generated",
    source="brain_ai",
    data={
        "symbol": "BTCUSDT",
        "signal_type": "BUY",
        "confidence": 0.78,
        "entry_price": 42500.0
    }
)

# Subscribe to events
event_bus = get_event_bus()
await event_bus.subscribe("signal_generated", my_handler)

async def my_handler(event):
    print(f"Signal: {event.data['symbol']}")
```

**Benefits:**
- ✅ Loose coupling - components don't know about each other
- ✅ Easy testing - mock events instead of entire systems
- ✅ Scalability - add new listeners without modifying existing code
- ✅ Failover - components can be swapped transparently

### 2. Modular Components

Each component is independent and swappable:

```python
# Strategy Type A: AI-based
async def brain_ai_decide(symbol, data):
    # Use HuggingFace API
    pass

# Strategy Type B: Technical Analysis
async def brain_technical_decide(symbol, data):
    # Use indicators only
    pass

# In config.yaml - choose which to use
strategy_type: "hybrid"  # Can change without code modification
```

### 3. Async Concurrency

Monitor 10+ pairs simultaneously:

```python
# Monitor pairs in parallel
async def monitoring_loop():
    while running:
        tasks = [
            analyze_symbol("BTCUSDT"),
            analyze_symbol("ETHUSDT"),
            analyze_symbol("XAUUSDT"),
            # ... more pairs
        ]
        await asyncio.gather(*tasks)  # All run concurrently
```

---

## Component Integration

### Implementing a Custom Data Provider

```python
# cortex/sense/your_exchange_client.py

from cortex.core.base_component import DataProvider
import pandas as pd

class YourExchangeClient(DataProvider):
    def __init__(self, api_key: str, api_secret: str):
        super().__init__("your_exchange")
        self.api_key = api_key
        self.api_secret = api_secret
    
    async def start(self):
        self._is_running = True
        logger.info("Your Exchange client started")
    
    async def stop(self):
        self._is_running = False
    
    async def fetch_ohlcv(self, symbol: str, interval: str, limit: int = 100):
        """Fetch OHLCV from your exchange"""
        try:
            # Your exchange API call here
            response = await self._api_call(f"/klines/{symbol}/{interval}")
            
            # Convert to DataFrame
            df = pd.DataFrame(response)
            
            # Emit event
            await self.emit_event("data_fetched", {
                "symbol": symbol,
                "rows": len(df),
                "latest_price": df.iloc[-1]['close']
            })
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {str(e)}")
            return pd.DataFrame()
```

### Implementing a Custom Decision Engine

```python
# cortex/brain/strategies/my_strategy.py

from cortex.core.base_component import DecisionEngine, Signal
from datetime import datetime

class MyHybridStrategy(DecisionEngine):
    def __init__(self, ai_enabled: bool = True):
        super().__init__("my_hybrid_strategy")
        self.ai_enabled = ai_enabled
    
    async def start(self):
        self._is_running = True
    
    async def stop(self):
        self._is_running = False
    
    async def decide(self, symbol: str, market_data, analysis: dict) -> Signal:
        """
        Make decision combining AI + Technical Analysis
        """
        # Get analysis results
        order_blocks = analysis.get('order_blocks', [])
        fvgs = analysis.get('fvgs', [])
        cvd = analysis.get('cvd', {})
        
        # AI score (if enabled)
        ai_score = 0
        if self.ai_enabled:
            ai_score = await self._get_ai_score(symbol)
        
        # Technical score
        ta_score = await self._get_technical_score(order_blocks, fvgs)
        
        # Combine scores
        final_score = (ai_score * 0.4) + (ta_score * 0.6)
        
        if final_score > 0.65:  # Confidence threshold
            # Generate BUY signal
            return Signal(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                signal_type='BUY',
                confidence=final_score,
                entry_price=market_data.close,
                stop_loss=market_data.close * 0.97,  # 3% below
                take_profit=market_data.close * 1.05,  # 5% above
                reason=f"Hybrid signal: AI={ai_score:.2f}, TA={ta_score:.2f}",
                source="my_hybrid_strategy"
            )
        
        return None
    
    async def _get_ai_score(self, symbol: str) -> float:
        """Query AI model for confidence score"""
        try:
            # HuggingFace API call
            pass
        except:
            return 0.0  # Fallback
    
    async def _get_technical_score(self, order_blocks, fvgs) -> float:
        """Calculate technical analysis score"""
        score = 0.0
        
        # Order block proximity
        if order_blocks and order_blocks[0]['type'] == 'bullish':
            score += 0.3
        
        # FVG proximity
        if fvgs and fvgs[0]['type'] == 'bullish':
            score += 0.2
        
        return score
```

---

## Advanced Configuration

### Multi-Profile Setup

```yaml
# config/profiles/aggressive.yaml
strategy_type: "ai_only"
confidence_threshold: 0.60
max_portfolio_risk: 0.10
position_size_pct: 0.05
max_drawdown: 0.15

# config/profiles/conservative.yaml
strategy_type: "hybrid"
confidence_threshold: 0.75
max_portfolio_risk: 0.03
position_size_pct: 0.01
max_drawdown: 0.05
```

### Dynamic Risk Adjustment

```python
# Adjust risk based on market conditions
async def adjust_risk_parameters(market_volatility: float):
    if market_volatility > 0.05:  # High volatility
        config.max_portfolio_risk = 0.02  # Reduce to 2%
        logger.warning(f"High volatility detected: {market_volatility:.2%}")
    else:
        config.max_portfolio_risk = 0.05  # Normal: 5%
```

---

## Deployment

### Docker Deployment

```dockerfile
# docker/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cortex/ ./cortex/
COPY config/ ./config/
COPY main.py .

ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

CMD ["python", "main.py"]
```

### Running in Docker

```bash
# Build image
docker build -f docker/Dockerfile -t cortex:v2 .

# Run container
docker run -d \
  -e API_KEY=$BINANCE_KEY \
  -e API_SECRET=$BINANCE_SECRET \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  cortex:v2
```

### Kubernetes Deployment (Future)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cortex-trading-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cortex-bot
  template:
    metadata:
      labels:
        app: cortex-bot
    spec:
      containers:
      - name: cortex
        image: cortex:v2
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: api-key
        - name: API_SECRET
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: api-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
```

---

## Troubleshooting

### Issue: Bot not detecting signals

**Diagnosis:**
```python
# Check event bus history
event_history = event_bus.get_event_history("signal_generated", limit=50)
if not event_history:
    logger.warning("No signals generated in last 50 events")

# Check analysis results
analysis = await order_block_detector.detect(df)
if not analysis:
    logger.warning("No order blocks detected - check data quality")
```

**Solution:**
1. Verify data is flowing properly: Check `market_update` events
2. Check indicator parameters in `config.yaml`
3. Lower confidence thresholds temporarily to see if signals are generated
4. Verify exchange API connection

### Issue: High slippage on order execution

**Solution:**
```yaml
# Increase limit order offset
order_type: "limit"
limit_offset_pct: 0.003  # 0.3% above market price

# Or use market orders when confident
order_type: "market"
```

### Issue: Excessive drawdown

**Solution:**
```yaml
# Tighten risk parameters
max_portfolio_risk: 0.02  # Reduce from 5% to 2%
max_drawdown: 0.05        # Reduce from 10% to 5%
position_size_pct: 0.01   # Reduce from 2% to 1%

# Use trailing stops
use_trailing_stop: true
trailing_stop_pct: 0.03   # Tighter stops
```

### Issue: API rate limiting

**Solution:**
```python
# Add request rate limiting
class RateLimitedClient:
    def __init__(self, max_requests_per_second: int = 10):
        self.rate_limiter = asyncio.Semaphore(max_requests_per_second)
    
    async def api_call(self, endpoint: str):
        async with self.rate_limiter:
            await asyncio.sleep(1 / max_requests_per_second)
            return await self._fetch(endpoint)
```

---

## Performance Optimization Tips

1. **Use appropriate timeframes**: 1m for day trading, 1h for swing trading
2. **Limit historical lookback**: 100 bars usually sufficient
3. **Cache indicator results**: Don't recalculate if data unchanged
4. **Batch API calls**: Fetch multiple symbols in one request
5. **Monitor memory**: Check memory usage with more pairs

```python
# Memory-efficient indicator calculation
def calculate_efficiently(df: pd.DataFrame) -> dict:
    # Only calculate needed columns
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    # In-place operations where possible
    df['rsi'] = calculate_rsi(df['close'])
    
    # Delete unnecessary data
    del df['open']  # If not needed
    
    return df
```

---

**Cortex v2 is production-ready. Deploy with confidence!**
