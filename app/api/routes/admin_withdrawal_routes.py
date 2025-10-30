# app/api/routes/admin_withdrawal_routes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.crud import service_provider_crud as vendor_crud
import logging

from app.core.security import get_db  # Add your admin authentication dependency
from app.schemas.withdrawal_schema import WithdrawalOut, WithdrawalUpdate
from app.crud import withdrawal_crud
from app.models.withdrawal_model import WithdrawalStatus
from app.utils.fcm import send_notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/withdrawals", tags=["Admin - Withdrawals"])


# TODO: Replace with your actual admin authentication
def get_current_admin(db: Session = Depends(get_db)):
    """Replace this with your actual admin authentication logic"""
    # For now, returning a mock admin
    class MockAdmin:
        id = 1
        email = "admin@serwex.com"
    return MockAdmin()


@router.get("/", response_model=List[WithdrawalOut], summary="Get All Withdrawals")
def get_all_withdrawals(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    status: Optional[WithdrawalStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Admin: Get all withdrawal requests"""
    try:
        withdrawals = withdrawal_crud.get_all_withdrawals(
            db, status=status, skip=skip, limit=limit
        )
        return withdrawals
    except Exception as e:
        logger.error(f"Error fetching all withdrawals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch withdrawals")


@router.get("/pending", response_model=List[WithdrawalOut], summary="Get Pending Withdrawals")
def get_pending_withdrawals(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """Admin: Get all pending withdrawal requests"""
    try:
        withdrawals = withdrawal_crud.get_all_withdrawals(
            db, status=WithdrawalStatus.PENDING, skip=skip, limit=limit
        )
        return withdrawals
    except Exception as e:
        logger.error(f"Error fetching pending withdrawals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending withdrawals")


@router.patch("/{withdrawal_id}/status", response_model=WithdrawalOut, summary="Update Withdrawal Status")
def update_withdrawal_status(
    withdrawal_id: int,
    update_data: WithdrawalUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Admin: Update withdrawal status with custom message"""
    withdrawal = withdrawal_crud.get_withdrawal_by_id(db, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    try:
        # Update withdrawal status
        updated_withdrawal = withdrawal_crud.update_withdrawal_status(
            db,
            withdrawal,
            update_data.status,
            admin.id,
            update_data.admin_message
        )

        # Send notification to vendor
        try:
            from app.crud import vendor_crud
            vendor = vendor_crud.get_vendor_by_id(db, withdrawal.vendor_id)

            if vendor:
                status_messages = {
                    WithdrawalStatus.PROCESSING: f"Your withdrawal request of ₹{withdrawal.amount} is being processed.",
                    WithdrawalStatus.APPROVED: f"Your withdrawal request of ₹{withdrawal.amount} has been approved!",
                    WithdrawalStatus.COMPLETED: f"₹{withdrawal.amount} has been transferred to your account.",
                    WithdrawalStatus.REJECTED: f"Your withdrawal request of ₹{withdrawal.amount} has been rejected."
                }

                message = status_messages.get(update_data.status, "Your withdrawal status has been updated.")

                # Add admin's custom message if provided
                if update_data.admin_message:
                    message += f" Message: {update_data.admin_message}"

                vendor_fcm_token = vendor.new_fcm_token or vendor.old_fcm_token
                send_notification(
                    recipient=vendor.email,
                    notification_type=f"withdrawal_{update_data.status.value.lower()}",
                    message=message,
                    recipient_id=vendor.id,
                    fcm_token=vendor_fcm_token
                )
                logger.info(f"Notification sent to vendor {vendor.id} for withdrawal {withdrawal_id}")

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            # Don't fail the request if notification fails

        return updated_withdrawal

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating withdrawal status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update withdrawal status")


@router.get("/stats", summary="Get Admin Withdrawal Statistics")
def get_admin_withdrawal_stats(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Admin: Get overall withdrawal statistics"""
    try:
        from sqlalchemy import func
        from app.models.withdrawal_model import Withdrawal

        total_withdrawals = db.query(func.count(Withdrawal.id)).scalar()
        pending_count = db.query(func.count(Withdrawal.id)).filter(
            Withdrawal.status == WithdrawalStatus.PENDING
        ).scalar()
        processing_count = db.query(func.count(Withdrawal.id)).filter(
            Withdrawal.status == WithdrawalStatus.PROCESSING
        ).scalar()
        approved_count = db.query(func.count(Withdrawal.id)).filter(
            Withdrawal.status.in_([WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED])
        ).scalar()
        rejected_count = db.query(func.count(Withdrawal.id)).filter(
            Withdrawal.status == WithdrawalStatus.REJECTED
        ).scalar()

        total_amount = db.query(func.sum(Withdrawal.amount)).filter(
            Withdrawal.status.in_([WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED])
        ).scalar() or 0

        pending_amount = db.query(func.sum(Withdrawal.amount)).filter(
            Withdrawal.status.in_([WithdrawalStatus.PENDING, WithdrawalStatus.PROCESSING])
        ).scalar() or 0

        return {
            "success": True,
            "total_withdrawals": total_withdrawals or 0,
            "pending_count": pending_count or 0,
            "processing_count": processing_count or 0,
            "approved_count": approved_count or 0,
            "rejected_count": rejected_count or 0,
            "total_amount_disbursed": float(total_amount),
            "pending_amount": float(pending_amount),
        }

    except Exception as e:
        logger.error(f"Error fetching admin withdrawal stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/{withdrawal_id}", response_model=WithdrawalOut, summary="Get Withdrawal Details")
def get_withdrawal_details(
    withdrawal_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):
    """Admin: Get specific withdrawal details"""
    withdrawal = withdrawal_crud.get_withdrawal_by_id(db, withdrawal_id)

    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")

    return withdrawal