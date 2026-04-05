import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import BOT_TOKEN
from Services.fetch_rates import get_current_rate
from Services.trend import get_trend
from database import init_db
from Services.rate_service import start_scheduler, stop_scheduler, set_alert_callback
from Services.alerts import save_user, send_alerts


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - save user, welcome message with current rate and trend"""
    chat_id = update.effective_chat.id
    
    # Save user to database
    save_user(chat_id)
    
    current_rate = get_current_rate()
    trend = get_trend()
    print(current_rate, trend)
    
    if current_rate:
        message = (
            f"🤖 Welcome to the Financial Bot!\n\n"
            f"💵 Current USD to UGX Rate: {current_rate:.2f}\n"
            f"📈 Trend: {trend}\n\n"
            f"✅ You will now receive forex alerts automatically."
        )
    else:
        message = (
            f"🤖 Welcome to the Financial Bot!\n\n"
            f"Unable to fetch current rate. Please try again later.\n\n"
            f"✅ You will now receive forex alerts automatically."
        )
    
    await update.message.reply_text(message)


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rate command - return latest USD to UGX rate"""
    current_rate = get_current_rate()
    print(current_rate)
    
    if current_rate:
        message = f"💵 Current USD to UGX Rate: {current_rate:.2f}"
    else:
        message = "❌ Unable to fetch the exchange rate. Please try again later."
    
    await update.message.reply_text(message)


async def trend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trend command - return current trend"""
    trend = get_trend()
    message = f"📈 Current Trend: {trend}"
    
    await update.message.reply_text(message)


def create_app():
    """Create and configure the Telegram bot application"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("rate", rate_command))
    app.add_handler(CommandHandler("trend", trend_command))
    
    # Start scheduler when app starts
    app.post_init = post_init
    
    return app


async def post_init(app: Application) -> None:
    """Initialize database and scheduler when app starts"""
    print("🚀 Initializing application...")
    init_db()
    print("✅ Database initialized")
    
    # Set alert callback before starting scheduler
    set_alert_callback(send_alerts)
    
    # Start scheduler with app context
    start_scheduler(app)


def main():
    """Main function to set up and run the bot"""
    app = create_app()
    
    # Start polling
    try:
        app.run_polling()
    finally:
        stop_scheduler()


if __name__ == "__main__":
    main()
