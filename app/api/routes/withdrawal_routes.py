# app/api/routes/withdrawal_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.security import get_db, get_current_vendor
from app.schemas.withdrawal_schema import WithdrawalRequest, WithdrawalOut, WithdrawalStats
from app.crud import withdrawal_crud, payment_crud
from app.models.withdrawal_model import WithdrawalStatus
from app.utils.fcm import send_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/withdrawals", tags=["Withdrawals"])


@router.post("/request", response_model=WithdrawalOut, summary="Request Withdrawal")
def request_withdrawal(
    withdrawal_data: WithdrawalRequest,
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Vendor requests withdrawal of available balance"""
    try:
        vendor_id = vendor.id

        # Get vendor's payment analytics to calculate available balance
        analytics = payment_crud.get_payment_analytics(db, vendor_id=vendor_id)
        total_revenue = analytics['total_revenue']

        # Calculate net earnings after 10% commission
        commission = total_revenue * 0.10
        net_earnings = total_revenue - commission

        # Get total withdrawn and pending amounts
        completed_withdrawals = withdrawal_crud.get_completed_withdrawal_amount(db, vendor_id)
        pending_withdrawals = withdrawal_crud.get_pending_withdrawal_amount(db, vendor_id)

        # Calculate available balance
        available_balance = net_earnings - completed_withdrawals - pending_withdrawals

        logger.info(f"Vendor {vendor_id} withdrawal check - Available: ₹{available_balance}, Requested: ₹{withdrawal_data.amount}")

        # Validate withdrawal amount
        if withdrawal_data.amount > available_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient balance. Available: ₹{available_balance:.2f}, Requested: ₹{withdrawal_data.amount:.2f}"
            )

        if withdrawal_data.amount < 100:
            raise HTTPException(
                status_code=400,
                detail="Minimum withdrawal amount is ₹100"
            )

        # Create withdrawal request
        withdrawal = withdrawal_crud.create_withdrawal(db, vendor_id, withdrawal_data)

        # Send notification to vendor
        try:
            vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
            send_notification(
                recipient=vendor.email,
                notification_type="withdrawal_requested",
                message=f"Your withdrawal request of ₹{withdrawal_data.amount} has been submitted and is under review.",
                recipient_id=vendor_id,
                fcm_token=vendor_fcm_token
            )
        except Exception as e:
            logger.error(f"Failed to send withdrawal notification: {str(e)}")

        return withdrawal

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating withdrawal request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create withdrawal request: {str(e)}")


@router.get("/history", response_model=List[WithdrawalOut], summary="Get Withdrawal History")
def get_withdrawal_history(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor),
    status: Optional[WithdrawalStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Get vendor's withdrawal history"""
    try:
        withdrawals = withdrawal_crud.get_withdrawals_by_vendor_id(
            db, vendor.id, status=status, skip=skip, limit=limit
        )
        return withdrawals
    except Exception as e:
        logger.error(f"Error fetching withdrawal history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch withdrawal history")


@router.get("/stats", response_model=WithdrawalStats, summary="Get Withdrawal Statistics")
def get_withdrawal_stats(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Get vendor's withdrawal statistics"""
    try:
        stats = withdrawal_crud.get_vendor_withdrawal_stats(db, vendor.id)
        return stats
    except Exception as e:
        logger.error(f"Error fetching withdrawal stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch withdrawal statistics")


@router.get("/balance", summary="Get Available Balance")
def get_available_balance(
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Calculate and return vendor's available balance after commission and withdrawals"""
    try:
        vendor_id = vendor.id

        # Get total revenue from successful payments
        analytics = payment_crud.get_payment_analytics(db, vendor_id=vendor_id)
        total_revenue = analytics['total_revenue']

        # Calculate commission (10%)
        commission_rate = 0.10
        commission_amount = total_revenue * commission_rate
        net_earnings = total_revenue - commission_amount

        # Get withdrawal amounts
        completed_withdrawals = withdrawal_crud.get_completed_withdrawal_amount(db, vendor_id)
        pending_withdrawals = withdrawal_crud.get_pending_withdrawal_amount(db, vendor_id)

        # Calculate available balance
        available_balance = net_earnings - completed_withdrawals - pending_withdrawals

        return {
            "success": True,
            "total_revenue": total_revenue,
            "commission_rate": commission_rate,
            "commission_amount": commission_amount,
            "net_earnings": net_earnings,
            "completed_withdrawals": completed_withdrawals,
            "pending_withdrawals": pending_withdrawals,
            "available_balance": max(0, available_balance),  # Never negative
            "successful_payments": analytics['successful_payments'],
        }

    except Exception as e:
        logger.error(f"Error calculating balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate balance: {str(e)}")


@router.get("/{withdrawal_id}", response_model=WithdrawalOut, summary="Get Withdrawal Details")
def get_withdrawal_details(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Get specific withdrawal details"""
    withdrawal = withdrawal_crud.get_withdrawal_by_id(db, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    if withdrawal.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    return withdrawal


@router.delete("/{withdrawal_id}", summary="Cancel Withdrawal Request")
def cancel_withdrawal(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    vendor=Depends(get_current_vendor)
):
    """Cancel a pending withdrawal request"""
    withdrawal = withdrawal_crud.get_withdrawal_by_id(db, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    if withdrawal.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    if withdrawal.status != WithdrawalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel withdrawal with status {withdrawal.status.value}"
        )

    try:
        withdrawal_crud.delete_withdrawal(db, withdrawal_id)
        return {"success": True, "message": "Withdrawal request cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))