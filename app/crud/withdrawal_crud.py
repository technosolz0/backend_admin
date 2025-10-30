# app/crud/withdrawal_crud.py

from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.withdrawal_model import Withdrawal, WithdrawalStatus
from app.schemas.withdrawal_schema import WithdrawalRequest, WithdrawalUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

COMMISSION_RATE = 0.10  # 10% commission


def calculate_commission(gross_amount: float) -> tuple[float, float]:
    """Calculate commission and net amount
    Returns: (commission_amount, net_amount)
    """
    commission = round(gross_amount * COMMISSION_RATE, 2)
    net_amount = round(gross_amount - commission, 2)
    return commission, net_amount


def create_withdrawal(db: Session, vendor_id: int, withdrawal_data: WithdrawalRequest) -> Withdrawal:
    """Create a new withdrawal request"""
    # The amount vendor requests is already net (after commission)
    # We need to calculate back the gross amount
    net_amount = withdrawal_data.amount
    gross_amount = round(net_amount / (1 - COMMISSION_RATE), 2)
    commission_amount = round(gross_amount - net_amount, 2)

    withdrawal = Withdrawal(
        vendor_id=vendor_id,
        amount=net_amount,
        gross_amount=gross_amount,
        commission_amount=commission_amount,
        bank_account=withdrawal_data.bank_account or "default",
        notes=withdrawal_data.notes,
        status=WithdrawalStatus.PENDING,
        requested_at=datetime.utcnow(),
    )

    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)

    logger.info(f"Withdrawal request created: ID {withdrawal.id} for vendor {vendor_id}, amount ₹{net_amount}")
    return withdrawal


def get_withdrawal_by_id(db: Session, withdrawal_id: int) -> Optional[Withdrawal]:
    """Get withdrawal by ID"""
    return db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).first()


def get_withdrawals_by_vendor_id(
    db: Session,
    vendor_id: int,
    status: Optional[WithdrawalStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Withdrawal]:
    """Get all withdrawals for a vendor"""
    query = db.query(Withdrawal).filter(Withdrawal.vendor_id == vendor_id)

    if status:
        query = query.filter(Withdrawal.status == status)

    return query.order_by(desc(Withdrawal.requested_at)).offset(skip).limit(limit).all()


def get_all_withdrawals(
    db: Session,
    status: Optional[WithdrawalStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Withdrawal]:
    """Get all withdrawals (admin only)"""
    query = db.query(Withdrawal)

    if status:
        query = query.filter(Withdrawal.status == status)

    return query.order_by(desc(Withdrawal.requested_at)).offset(skip).limit(limit).all()


def update_withdrawal_status(
    db: Session,
    withdrawal: Withdrawal,
    status: WithdrawalStatus,
    admin_id: int,
    admin_message: Optional[str] = None
) -> Withdrawal:
    """Update withdrawal status by admin"""
    old_status = withdrawal.status

    # Validate status transitions
    valid_transitions = {
        WithdrawalStatus.PENDING: [WithdrawalStatus.PROCESSING, WithdrawalStatus.REJECTED],
        WithdrawalStatus.PROCESSING: [WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED, WithdrawalStatus.REJECTED],
        WithdrawalStatus.APPROVED: [WithdrawalStatus.COMPLETED],
        WithdrawalStatus.COMPLETED: [],
        WithdrawalStatus.REJECTED: []
    }

    if status not in valid_transitions.get(old_status, []):
        raise ValueError(f"Invalid status transition from {old_status} to {status}")

    withdrawal.status = status
    withdrawal.admin_id = admin_id
    withdrawal.admin_message = admin_message
    withdrawal.processed_at = datetime.utcnow()
    withdrawal.updated_at = datetime.utcnow()

    if status == WithdrawalStatus.COMPLETED:
        withdrawal.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(withdrawal)

    logger.info(f"Withdrawal {withdrawal.id} status updated from {old_status} to {status} by admin {admin_id}")
    return withdrawal


def get_vendor_withdrawal_stats(db: Session, vendor_id: int) -> dict:
    """Get withdrawal statistics for a vendor"""
    withdrawals = db.query(Withdrawal).filter(Withdrawal.vendor_id == vendor_id).all()

    total_withdrawals = len(withdrawals)
    pending_count = len([w for w in withdrawals if w.status == WithdrawalStatus.PENDING])
    approved_count = len([w for w in withdrawals if w.status in [WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED]])
    rejected_count = len([w for w in withdrawals if w.status == WithdrawalStatus.REJECTED])

    total_withdrawn = sum(w.amount for w in withdrawals if w.status in [WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED])
    pending_amount = sum(w.amount for w in withdrawals if w.status == WithdrawalStatus.PENDING)

    return {
        "total_withdrawals": total_withdrawals,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "rejected_count": rejected_count,
        "total_withdrawn": total_withdrawn,
        "pending_amount": pending_amount,
    }


def get_pending_withdrawal_amount(db: Session, vendor_id: int) -> float:
    """Get total pending withdrawal amount for a vendor"""
    result = db.query(func.sum(Withdrawal.amount)).filter(
        and_(
            Withdrawal.vendor_id == vendor_id,
            Withdrawal.status.in_([WithdrawalStatus.PENDING, WithdrawalStatus.PROCESSING])
        )
    ).scalar()

    return float(result or 0)


def get_completed_withdrawal_amount(db: Session, vendor_id: int) -> float:
    """Get total completed withdrawal amount for a vendor"""
    result = db.query(func.sum(Withdrawal.amount)).filter(
        and_(
            Withdrawal.vendor_id == vendor_id,
            Withdrawal.status.in_([WithdrawalStatus.APPROVED, WithdrawalStatus.COMPLETED])
        )
    ).scalar()

    return float(result or 0)


def delete_withdrawal(db: Session, withdrawal_id: int) -> bool:
    """Delete withdrawal (only if pending)"""
    withdrawal = get_withdrawal_by_id(db, withdrawal_id)
    if not withdrawal:
        return False

    if withdrawal.status != WithdrawalStatus.PENDING:
        raise ValueError("Can only delete pending withdrawal requests")

    db.delete(withdrawal)
    db.commit()
    logger.info(f"Withdrawal {withdrawal_id} deleted")
    return True