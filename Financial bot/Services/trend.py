from database import SessionLocal
from Services.rate_service import get_latest_rate, get_previous_rate


def get_trend():
    """
    Determine the trend of USD to UGX exchange rate by comparing latest with previous rate.
    
    Returns:
        str: "Rising" if increase > 30, "Falling" if decrease > 30, "Stable" otherwise
    """
    db = SessionLocal()
    try:
        latest = get_latest_rate(db)
        
        if latest is None:
            return "Unable to determine trend"
        
        # Get the previous rate for comparison
        previous = get_previous_rate(db)
        
        # If we don't have a previous rate, return stable
        if previous is None:
            return "Stable"
        
        # Calculate the difference
        difference = latest.rate - previous.rate
        
        # Determine the trend based on the difference
        if difference > 30:
            return "Rising"
        elif difference < -30:
            return "Falling"
        else:
            return "Stable"
    finally:
        db.close()
