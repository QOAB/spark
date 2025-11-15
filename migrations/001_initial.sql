-- Initial database schema for trading bot
-- Creates tables for trades and sets up TimescaleDB hypertable for OHLCV data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Trades table (trade history)
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    entry_price NUMERIC(20, 8) NOT NULL,
    exit_price NUMERIC(20, 8),
    qty NUMERIC(20, 8) NOT NULL,
    stop_loss NUMERIC(20, 8) NOT NULL,
    take_profit NUMERIC(20, 8) NOT NULL,
    pnl NUMERIC(20, 8),
    pnl_pct NUMERIC(10, 4),
    exit_reason VARCHAR(50),
    opened_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),
    notes TEXT
);

-- Create indexes for common queries
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_opened_at ON trades(opened_at DESC);
CREATE INDEX idx_trades_closed_at ON trades(closed_at DESC);

-- OHLCV data table (market data)
CREATE TABLE IF NOT EXISTS ohlcv (
    time TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open NUMERIC(20, 8) NOT NULL,
    high NUMERIC(20, 8) NOT NULL,
    low NUMERIC(20, 8) NOT NULL,
    close NUMERIC(20, 8) NOT NULL,
    volume NUMERIC(20, 8) NOT NULL,
    PRIMARY KEY (time, symbol, timeframe)
);

-- Convert ohlcv to TimescaleDB hypertable for efficient time-series queries
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

-- Create indexes for OHLCV queries
CREATE INDEX idx_ohlcv_symbol_timeframe ON ohlcv(symbol, timeframe, time DESC);

-- Portfolio state table (for paper trading engine)
CREATE TABLE IF NOT EXISTS portfolio_state (
    id SERIAL PRIMARY KEY,
    equity NUMERIC(20, 8) NOT NULL,
    available NUMERIC(20, 8) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index for portfolio queries
CREATE INDEX idx_portfolio_timestamp ON portfolio_state(timestamp DESC);

-- Insert initial portfolio state ($500 starting capital)
INSERT INTO portfolio_state (equity, available) VALUES (500.0, 500.0);

-- View for daily statistics
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(closed_at) as date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(CAST(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS NUMERIC) / COUNT(*) * 100, 2) as win_rate,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl,
    ROUND(MAX(pnl), 2) as max_win,
    ROUND(MIN(pnl), 2) as max_loss
FROM trades
WHERE status = 'closed' AND closed_at IS NOT NULL
GROUP BY DATE(closed_at)
ORDER BY date DESC;

-- View for symbol performance
CREATE OR REPLACE VIEW symbol_performance AS
SELECT 
    symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    ROUND(CAST(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) AS NUMERIC) / COUNT(*) * 100, 2) as win_rate,
    ROUND(SUM(pnl), 2) as total_pnl,
    ROUND(AVG(pnl), 2) as avg_pnl
FROM trades
WHERE status = 'closed'
GROUP BY symbol
ORDER BY total_pnl DESC;

-- Grant permissions (adjust username as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
