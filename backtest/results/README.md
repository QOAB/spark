# Backtest Results

Сохраняйте сюда результаты backtest:

1. `equity_curve_6m.png` - screenshot equity curve из TradingView
2. `trade_list_6m.csv` - экспортированный список сделок
3. `metrics_summary.txt` - текстовый файл с ключевыми метриками

---

## Формат metrics_summary.txt:

```
BACKTEST RESULTS - Swing Trend Strategy
Period: May 15 - Nov 15, 2024
Symbol: BINANCE:BTCUSDT
Timeframe: 1H

============================================
Net Profit: $________
Net Profit %: _______%
Total Trades: ________
Win Rate: _______%
Profit Factor: ________
Max Drawdown: $________ (______%)
Sharpe Ratio: ________
Avg Win: $________
Avg Loss: $________
Largest Win: $________
Largest Loss: $________
Avg Trade Duration: ________ hours
============================================

PASS/FAIL CRITERIA:
[ ] Net Profit > $0
[ ] Win Rate > 50%
[ ] Profit Factor > 1.2
[ ] Max Drawdown < 10%
[ ] Total Trades >= 10

DECISION: [ ] GO / [ ] NO-GO for Phase 0
```

---

**Эта папка в .gitignore - результаты не будут закоммичены в Git.**
