import requests
from sqlalchemy.orm import Session
from models import ExchangeRate
from database import SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


# Global variables for scheduler callback
_scheduler_context = None
_alert_callback = None


def fetch_and_store_rate(db: Session = None) -> bool:
    """
    Fetch USD to UGX exchange rate from exchangerate.host API and store in database.
    
    Args:
        db: Database session. If None, creates a new session.
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _scheduler_context, _alert_callback
    
    # Create a new session if not provided
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        response = requests.get(
            "https://api.exchangerate.host/live?access_key=c332a62fa57d478f3e85efab6137d5f4&symbols=USD,UGX"
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("success", True):
            rate = data.get("quotes", {}).get("USDUGX")
            if rate:
                exchange_rate = ExchangeRate(
                    rate=float(rate),
                    timestamp=datetime.utcnow()
                )
                db.add(exchange_rate)
                db.commit()
                db.refresh(exchange_rate)
                print(f"✅ Successfully stored exchange rate: {rate} at {datetime.utcnow()}")
                
                # Call alert callback if available
                if _scheduler_context and _alert_callback:
                    try:
                        import asyncio
                        # Run async callback
                        asyncio.create_task(_alert_callback(_scheduler_context))
                    except Exception as e:
                        print(f"⚠️ Error calling alert callback: {e}")
                
                return True
        
        print("❌ API returned invalid data")
        return False
        
    except requests.RequestException as e:
        print(f"❌ Error fetching exchange rate: {e}")
        return False
    except Exception as e:
        print(f"❌ Error storing exchange rate: {e}")
        db.rollback()
        return False
    finally:
        if close_db:
            db.close()


def get_latest_rate(db: Session) -> ExchangeRate | None:
    """
    Get the most recent exchange rate from the database.
    
    Args:
        db: Database session
        
    Returns:
        ExchangeRate: The latest exchange rate record, or None if not found
    """
    try:
        latest = db.query(ExchangeRate).order_by(ExchangeRate.timestamp.desc()).first()
        return latest
    except Exception as e:
        print(f"❌ Error fetching latest rate: {e}")
        return None


def get_previous_rate(db: Session, limit: int = 2) -> ExchangeRate | None:
    """
    Get the previous exchange rate from the database (second most recent).
    
    Args:
        db: Database session
        limit: Number of records to fetch
        
    Returns:
        ExchangeRate: The previous exchange rate record, or None if not found
    """
    try:
        rates = db.query(ExchangeRate).order_by(ExchangeRate.timestamp.desc()).limit(limit).all()
        if len(rates) >= 2:
            return rates[1]
        return None
    except Exception as e:
        print(f"❌ Error fetching previous rate: {e}")
        return None


# Global scheduler instance
scheduler = None


def start_scheduler(app=None):
    """
    Start the APScheduler to fetch rates every 2 hours.
    
    Args:
        app: Telegram application for alert callbacks (optional)
    """
    global scheduler, _scheduler_context
    
    if scheduler is None:
        _scheduler_context = app
        
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            fetch_and_store_rate,
            'interval',
            hours=2,
            id='fetch_rate_job',
            name='Fetch and store exchange rate every 2 hours'
        )
        scheduler.start()
        print("✅ Scheduler started - fetching rates every 2 hours")
        
        # Fetch rate immediately on startup
        fetch_and_store_rate()


def set_alert_callback(callback):
    """
    Set the callback function to be called after each rate fetch.
    
    Args:
        callback: Async function to call with context
    """
    global _alert_callback
    _alert_callback = callback


def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        scheduler = None
        print("✅ Scheduler stopped")
        print("✅ Scheduler stopped")
