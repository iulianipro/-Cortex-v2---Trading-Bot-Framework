# Cortex v2 - Trading Bot Architecture

```
cortex_v2/
├── config/
│   ├── config.yaml                 # Configuration centralizată
│   ├── .env.example                # Template variabile de mediu
│   └── strategy_profiles.yaml       # Profiluri de strategie
│
├── cortex/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── event_bus.py            # Pub/Sub Event System
│   │   ├── base_component.py       # Abstract Base Classes
│   │   └── state_machine.py        # State management per pereche
│   │
│   ├── sense/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py         # Interface generică pentru exchange-uri
│   │   ├── binance_client.py       # Implementare Binance
│   │   ├── indicators/
│   │   │   ├── __init__.py
│   │   │   ├── ta_indicators.py    # Indicatori TA standard
│   │   │   ├── order_block.py      # Detectare Order Blocks
│   │   │   ├── fvg_detector.py     # Fair Value Gaps
│   │   │   └── cvd_calculator.py   # Cumulative Volume Delta
│   │   └── pipeline.py             # Pipeline de procesare date
│   │
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── base_strategy.py        # Interfață strategie
│   │   ├── ai_engine.py            # Integration Hugging Face (Chronos/FinBERT)
│   │   ├── strategies/
│   │   │   ├── __init__.py
│   │   │   ├── technical_fallback.py # Strategie de backup
│   │   │   └── hybrid_strategy.py   # AI + TA hibridă
│   │   └── decision_maker.py       # State Machine + Decision Logic
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── global_risk_manager.py  # Portfolio-level risk
│   │   ├── position_sizer.py       # Calculare mărime pozițiie
│   │   └── drawdown_monitor.py     # Monitorizare MaxDD
│   │
│   ├── exec/
│   │   ├── __init__.py
│   │   ├── order_executor.py       # Execuție ordine (Limit/Market)
│   │   ├── trailing_stop.py        # Implementare Trailing Stop
│   │   └── order_manager.py        # Gestionare lifecycle ordine
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py               # JSON logging structurat
│   │   ├── config_loader.py        # Parsing config.yaml
│   │   └── metrics.py              # Calculare metrici P&L
│   │
│   └── bot.py                      # Orchestrator principal
│
├── tests/
│   ├── __init__.py
│   ├── test_order_blocks.py        # Unit tests Order Blocks
│   ├── test_risk_manager.py        # Unit tests Risk
│   ├── test_decision_maker.py      # Unit tests Brain
│   └── integration_test.py         # Simulare end-to-end
│
├── notebooks/
│   ├── backtest_analysis.ipynb     # Analiza backtesting
│   └── indicator_exploration.ipynb # Explorare indicatori
│
├── docker/
│   └── Dockerfile                  # Container pentru deployment
│
├── requirements.txt                # Dependințe Python
├── .env.example                    # Template variabile
├── main.py                         # Entry point
└── README.md                       # Documentație
```

## Flux de Operare (Event-Driven)

```
[Market Data] 
      ↓
[Data Fetcher] --emit--> EVENT: "market_update"
      ↓
[Indicators Pipeline] --process--> [Order Blocks, FVG, CVD]
      ↓
[Brain: AI Engine] + [Fallback Strategy] --emit--> EVENT: "signal_generated"
      ↓
[Risk Manager] --validate--> "Is portfolio safe?"
      ↓
[Position Sizer] --calculate--> "Cât risc la trade?"
      ↓
[Order Executor] --execute--> Binance API
      ↓
[Trailing Stop Monitor] --monitor--> "Să închid poziția?"
```

## Key Principles

✅ **Decoupling Total**: Fiecare componentă ascultă doar la event-uri, nu cunoaște alte componente
✅ **Failover Automat**: Dacă HuggingFace API scade → automatic fallback la Technical Analysis
✅ **Configurare YAML**: Schimbă strategie fără a rescrie cod
✅ **Logging Structurat**: Orice acțiune este logată cu timestamp și context
✅ **Async/Await**: Monitorizează 10+ perechi în paralel
✅ **Testabil**: Fiecare modul poate fi testat independent cu mock data
