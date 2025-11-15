"""
Telegram bot main entry point.
Handles user commands and communicates with backend API.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import httpx
from datetime import datetime

from config import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Backend API base URL
API_BASE = f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/api/v1"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = (
        "🤖 *Swing Trend Trading Bot*\n\n"
        "Привет! Я бот для paper trading на основе Swing Trend стратегии.\n\n"
        "*Доступные команды:*\n"
        "/status - Показать состояние портфеля\n"
        "/signals <SYMBOL> - Проверить сигнал (пример: /signals BTCUSDT)\n"
        "/execute <SYMBOL> - Открыть позицию по сигналу\n"
        "/positions - Показать открытые позиции\n"
        "/update <SYMBOL> - Обновить позиции (проверить SL/TP)\n"
        "/history - Показать историю сделок\n"
        "/help - Показать помощь\n\n"
        "⚠️ *ВНИМАНИЕ:* Это paper trading (тестовый режим)!\n"
        "Реальные деньги не используются."
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "*📖 Справка по командам:*\n\n"
        "*1️⃣ /status*\n"
        "Показывает:\n"
        "• Текущий капитал (equity)\n"
        "• Количество открытых позиций\n"
        "• P&L за сегодня\n"
        "• Win rate за последние 30 дней\n\n"
        "*2️⃣ /signals BTCUSDT*\n"
        "Проверяет наличие торгового сигнала:\n"
        "• Long/Short направление\n"
        "• Entry price (цена входа)\n"
        "• Stop Loss и Take Profit уровни\n\n"
        "*3️⃣ /execute BTCUSDT*\n"
        "Открывает позицию по текущему сигналу:\n"
        "• Рассчитывает размер позиции (2% риск)\n"
        "• Открывает в paper engine\n"
        "• Сохраняет в базу данных\n\n"
        "*4️⃣ /positions*\n"
        "Показывает все открытые позиции с текущим P&L\n\n"
        "*5️⃣ /update BTCUSDT*\n"
        "Обновляет позиции (проверяет SL/TP hits)\n\n"
        "*6️⃣ /history*\n"
        "Показывает последние 20 закрытых сделок\n\n"
        "*⚙️ Параметры стратегии:*\n"
        f"• Timeframe: {settings.TIMEFRAME}\n"
        f"• Risk per trade: {settings.RISK_PER_TRADE}%\n"
        f"• Max open positions: {settings.MAX_OPEN_POSITIONS}\n"
        f"• Risk/Reward ratio: {settings.RR_RATIO}\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show portfolio status."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/status", timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        # Format message
        message = (
            "📊 *Статус портфеля*\n\n"
            f"💰 Equity: ${data['equity']:.2f}\n"
            f"💵 Available: ${data['available']:.2f}\n"
            f"📈 Open positions: {data['open_positions']}\n"
            f"💸 Today's P&L: ${data['today_pnl']:.2f}\n"
            f"🎯 Win rate (30d): {data['win_rate_30d']:.1f}%\n"
            f"📊 Total trades (30d): {data['total_trades_30d']}\n\n"
        )
        
        # Add open positions details
        if data['open_positions'] > 0:
            message += "*Открытые позиции:*\n"
            for pos in data['positions']:
                pnl_emoji = "🟢" if pos['pnl'] > 0 else "🔴"
                message += (
                    f"\n{pnl_emoji} *{pos['symbol']}* {pos['side'].upper()}\n"
                    f"  Entry: ${pos['entry_price']:.2f}\n"
                    f"  Current: ${pos['current_price']:.2f}\n"
                    f"  P&L: ${pos['pnl']:.2f} ({pos['pnl_pct']:.2f}%)\n"
                    f"  SL: ${pos['stop_loss']:.2f} | TP: ${pos['take_profit']:.2f}\n"
                )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in status_command: {e}")
        await update.message.reply_text(
            "❌ Ошибка при получении статуса. Проверьте, что backend работает."
        )
    except Exception as e:
        logger.error(f"Error in status_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals <SYMBOL> command - check for trading signals."""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Укажите символ! Пример: /signals BTCUSDT"
        )
        return
    
    symbol = context.args[0].upper()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/signals/{symbol}", timeout=15.0)
            response.raise_for_status()
            data = response.json()
        
        if data['signal'] is None:
            message = (
                f"🔍 *{symbol}*\n\n"
                "⏳ Нет сигнала в данный момент.\n"
                "Попробуйте позже."
            )
        else:
            side_emoji = "🟢" if data['signal'] == 'long' else "🔴"
            message = (
                f"{side_emoji} *СИГНАЛ: {data['signal'].upper()}*\n\n"
                f"📊 Symbol: {symbol}\n"
                f"💰 Entry: ${data['entry_price']:.2f}\n"
                f"🛑 Stop Loss: ${data['stop_loss']:.2f}\n"
                f"🎯 Take Profit: ${data['take_profit']:.2f}\n"
                f"⚖️ Risk/Reward: 1:{data['risk_reward']}\n\n"
                f"Для открытия позиции используйте:\n"
                f"/execute {symbol}"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in signals_command: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении сигнала для {symbol}"
        )
    except Exception as e:
        logger.error(f"Error in signals_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def execute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /execute <SYMBOL> command - execute trade."""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Укажите символ! Пример: /execute BTCUSDT"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Send "processing" message
    processing_msg = await update.message.reply_text(
        f"⏳ Открываю позицию по {symbol}..."
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE}/execute/{symbol}", timeout=15.0)
            response.raise_for_status()
            data = response.json()
        
        # Format success message
        side_emoji = "🟢" if data['side'] == 'long' else "🔴"
        message = (
            f"{side_emoji} *ПОЗИЦИЯ ОТКРЫТА*\n\n"
            f"📊 Symbol: {data['symbol']}\n"
            f"📍 Side: {data['side'].upper()}\n"
            f"💰 Entry: ${data['entry_price']:.2f}\n"
            f"📦 Quantity: {data['quantity']:.4f}\n"
            f"🛑 Stop Loss: ${data['stop_loss']:.2f}\n"
            f"🎯 Take Profit: ${data['take_profit']:.2f}\n"
            f"💸 Risk amount: ${data['risk_amount']:.2f}\n\n"
            f"✅ Trade ID: {data['trade_id']}\n"
            f"🕐 {datetime.fromisoformat(data['timestamp']).strftime('%H:%M:%S')}"
        )
        
        await processing_msg.edit_text(message, parse_mode='Markdown')
        
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get('detail', 'Unknown error')
        await processing_msg.edit_text(f"❌ Ошибка: {error_detail}")
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in execute_command: {e}")
        await processing_msg.edit_text(
            f"❌ Ошибка при открытии позиции для {symbol}"
        )
    except Exception as e:
        logger.error(f"Error in execute_command: {e}")
        await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")


async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /positions command - show open positions."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/positions", timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        if data['open_positions'] == 0:
            message = "📭 Нет открытых позиций"
        else:
            message = f"📊 *Открытые позиции: {data['open_positions']}*\n\n"
            
            for pos in data['positions']:
                pnl_emoji = "🟢" if pos['pnl'] > 0 else "🔴"
                side_emoji = "🟢" if pos['side'] == 'long' else "🔴"
                message += (
                    f"{side_emoji} *{pos['symbol']}* {pos['side'].upper()}\n"
                    f"💰 Entry: ${pos['entry_price']:.2f}\n"
                    f"📍 Current: ${pos['current_price']:.2f}\n"
                    f"{pnl_emoji} P&L: ${pos['pnl']:.2f} ({pos['pnl_pct']:.2f}%)\n"
                    f"🛑 SL: ${pos['stop_loss']:.2f}\n"
                    f"🎯 TP: ${pos['take_profit']:.2f}\n"
                    f"📦 Qty: {pos['qty']:.4f}\n\n"
                )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in positions_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении позиций")
    except Exception as e:
        logger.error(f"Error in positions_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /update <SYMBOL> command - update positions (check SL/TP)."""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Укажите символ! Пример: /update BTCUSDT"
        )
        return
    
    symbol = context.args[0].upper()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE}/update-positions/{symbol}", timeout=10.0)
            response.raise_for_status()
            data = response.json()
        
        message = (
            f"🔄 *Обновление позиций: {symbol}*\n\n"
            f"💰 Current price: ${data['current_price']:.2f}\n"
            f"🔒 Closed positions: {data['closed_positions']}\n\n"
        )
        
        if data['closed_positions'] > 0:
            message += "*Закрытые позиции:*\n"
            for pos in data['details']:
                pnl_emoji = "🟢" if pos['pnl'] > 0 else "🔴"
                message += (
                    f"\n{pnl_emoji} {pos['side'].upper()}\n"
                    f"  Entry: ${pos['entry_price']:.2f}\n"
                    f"  Exit: ${pos['exit_price']:.2f}\n"
                    f"  P&L: ${pos['pnl']:.2f} ({pos['pnl_pct']:.2f}%)\n"
                    f"  Reason: {pos['exit_reason']}\n"
                )
        else:
            message += "✅ Все позиции остаются открытыми (SL/TP не достигнуты)"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in update_command: {e}")
        await update.message.reply_text(f"❌ Ошибка при обновлении {symbol}")
    except Exception as e:
        logger.error(f"Error in update_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command - show trade history."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/trades/history?limit=20&status=closed",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
        
        if data['total'] == 0:
            message = "📭 История сделок пуста"
        else:
            message = f"📜 *История сделок (последние {data['total']})*\n\n"
            
            for trade in data['trades'][:10]:  # Show only last 10
                pnl_emoji = "🟢" if trade['pnl'] > 0 else "🔴"
                side_emoji = "🟢" if trade['side'] == 'long' else "🔴"
                
                closed_at = datetime.fromisoformat(trade['closed_at'])
                message += (
                    f"{side_emoji} *{trade['symbol']}* {trade['side'].upper()}\n"
                    f"{pnl_emoji} P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)\n"
                    f"📅 {closed_at.strftime('%d.%m %H:%M')}\n"
                    f"Exit: {trade['exit_reason']}\n\n"
                )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in history_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении истории")
    except Exception as e:
        logger.error(f"Error in history_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("signals", signals_command))
    application.add_handler(CommandHandler("execute", execute_command))
    application.add_handler(CommandHandler("positions", positions_command))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("history", history_command))
    
    # Start bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
