
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import razorpay
from app.core.config import settings
from app.core.security import get_current_user
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payment"])

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class OrderCreate(BaseModel):
    amount: int  # Amount in rupees
    currency: str = "INR"

@router.post("/create-order")
def create_order(order: OrderCreate, user=Depends(get_current_user)):
    try:
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            logger.error("Razorpay credentials missing")
            raise HTTPException(status_code=500, detail="Razorpay configuration error")
        order_data = {
            "amount": order.amount * 100,  # Convert to paise
            "currency": order.currency,
            "payment_capture": 1  # Auto-capture payment
        }
        razorpay_order = razorpay_client.order.create(data=order_data)
        logger.info(f"Razorpay order created for user {user.id}: order_id={razorpay_order['id']}")
        return {
            "order_id": razorpay_order["id"],
            "key": settings.RAZORPAY_KEY_ID,
            "amount": order.amount,
            "currency": order.currency
        }
    except Exception as e:
        logger.error(f"Error creating Razorpay order for user {user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")