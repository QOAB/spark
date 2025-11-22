"""
FastAPI routes for trading bot API.
Provides REST endpoints for Telegram bot to interact with paper trading engine.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models.trade import Trade
from ..services.market_data import MarketDataService
from ..services.paper_trading import PaperTradingEngine
from ..strategies.swing_trend import SwingTrendStrategy
from ..config import settings

router = APIRouter(prefix="/api/v1", tags=["trading"])

# Global instances
market_data = MarketDataService()
paper_engine = PaperTradingEngine(initial_capital=settings.INITIAL_CAPITAL)
strategy = SwingTrendStrategy()


@router.get("/status")
async def get_status(db: AsyncSession = Depends(get_db)):
    """
    Get current trading status:
    - Portfolio equity
    - Open positions
    - Today's P&L
    - Win rate (last 30 days)
    """
    try:
        # Get portfolio status from paper engine
        portfolio = paper_engine.get_status()
        
        # Query recent trades (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        result = await db.execute(
            select(Trade)
            .where(Trade.status == "closed")
            .where(Trade.closed_at >= thirty_days_ago)
            .order_by(desc(Trade.closed_at))
        )
        recent_trades = result.scalars().all()
        
        # Calculate win rate
        if recent_trades:
            winning_trades = [t for t in recent_trades if t.pnl > 0]
            win_rate = (len(winning_trades) / len(recent_trades)) * 100
        else:
            win_rate = 0.0
        
        # Today's P&L
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(Trade)
            .where(Trade.status == "closed")
            .where(Trade.closed_at >= today_start)
        )
        today_trades = result.scalars().all()
        today_pnl = sum(t.pnl for t in today_trades)
        
        return {
            "equity": portfolio["equity"],
            "available": portfolio["available"],
            "open_positions": len(portfolio["positions"]),
            "positions": portfolio["positions"],
            "today_pnl": round(today_pnl, 2),
            "win_rate_30d": round(win_rate, 2),
            "total_trades_30d": len(recent_trades),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching status: {str(e)}")


@router.get("/signals/{symbol}")
async def get_signal(symbol: str):
    """
    Check if there's a trading signal for given symbol.
    Returns entry price, stop loss, take profit if signal exists.
    """
    try:
        # Fetch recent OHLCV data (last 100 bars)
        df = await market_data.fetch_ohlcv(
            symbol=symbol,
            timeframe=settings.TIMEFRAME,
            limit=100
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        
        # Generate signal
        signal = strategy.generate_signal(df)
        
        if signal is None:
            return {
                "symbol": symbol,
                "signal": None,
                "message": "No signal at this time",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "symbol": symbol,
            "signal": signal["side"],
            "entry_price": signal["entry"],
            "stop_loss": signal["stop"],
            "take_profit": signal["tp"],
            "risk_reward": settings.RR_RATIO,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")


@router.post("/execute/{symbol}")
async def execute_trade(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Execute trade for given symbol:
    1. Check for signal
    2. Calculate position size
    3. Open position in paper engine
    4. Save to database
    """
    try:
        # Check if max positions reached
        status = paper_engine.get_status()
        if len(status["positions"]) >= settings.MAX_OPEN_POSITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Max positions ({settings.MAX_OPEN_POSITIONS}) already open"
            )
        
        # Fetch data and check signal
        df = await market_data.fetch_ohlcv(
            symbol=symbol,
            timeframe=settings.TIMEFRAME,
            limit=100
        )
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        
        signal = strategy.generate_signal(df)
        
        if signal is None:
            raise HTTPException(
                status_code=400,
                detail="No valid signal at this time"
            )
        
        # Calculate position size
        qty = paper_engine.calculate_position_size(
            entry_price=signal["entry"],
            stop_price=signal["stop"]
        )
        
        # Open position in paper engine
        position = paper_engine.open_position(
            symbol=symbol,
            side=signal["side"],
            entry_price=signal["entry"],
            qty=qty,
            stop_loss=signal["stop"],
            take_profit=signal["tp"]
        )
        
        # Save to database
        trade = Trade(
            strategy="swing_trend",
            symbol=symbol,
            side=signal["side"],
            entry_price=signal["entry"],
            qty=qty,
            stop_loss=signal["stop"],
            take_profit=signal["tp"],
            opened_at=datetime.utcnow(),
            status="open"
        )
        db.add(trade)
        await db.commit()
        await db.refresh(trade)
        
        return {
            "trade_id": trade.id,
            "symbol": symbol,
            "side": signal["side"],
            "entry_price": signal["entry"],
            "quantity": qty,
            "stop_loss": signal["stop"],
            "take_profit": signal["tp"],
            "risk_amount": round(paper_engine.equity * (settings.RISK_PER_TRADE / 100), 2),
            "message": "Position opened successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error executing trade: {str(e)}")


@router.get("/positions")
async def get_positions():
    """
    Get all open positions with current P&L.
    """
    try:
        status = paper_engine.get_status()
        return {
            "open_positions": len(status["positions"]),
            "positions": status["positions"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching positions: {str(e)}")


@router.post("/update-positions/{symbol}")
async def update_positions(symbol: str, db: AsyncSession = Depends(get_db)):
    """
    Update positions for given symbol:
    1. Fetch current price
    2. Check SL/TP hits
    3. Close positions if needed
    4. Update database
    """
    try:
        # Fetch current ticker
        ticker = await market_data.get_ticker(symbol)
        current_price = ticker["last"]
        
        # Update positions in paper engine
        closed_positions = paper_engine.update_positions(symbol, current_price)
        
        # Update database for closed positions
        for pos in closed_positions:
            result = await db.execute(
                select(Trade)
                .where(Trade.symbol == symbol)
                .where(Trade.status == "open")
                .where(Trade.entry_price == pos["entry_price"])
            )
            trade = result.scalar_one_or_none()
            
            if trade:
                trade.exit_price = pos["exit_price"]
                trade.pnl = pos["pnl"]
                trade.pnl_pct = pos["pnl_pct"]
                trade.exit_reason = pos["exit_reason"]
                trade.closed_at = datetime.utcnow()
                trade.status = "closed"
        
        await db.commit()
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "closed_positions": len(closed_positions),
            "details": closed_positions,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating positions: {str(e)}")


@router.get("/trades/history")
async def get_trade_history(
    limit: int = 50,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get trade history with optional filtering.
    """
    try:
        query = select(Trade).order_by(desc(Trade.opened_at))
        
        if status:
            query = query.where(Trade.status == status)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        trades = result.scalars().all()
        
        return {
            "total": len(trades),
            "trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "qty": t.qty,
                    "pnl": t.pnl,
                    "pnl_pct": t.pnl_pct,
                    "exit_reason": t.exit_reason,
                    "opened_at": t.opened_at.isoformat() if t.opened_at else None,
                    "closed_at": t.closed_at.isoformat() if t.closed_at else None,
                    "status": t.status
                }
                for t in trades
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "trading-bot-api",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/system-info")
async def get_system_info(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive system information endpoint.
    Returns complete inventory of what the system has:
    - System configuration and parameters
    - Strategy settings and indicators
    - Portfolio state and performance
    - Database statistics
    - Exchange connection info
    - Available features
    """
    try:
        # Portfolio status
        portfolio = paper_engine.get_status()
        
        # Database statistics - limit to last 1000 trades for performance
        result = await db.execute(
            select(Trade)
            .order_by(desc(Trade.opened_at))
            .limit(1000)
        )
        all_trades = result.scalars().all()
        
        closed_trades = [t for t in all_trades if t.status == "closed"]
        open_trades = [t for t in all_trades if t.status == "open"]
        
        # Calculate statistics
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl is not None)
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        
        # Average win/loss
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Exchange status - handle specific exceptions
        try:
            ticker = await market_data.get_ticker("BTCUSDT")
            exchange_status = "connected"
            exchange_last_price = ticker.get("last", 0)
        except (ConnectionError, TimeoutError) as e:
            exchange_status = "disconnected"
            exchange_last_price = 0
        except Exception as e:
            # Log unexpected errors but don't fail the endpoint
            exchange_status = "error"
            exchange_last_price = 0
        
        return {
            "system": {
                "name": "Swing Trend Trading Bot",
                "version": "1.0.0",
                "phase": "Phase 0 - Paper Trading",
                "timestamp": datetime.utcnow().isoformat()
            },
            "configuration": {
                "initial_capital": settings.INITIAL_CAPITAL,
                "risk_per_trade": f"{settings.RISK_PER_TRADE}%",
                "max_open_positions": settings.MAX_OPEN_POSITIONS,
                "daily_loss_limit": f"{settings.DAILY_LOSS_LIMIT}%",
                "timeframe": settings.TIMEFRAME,
                "timezone": settings.TIMEZONE
            },
            "strategy": {
                "name": "Swing Trend Baseline",
                "indicators": {
                    "ema_fast": settings.EMA_FAST,
                    "ema_slow": settings.EMA_SLOW,
                    "rsi_length": settings.RSI_LENGTH,
                    "rsi_long_threshold": settings.RSI_LONG_THRESHOLD,
                    "rsi_short_threshold": settings.RSI_SHORT_THRESHOLD,
                    "atr_length": settings.ATR_LENGTH,
                    "breakout_lookback": settings.LOOKBACK
                },
                "risk_management": {
                    "stop_loss": "Entry ± 2*ATR",
                    "take_profit": f"Entry ± {settings.RR_RATIO}*(Entry-StopLoss)",
                    "risk_reward_ratio": settings.RR_RATIO
                }
            },
            "portfolio": {
                "equity": portfolio["equity"],
                "available_capital": portfolio["available"],
                "open_positions": len(portfolio["positions"]),
                "positions_detail": portfolio["positions"],
                "total_pnl": round(total_pnl, 2),
                "pnl_percentage": round((total_pnl / settings.INITIAL_CAPITAL) * 100, 2) if settings.INITIAL_CAPITAL > 0 else 0
            },
            "statistics": {
                "total_trades": len(all_trades),
                "closed_trades": len(closed_trades),
                "open_trades": len(open_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": round(win_rate, 2),
                "average_win": round(avg_win, 2),
                "average_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2)
            },
            "exchange": {
                "name": "Binance",
                "mode": "testnet" if settings.EXCHANGE_TESTNET else "live",
                "status": exchange_status,
                "btcusdt_price": exchange_last_price,
                "api_configured": bool(settings.EXCHANGE_API_KEY and settings.EXCHANGE_API_SECRET)
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
                "total_records": len(all_trades)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system info: {str(e)}")
