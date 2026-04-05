from database import SessionLocal
from Services.rate_service import get_latest_rate


def get_current_rate():
    """
    Get the latest USD to UGX exchange rate from the database.
    
    Returns:
        float: The current UGX rate (how many UGX = 1 USD), or None if no rate is available
    """
    db = SessionLocal()
    try:
        latest = get_latest_rate(db)
        if latest:
            return latest.rate
        return None
    finally:
        db.close()
