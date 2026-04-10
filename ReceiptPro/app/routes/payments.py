import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.payment import Payment
from app.models.user import User
import httpx

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/payments", tags=["payments"])

# Pydantic request/response models
class PaymentPhone(BaseModel):
    phone_number: str


class PaymentInitiate(BaseModel):
    phone_number: str
    amount: float
    currency: str = "UGX"
    pin: str | None = None
    pin_id: str | None = None


class CreatePaymentRequest(BaseModel):
    user_id: int
    amount: float


class CreatePaymentResponse(BaseModel):
    payment_url: str
    reference: str


class VerifyPaymentRequest(BaseModel):
    reference: str


class VerifyPaymentResponse(BaseModel):
    status: str


# Environment configuration
EVERSEND_BASE_URL = os.getenv("EVERSEND_BASE_URL")
EVERSEND_CLIENT_ID = os.getenv("CLIENT_ID")
EVERSEND_CLIENT_SECRET = os.getenv("CLIENT_SECRET")


# Internal helper: get access token from Eversend API
async def get_access_token():
    """
    Retrieve access token from Eversend API using client credentials.
    Required for all subsequent API calls.
    """
    client_id = EVERSEND_CLIENT_ID
    client_secret = EVERSEND_CLIENT_SECRET
    print(client_id, client_secret)
    
    if not client_id or not client_secret:
        logger.error("Missing Eversend credentials: CLIENT_ID or CLIENT_SECRET")
        raise HTTPException(status_code=500, detail="Missing credentials")
    
    if not EVERSEND_BASE_URL:
        logger.error("EVERSEND_BASE_URL not configured")
        raise HTTPException(status_code=500, detail="EVERSEND_BASE_URL not configured")

    try:
        async with httpx.AsyncClient() as client:
            # Eversend's auth endpoint expects a GET with query params
            response = await client.get(
                f"{EVERSEND_BASE_URL.rstrip('/')}/auth/token",
                headers={
                    "clientId": client_id,
                    "clientSecret": client_secret
                },
                timeout=30.0,
            )

        if response.status_code not in (200, 201):
            try:
                err = response.json()
            except Exception:
                err = response.text
            logger.error("Eversend token request failed: status=%s body=%s", response.status_code, err)
            raise HTTPException(status_code=response.status_code, detail=err)

        data = response.json()
        # prefer common keys
        token = data.get("access_token") or data.get("token")
        
        if not token:
            logger.error("Eversend response missing access_token: %s", data)
            raise HTTPException(status_code=500, detail="failed to obtain access token")
        
        return token
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting access token: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

# Public route: send PIN to phone number
@router.post("/send-pin")
async def send_pin(phone: PaymentPhone):
    """
    Send OTP PIN to a phone number via Eversend API.
    Returns pin_id needed for payment initiation.
    """
    token = await get_access_token()
    phone_number = phone.phone_number
    
    if not phone_number:
        raise HTTPException(status_code=400, detail="Phone number required")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVERSEND_BASE_URL.rstrip('/')}/collections/otp",
                headers={"Authorization": f"Bearer {token}"},
                json={"phone": phone_number},
                timeout=30.0,
            )
            
            if response.status_code != 200:
                try:
                    err = response.json()
                except Exception:
                    err = response.text
                logger.error("Eversend OTP request failed: status=%s body=%s", response.status_code, err)
                raise HTTPException(status_code=response.status_code, detail=err)
            
            return response.json()
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error sending PIN: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
# Public route: initiate payment
@router.post("/pay")
async def initiate_payment(payment: PaymentInitiate):
    """
    Initiate a payment using Eversend API.
    Requires PIN and PIN ID from /send-pin endpoint.
    """
    token = await get_access_token()
    pin = payment.pin
    pin_id = payment.pin_id
    amount = payment.amount
    phone = payment.phone_number
    currency = payment.currency

    if not pin or not pin_id:
        raise HTTPException(
            status_code=400,
            detail="pin and pin_id are required; call /send-pin first to get pinId"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVERSEND_BASE_URL.rstrip('/')}/collections/momo",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "phone": phone,
                    "amount": amount,
                    "country": "UG",
                    "currency": currency,
                    "otp": {"pinId": pin_id, "pin": pin},
                },
                timeout=30.0,
            )
    except Exception as exc:
        logger.exception("Eversend momo request exception: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    if response.status_code not in (200, 201):
        try:
            err = response.json()
        except Exception:
            err = response.text
        logger.error("Eversend momo request failed: status=%s body=%s", response.status_code, err)
        raise HTTPException(status_code=response.status_code, detail=err)

    try:
        return response.json()
    except Exception:
        # Return raw text if JSON parsing fails
        return {"data": response.text}


# Backwards-compatible endpoints used by the frontend
@router.post("/initiate")
async def initiate_compat(payment: PaymentInitiate, db: Session = Depends(get_db)):
    """
    Initiate a payment for the current user.
    Returns payment details including transaction ID.
    """
    try:
        token = await get_access_token()
        
        # Call the payment initiation endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EVERSEND_BASE_URL.rstrip('/')}/collections/momo",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "phone": payment.phone_number,
                    "amount": payment.amount,
                    "country": "UG",
                    "currency": payment.currency,
                    "otp": {"pinId": payment.pin_id, "pin": payment.pin},
                },
                timeout=30.0,
            )
        
        if response.status_code not in (200, 201):
            try:
                err = response.json()
            except Exception:
                err = response.text
            logger.error("Payment initiation failed: status=%s body=%s", response.status_code, err)
            raise HTTPException(status_code=response.status_code, detail=err)
        
        result = response.json()
        return {"status": "success", "transaction_id": result.get("transaction_id"), "message": "Payment initiated"}
    
    except Exception as exc:
        logger.exception("Payment initiation error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/me")
async def my_payment(db: Session = Depends(get_db)):
    """
    Get the latest payment for the current session.
    Returns payment details if available.
    """
    try:
        # Query the most recent payment
        payment = db.query(Payment).order_by(Payment.id.desc()).first()
        
        if not payment:
            return {"status": "not_found", "message": "No payments found"}
        
        return {
            "id": payment.id,
            "user_id": payment.user_id,
            "status": payment.status,
            "amount": payment.amount,
            "reference": payment.reference,
            "created_at": payment.created_at.isoformat() if payment.created_at else None
        }
    except Exception as exc:
        logger.exception("Error fetching payment: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{payment_id}")
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """
    Get a specific payment by ID.
    Returns payment details including status and reference.
    """
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "id": payment.id,
            "user_id": payment.user_id,
            "status": payment.status,
            "amount": payment.amount,
            "reference": payment.reference,
            "created_at": payment.created_at.isoformat() if payment.created_at else None
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error fetching payment: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
