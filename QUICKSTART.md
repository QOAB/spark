# 🚀 Quick Start Cheat Sheet

## 📦 Initial Setup (One-time, 30 min)

```powershell
# 1. Create .env from template
Copy-Item .env.example .env

# 2. Edit .env - add your keys:
#    - EXCHANGE_API_KEY=<Binance Testnet API Key>
#    - EXCHANGE_API_SECRET=<Binance Testnet Secret>
#    - TELEGRAM_BOT_TOKEN=<Your Bot Token>

# 3. Start all services
docker-compose up -d

# 4. Check status (all should be "Up")
docker-compose ps

# 5. Initialize database
docker-compose exec postgres psql -U postgres -d trading_bot -f /docker-entrypoint-initdb.d/001_initial.sql

# 6. Test Telegram bot
#    Send /start to your bot in Telegram
```

---

## 🔄 Daily Operations (5 min/day)

```powershell
# Morning (9:00 CET)
# 1. Check if services are running
docker-compose ps

# 2. If not running, start them
docker-compose start

# 3. Telegram: /status
# 4. Telegram: /update BTCUSDT (if positions open)

# Evening (21:00 CET)
# 1. Telegram: /signals BTCUSDT
# 2. If signal exists: /execute BTCUSDT
# 3. Telegram: /status
```

---

## 🐛 Troubleshooting

```powershell
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f bot

# Restart everything
docker-compose restart

# Rebuild from scratch (if code changed)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check database
docker-compose exec postgres psql -U postgres -d trading_bot
# Then: SELECT * FROM trades;
# Exit: \q

# Stop everything
docker-compose stop

# Remove everything (keeps data)
docker-compose down

# Remove everything + data (DANGEROUS!)
docker-compose down -v
```

---

## 📊 Monitoring Commands

```powershell
# Check portfolio state
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT * FROM portfolio_state ORDER BY timestamp DESC LIMIT 1;"

# Check all trades
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT symbol, side, pnl, pnl_pct, status, closed_at FROM trades ORDER BY opened_at DESC LIMIT 10;"

# Daily stats
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT * FROM daily_stats;"

# Symbol performance
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT * FROM symbol_performance;"

# Win rate calculation
docker-compose exec postgres psql -U postgres -d trading_bot -c "SELECT COUNT(*) FILTER (WHERE pnl > 0) * 100.0 / COUNT(*) as win_rate FROM trades WHERE status='closed';"
```

---

## 📱 Telegram Commands Quick Reference

```
/start              Welcome message + command list
/help               Detailed help
/status             Portfolio status + P&L
/signals BTCUSDT    Check for trading signal
/execute BTCUSDT    Open position (if signal exists)
/positions          Show all open positions
/update BTCUSDT     Update positions (check SL/TP)
/history            Last 20 closed trades
/system             Complete system information and stats
```

---

## 🔑 Important URLs

- **Binance Testnet**: https://testnet.binance.vision/
- **TradingView**: https://www.tradingview.com/
- **Backend API**: http://localhost:8000/docs (Swagger UI)
- **Database**: localhost:5432 (user: postgres, db: trading_bot)
- **Redis**: localhost:6379

---

## ⚙️ Configuration Files

```
.env                    # YOUR KEYS (never commit!)
docker-compose.yml      # Container orchestration
backend/config.py       # Backend settings
bot/config.py          # Bot settings
```

---

## 📁 Key Files Structure

```
trading-bot/
├── backend/            # FastAPI backend
│   ├── api/            # REST endpoints
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── strategies/     # Trading strategies
│   └── main.py         # Entry point
├── bot/                # Telegram bot
│   └── main.py         # Bot handlers
├── migrations/         # Database schema
├── backtest/           # TradingView scripts
├── docker-compose.yml  # Docker setup
└── .env                # Your secrets
```

---

## 🎯 Phase 0 Timeline

```
Day 1-3:  Setup + Testing
Day 4-17: Paper Trading (2 weeks)
Day 18:   Results Analysis

Daily commitment:
- Morning: 5 min (check positions)
- Evening: 10 min (check signals + execute)
```

---

## 🚨 Emergency Stops

```powershell
# Stop all trading immediately
docker-compose stop bot

# Close all open positions (via Telegram)
/update BTCUSDT

# Or via SQL (EMERGENCY ONLY!)
docker-compose exec postgres psql -U postgres -d trading_bot -c "UPDATE trades SET status='cancelled' WHERE status='open';"

# Then manually close in Paper Trading Engine
# (requires code modification - contact support)
```

---

## 📊 Success Metrics (End of Phase 0)

```
✅ PASS Criteria:
- Net Profit > $0
- Win Rate > 50%
- Profit Factor > 1.2
- Max Drawdown < 10%
- Min 10 trades

🎯 Excellent:
- Net Profit > $50 (10%)
- Win Rate > 60%
- Profit Factor > 1.5
- Max Drawdown < 5%
- Sharpe > 1.5
```

---

## 🔒 Security Checklist

```
✅ .env in .gitignore
✅ EXCHANGE_TESTNET=true
✅ API keys from Testnet only
✅ Withdrawals disabled on API keys
✅ Telegram bot token secret
✅ Different password for Testnet vs Live Binance
```

---

## 💡 Pro Tips

1. **Always check logs first**: `docker-compose logs -f`
2. **Test on weekends**: Market is less volatile
3. **Don't overtrade**: Max 1 position (Phase 0 limit)
4. **Keep a journal**: Note why each trade was taken
5. **Screenshot everything**: Evidence for post-analysis
6. **Backup .env**: Save it securely offline
7. **Monitor daily**: Don't skip monitoring days
8. **Read the README**: Full instructions there

---

**Keep calm and trade paper! 📈**
