# System Information Feature - "что мы имеем" (What We Have)

## Overview

This feature answers the question "что мы имеем" (Russian: "what we have") by providing a comprehensive system inventory and status through both REST API and Telegram bot interfaces.

## Implementation Details

### 1. REST API Endpoint

**Endpoint:** `GET /api/v1/system-info`

**Location:** `backend/api/routes.py`

**Response Structure:**
```json
{
  "system": {
    "name": "Swing Trend Trading Bot",
    "version": "1.0.0",
    "phase": "Phase 0 - Paper Trading",
    "timestamp": "2025-11-22T12:00:00"
  },
  "configuration": {
    "initial_capital": 500.0,
    "risk_per_trade": "2.0%",
    "max_open_positions": 1,
    "daily_loss_limit": "6.0%",
    "timeframe": "1h",
    "timezone": "Europe/Luxembourg"
  },
  "strategy": {
    "name": "Swing Trend Baseline",
    "indicators": {
      "ema_fast": 9,
      "ema_slow": 21,
      "rsi_length": 14,
      "rsi_long_threshold": 50,
      "rsi_short_threshold": 50,
      "atr_length": 14,
      "breakout_lookback": 40
    },
    "risk_management": {
      "stop_loss": "Entry ± 2*ATR",
      "take_profit": "Entry ± 2.5*(Entry-StopLoss)",
      "risk_reward_ratio": 2.5
    }
  },
  "portfolio": {
    "equity": 500.00,
    "available_capital": 500.00,
    "open_positions": 0,
    "positions_detail": [],
    "total_pnl": 0.00,
    "pnl_percentage": 0.00
  },
  "statistics": {
    "total_trades": 0,
    "closed_trades": 0,
    "open_trades": 0,
    "winning_trades": 0,
    "losing_trades": 0,
    "win_rate": 0.00,
    "average_win": 0.00,
    "average_loss": 0.00,
    "profit_factor": 0.00,
    "gross_profit": 0.00,
    "gross_loss": 0.00
  },
  "exchange": {
    "name": "Binance",
    "mode": "testnet",
    "status": "connected",
    "btcusdt_price": 45000.00,
    "api_configured": true
  },
  "features": {
    "api_endpoints": [
      "GET /api/v1/status - Portfolio status",
      "GET /api/v1/signals/{symbol} - Check trading signal",
      "POST /api/v1/execute/{symbol} - Open position",
      "GET /api/v1/positions - List open positions",
      "POST /api/v1/update-positions/{symbol} - Update positions",
      "GET /api/v1/trades/history - Trade history",
      "GET /api/v1/system-info - System information",
      "GET /health - Health check"
    ],
    "telegram_commands": [
      "/start - Welcome message",
      "/help - Command help",
      "/status - Portfolio status",
      "/signals BTCUSDT - Check signal",
      "/execute BTCUSDT - Open position",
      "/positions - List positions",
      "/update BTCUSDT - Update positions",
      "/history - Trade history",
      "/system - System information"
    ]
  },
  "database": {
    "connection": "PostgreSQL + TimescaleDB",
    "tables": ["trades", "ohlcv", "portfolio_state"],
    "total_records": 0
  }
}
```

### 2. Telegram Bot Command

**Command:** `/system`

**Location:** `bot/main.py`

**Display Format:**
```
🤖 Swing Trend Trading Bot
📌 Phase 0 - Paper Trading
🔖 Version: 1.0.0

⚙️ Конфигурация:
💰 Initial Capital: $500
⚠️ Risk per Trade: 2.0%
📊 Max Positions: 1
🛑 Daily Loss Limit: 6.0%
⏰ Timeframe: 1h

📈 Стратегия: Swing Trend Baseline
• EMA Fast/Slow: 9/21
• RSI: 14
• ATR: 14
• Breakout Lookback: 40
• R:R Ratio: 2.5

💼 Портфель:
💰 Equity: $500.00
💵 Available: $500.00
📊 Open Positions: 0
💸 Total P&L: $0.00 (0.00%)

📊 Статистика:
📝 Total Trades: 0
✅ Closed: 0 | 🔓 Open: 0
🟢 Wins: 0 | 🔴 Losses: 0
🎯 Win Rate: 0.0%
📈 Avg Win: $0.00
📉 Avg Loss: $0.00
💹 Profit Factor: 0.00

🔗 Exchange:
• Binance (TESTNET)
• Status: connected
• API Configured: ✅
• BTC/USDT: $45000.00

💾 База данных:
• PostgreSQL + TimescaleDB
• Tables: 3
• Records: 0
```

## Changes Summary

### Modified Files

1. **backend/api/routes.py** (+140 lines)
   - Added `get_system_info()` endpoint
   - Comprehensive data aggregation from multiple sources
   - Error handling and exception management

2. **bot/main.py** (+78 lines)
   - Added `system_command()` handler
   - Updated `start_command()` to include `/system`
   - Updated `help_command()` with `/system` documentation
   - Registered handler in `main()`

3. **README.md** (+5 lines)
   - Added `/system` command description
   - Documented command features

4. **QUICKSTART.md** (+1 line)
   - Added `/system` to command reference

## Use Cases

### 1. Quick System Overview
**User Action:** Send `/system` in Telegram or GET `/api/v1/system-info`
**Use Case:** Get a complete snapshot of system state, configuration, and performance

### 2. Performance Monitoring
**User Action:** Check statistics section
**Use Case:** Monitor win rate, profit factor, and trading performance

### 3. Configuration Verification
**User Action:** Check configuration section
**Use Case:** Verify risk management parameters and strategy settings

### 4. System Health Check
**User Action:** Check exchange and database status
**Use Case:** Ensure all system components are operational

### 5. Feature Discovery
**User Action:** Check features section
**Use Case:** Learn what API endpoints and commands are available

## Testing

### Manual Testing Steps

1. **Start the system:**
   ```bash
   docker-compose up -d
   ```

2. **Test REST API:**
   ```bash
   # Via curl
   curl http://localhost:8000/api/v1/system-info | jq

   # Via browser
   http://localhost:8000/docs
   # Then test the /api/v1/system-info endpoint
   ```

3. **Test Telegram Bot:**
   - Open Telegram
   - Find your bot
   - Send `/system`
   - Verify comprehensive output

### Expected Behaviors

- ✅ Endpoint returns JSON with all sections
- ✅ No errors when database is empty (0 trades)
- ✅ Exchange status reflects actual connection state
- ✅ Telegram command displays formatted, readable output
- ✅ Statistics calculate correctly (handle division by zero)
- ✅ All configuration values match .env settings

## Benefits

1. **Single Command Visibility:** Everything about the system in one command
2. **Troubleshooting:** Quick diagnosis of configuration issues
3. **Monitoring:** Real-time performance metrics
4. **Documentation:** Self-documenting available features
5. **Onboarding:** New users can understand system capabilities instantly

## Future Enhancements

Potential improvements for future iterations:

1. **Caching:** Cache system info for 1 minute to reduce database queries
2. **Filtering:** Allow filtering sections (e.g., `/system --stats-only`)
3. **Export:** Add CSV/JSON export of statistics
4. **Comparison:** Compare current vs. initial state
5. **Alerts:** Notify when key metrics cross thresholds
6. **Historical:** Track system state changes over time

## Architecture Notes

### Data Sources

- **Configuration:** `backend/config.py` (Settings class)
- **Portfolio:** `PaperTradingEngine.get_status()`
- **Statistics:** Database queries on `Trade` model
- **Exchange:** `MarketDataService.get_ticker()`
- **Features:** Hardcoded list (consider generating dynamically)

### Performance Considerations

- Database query fetches ALL trades (consider pagination for large datasets)
- Exchange ticker call may timeout if Binance is down
- Async operations ensure non-blocking behavior

### Error Handling

- Graceful degradation if exchange is disconnected
- Safe division (avoid division by zero in statistics)
- HTTPException with 500 status on unexpected errors

## Maintenance

### Updating Feature Lists

When adding new endpoints or commands, update the hardcoded lists in:
- `backend/api/routes.py` line ~413 (api_endpoints list)
- `backend/api/routes.py` line ~423 (telegram_commands list)

### Version Management

Update version in:
- `backend/api/routes.py` line ~364 ("version": "1.0.0")
- `backend/main.py` line ~14 (FastAPI version)

## Related Documentation

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Project Summary:** `PROJECT_SUMMARY.md`
- **Quick Start:** `QUICKSTART.md`
- **README:** `README.md`

---

**Last Updated:** November 22, 2025
**Author:** Copilot SWE Agent
**Feature Status:** ✅ Implemented and Documented
