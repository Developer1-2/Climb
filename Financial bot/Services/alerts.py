from sqlalchemy.orm import Session
from models import User, ExchangeRate
from database import SessionLocal
from telegram.ext import Application
import logging

logger = logging.getLogger(__name__)


def save_user(chat_id: int, db: Session = None) -> User | None:
    """
    Save a user's chat_id to the database if not already exists.
    
    Args:
        chat_id: Telegram user's chat ID
        db: Database session. If None, creates a new session.
        
    Returns:
        User: The user record, or None if error occurred
    """
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.chat_id == chat_id).first()
        if existing_user:
            return existing_user
        
        # Create new user
        new_user = User(chat_id=chat_id)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"✅ User {chat_id} saved successfully")
        return new_user
        
    except Exception as e:
        print(f"❌ Error saving user {chat_id}: {e}")
        db.rollback()
        return None
    finally:
        if close_db:
            db.close()


def get_all_users(db: Session) -> list[User]:
    """
    Get all users from the database.
    
    Args:
        db: Database session
        
    Returns:
        list[User]: List of all user records
    """
    try:
        users = db.query(User).all()
        return users
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
        return []


def get_rate_difference(db: Session) -> dict | None:
    """
    Get the difference between latest and previous exchange rate.
    
    Args:
        db: Database session
        
    Returns:
        dict: Dictionary with 'latest', 'previous', 'difference', and 'trend', or None if error
    """
    try:
        # Get latest two rates
        rates = db.query(ExchangeRate).order_by(ExchangeRate.timestamp.desc()).limit(2).all()
        
        if len(rates) < 1:
            return None
        
        latest = rates[0]
        
        # If only one rate exists, no previous rate
        if len(rates) < 2:
            return {
                'latest': latest.rate,
                'previous': None,
                'difference': 0,
                'trend': 'Stable'
            }
        
        previous = rates[1]
        difference = latest.rate - previous.rate
        
        # Determine trend
        if difference > 50:
            trend = 'Rising'
        elif difference < -50:
            trend = 'Falling'
        else:
            trend = 'Stable'
        
        return {
            'latest': latest.rate,
            'previous': previous.rate,
            'difference': difference,
            'trend': trend
        }
        
    except Exception as e:
        print(f"❌ Error calculating rate difference: {e}")
        return None


def format_alert_message(rate_info: dict) -> str | None:
    """
    Format the alert message for users.
    
    Args:
        rate_info: Dictionary with rate information
        
    Returns:
        str: Formatted alert message, or None if no alert needed
    """
    if not rate_info or rate_info['difference'] == 0:
        return None
    
    # Only send alerts if difference is significant (> 50 or < -50)
    if abs(rate_info['difference']) <= 50:
        return None
    
    latest = rate_info['latest']
    difference = rate_info['difference']
    trend = rate_info['trend']
    
    # Create suggestion based on trend
    if trend == 'Rising':
        suggestion = "💡 Consider exchanging soon before rates go higher."
    elif trend == 'Falling':
        suggestion = "💡 Better rates might be coming. You may want to wait a bit."
    else:
        suggestion = "💡 Rates are stable. No urgent action needed."
    
    message = (
        f"🚨 Forex Alert!\n\n"
        f"USD is now {latest:.0f} ({difference:+.0f} UGX)\n"
        f"📈 Trend: {trend}\n\n"
        f"{suggestion}"
    )
    
    return message


async def send_alerts(context):
    """
    Send alerts to all subscribed users about significant rate changes.
    
    Args:
        context: Telegram bot context with bot instance
    """
    db = SessionLocal()
    
    try:
        # Get rate difference
        rate_info = get_rate_difference(db)
        if not rate_info:
            return
        
        # Only send if significant change (difference > 50 or < -50)
        if abs(rate_info['difference']) <= 50:
            return
        
        # Format alert message
        message = format_alert_message(rate_info)
        if not message:
            return
        
        # Get all users
        users = get_all_users(db)
        if not users:
            print("⚠️ No users to alert")
            return
        
        # Send message to each user
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.chat_id,
                    text=message
                )
                sent_count += 1
                print(f"✅ Alert sent to user {user.chat_id}")
            except Exception as e:
                failed_count += 1
                # Log error but continue sending to other users
                if "bot was blocked by the user" in str(e):
                    print(f"⚠️ User {user.chat_id} blocked the bot")
                else:
                    print(f"❌ Error sending alert to user {user.chat_id}: {e}")
        
        if sent_count > 0:
            print(f"📊 Alerts sent to {sent_count} users ({failed_count} failed)")
        
    except Exception as e:
        print(f"❌ Error in send_alerts: {e}")
    finally:
        db.close()
