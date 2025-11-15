# GitHub Copilot & ChatGPT Instructions

## Project Context

You're working on **Spark** - a Phase 0 paper trading bot for cryptocurrency. This is a 2-week validation project before live trading starts December 1, 2025.

**Key Facts:**
- Trading Bot: Swing Trend Baseline strategy (EMA crossover + RSI + breakouts)
- Exchange: Binance Testnet (paper trading only)
- Capital: $500, Risk: 2% per trade, Max: 1 position
- Stack: Python, FastAPI, PostgreSQL+TimescaleDB, Redis, Telegram Bot, Docker
- Architecture: Microservices (Telegram → REST API → Database → Binance)

## Code Style

- Python 3.11+, PEP 8, async/await everywhere
- Type hints mandatory
- Google-style docstrings
- Error handling: specific exceptions only
- Logging: use `logging` module (not print)

## Critical Rules

**Risk Management (NEVER violate):**
- Max 1 open position (`MAX_OPEN_POSITIONS=1`)
- Risk exactly 2% per trade
- Daily loss limit: 6%
- Position size = `risk_amount / abs(entry - stop_loss)`
- Stop loss = `entry ± 2*ATR`
- Take profit = `entry ± 2.5*stop_distance`

**Security:**
- Never commit API keys (already in `.gitignore`)
- Testnet only (`EXCHANGE_TESTNET=true`)
- No hardcoded values (use `backend/config.py`)

## File Structure Quick Reference

```
backend/
├── api/routes.py          # 7 REST endpoints
├── models/trade.py        # SQLAlchemy Trade model
├── services/
│   ├── market_data.py     # ccxt wrapper (Binance)
│   └── paper_trading.py   # Paper trading engine
├── strategies/
│   └── swing_trend.py     # Strategy (EMA, RSI, breakout logic)
├── config.py              # All settings (Pydantic)
├── database.py            # SQLAlchemy async
└── main.py                # FastAPI app

bot/
├── main.py                # Telegram bot (8 commands)
└── config.py              # Bot settings

migrations/
└── 001_initial.sql        # PostgreSQL schema (TimescaleDB)

docker-compose.yml         # 4 services orchestration
.env                       # Config (NEVER commit)
```

## Common Patterns

**Database query:**
```python
async def get_trades(db: AsyncSession, status: str = None):
    query = select(Trade).order_by(Trade.opened_at.desc())
    if status:
        query = query.where(Trade.status == status)
    result = await db.execute(query)
    return result.scalars().all()
```

**API endpoint:**
```python
@router.get("/api/v1/endpoint", response_model=ResponseModel)
async def endpoint(db: AsyncSession = Depends(get_db)):
    try:
        # ... logic
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Telegram command:**
```python
async def command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/endpoint")
            data = response.json()
        await update.message.reply_text(f"Result: {data}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
```

## Strategy Signal Logic

**Long signal:**
- EMA fast > EMA slow (uptrend)
- RSI > 50 (bullish momentum)
- Close > highest high of last 40 bars (breakout)

**Short signal:**
- EMA fast < EMA slow (downtrend)
- RSI < 50 (bearish momentum)
- Close < lowest low of last 40 bars (breakdown)

**Implementation in `backend/strategies/swing_trend.py`:**
```python
def generate_signal(self, df: pd.DataFrame) -> Optional[Dict]:
    latest = df.iloc[-1]
    
    if latest['uptrend'] and latest['rsi'] > 50 and latest['close'] > df.iloc[-2]['highest_high']:
        entry = latest['close']
        stop = entry - (2 * latest['atr'])
        tp = entry + (2.5 * (entry - stop))
        return {'side': 'long', 'entry': entry, 'stop': stop, 'tp': tp}
    
    return None
```

## Testing Commands

```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f bot

# Rebuild after changes
docker-compose up -d --build backend

# Test API
curl http://localhost:8000/health
# Or open: http://localhost:8000/docs (Swagger UI)

# Database query
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT * FROM trades;"

# Restart service
docker-compose restart backend
```

## When Editing Code

**Before:**
1. Read relevant files (understand context)
2. Check existing patterns (match style)
3. Verify imports and dependencies

**During:**
1. Follow existing structure
2. Add docstrings (explain why, not just what)
3. Handle errors (specific exceptions)
4. Log important events

**After:**
1. Test manually (Docker, Swagger UI)
2. Check logs (`docker-compose logs`)
3. Verify database (psql queries)

## Phase 0 Success Criteria

After 2 weeks, bot must pass:
- Net Profit > $0
- Win Rate > 50%
- Profit Factor > 1.2
- Max Drawdown < 10%
- Total Trades ≥ 10

## Important Files

- **Full instructions:** `.cursorrules` (comprehensive guide)
- **Setup guide:** `README.md`
- **Quick reference:** `QUICKSTART.md`
- **Project summary:** `PROJECT_SUMMARY.md`
- **ChatGPT integration:** `CHATGPT_INTEGRATION.md`

## API Endpoints

1. `GET /api/v1/status` - Portfolio equity, positions, P&L
2. `GET /api/v1/signals/{symbol}` - Generate trading signal
3. `POST /api/v1/execute/{symbol}` - Open position
4. `GET /api/v1/positions` - List open positions
5. `POST /api/v1/update-positions/{symbol}` - Check SL/TP hits
6. `GET /api/v1/trades/history` - Closed trades history
7. `GET /health` - Health check

## Telegram Bot Commands

1. `/start` - Welcome message
2. `/help` - Command list
3. `/status` - Portfolio status
4. `/signals BTCUSDT` - Check for signal
5. `/execute BTCUSDT` - Open position
6. `/positions` - List open positions
7. `/update BTCUSDT` - Update position (check SL/TP)
8. `/history` - Last 20 trades

## Configuration (.env)

Required variables:
- `EXCHANGE_API_KEY` - Binance Testnet API key
- `EXCHANGE_API_SECRET` - Binance Testnet secret
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `DATABASE_URL` - PostgreSQL connection string
- `INITIAL_CAPITAL=500.0`
- `RISK_PER_TRADE=2.0`
- `MAX_OPEN_POSITIONS=1`
- `DAILY_LOSS_LIMIT=6.0`
- Strategy params: `EMA_FAST=9`, `EMA_SLOW=21`, `RSI_LENGTH=14`, `LOOKBACK=40`, `ATR_LENGTH=14`, `RR_RATIO=2.5`

## Quick Answers to Common Questions

**Q: How to add new endpoint?**
A: Add route in `backend/api/routes.py`, create Pydantic model, test via Swagger UI

**Q: How to modify strategy?**
A: Edit `backend/strategies/swing_trend.py`, update indicators/signal logic, rebuild Docker

**Q: How to add database table?**
A: Create migration SQL in `migrations/`, add SQLAlchemy model in `backend/models/`, run migration via psql

**Q: Bot not responding?**
A: Check `docker-compose logs bot`, verify `TELEGRAM_BOT_TOKEN` in .env, ensure backend is running

**Q: Where are API keys?**
A: In `.env` file (never commit this file, it's in `.gitignore`)

**Q: How to test without Docker?**
A: Not recommended, but possible: install PostgreSQL, Redis, Python deps, set .env, run `uvicorn backend.main:app` + `python bot/main.py`

## Repository

https://github.com/QOAB/spark

## Last Updated

November 16, 2025 - Phase 0 (Paper Trading)
