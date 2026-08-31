import sys
import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path and sqlite in-memory or test database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from unittest.mock import MagicMock
sys.modules['bcrypt'] = MagicMock()
sys.modules['passlib'] = MagicMock()
sys.modules['passlib.context'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.messaging'] = MagicMock()
sys.modules['jose'] = MagicMock()

from app.database import Base
from app.models.vendor_model import Vendor
from app.models.vendor_referral_model import VendorReferral, ReferralStatus
from app.models.booking_model import Booking, BookingStatus
from app.models.wallet_model import Wallet, WalletTransaction
from app.models.app_config_model import AppConfig
from app.services.referral_service import (
    process_vendor_referral_registration,
    process_first_booking_referral_reward,
    get_referral_reward_configs
)
from app.crud.vendor_crud import generate_referral_code

# Setup test DB (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def run_referral_system_tests():
    print("=" * 60)
    print("RUNNING VENDOR REFERRAL & REWARDS SYSTEM VERIFICATION TESTS")
    print("=" * 60)

    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    try:
        # --- TEST 1: App Config Defaults ---
        referrer_reward, referred_reward = get_referral_reward_configs(db)
        assert referrer_reward == 100.0, f"Expected 100.0, got {referrer_reward}"
        assert referred_reward == 50.0, f"Expected 50.0, got {referred_reward}"
        print("✅ TEST 1 PASSED: Default referral reward configuration (₹100 / ₹50)")

        # --- TEST 2: Create Referrer Vendor A ---
        vendor_a = Vendor(
            full_name="Vendor Alpha",
            email="alphavendor@serwex.in",
            phone="9876543210",
            password="HashedPassword123",
            referral_code=generate_referral_code(db, "Vendor Alpha"),
            status="approved",
            admin_status="active"
        )
        db.add(vendor_a)
        db.commit()
        db.refresh(vendor_a)

        assert vendor_a.referral_code is not None, "Vendor A referral code not generated"
        print(f"✅ TEST 2 PASSED: Created Referrer Vendor A with referral code: {vendor_a.referral_code}")

        # --- TEST 3: Self-Referral Prevention ---
        vendor_a_self_res = process_vendor_referral_registration(db, vendor_a, vendor_a.referral_code)
        assert vendor_a_self_res == False, "Self-referral should have been rejected!"
        print("✅ TEST 3 PASSED: Self-referral attempt successfully rejected")

        # --- TEST 4: Create Referred Vendor B with Vendor A's Referral Code ---
        vendor_b = Vendor(
            full_name="Vendor Beta",
            email="betavendor@serwex.in",
            phone="9876543211",
            password="HashedPassword123",
            referral_code=generate_referral_code(db, "Vendor Beta"),
            status="approved",
            admin_status="active"
        )
        db.add(vendor_b)
        db.commit()
        db.refresh(vendor_b)

        ref_success = process_vendor_referral_registration(db, vendor_b, vendor_a.referral_code)
        assert ref_success == True, "Referral registration failed for Vendor B"

        # Verify Vendor B association
        db.refresh(vendor_b)
        assert vendor_b.referred_by_id == vendor_a.id, "Vendor B referred_by_id mismatch"
        assert vendor_b.applied_referral_code == vendor_a.referral_code, "Applied referral code mismatch"

        # Verify VendorReferral DB record
        referral_rec = db.query(VendorReferral).filter(VendorReferral.referred_vendor_id == vendor_b.id).first()
        assert referral_rec is not None, "VendorReferral record not found"
        assert referral_rec.status == ReferralStatus.REGISTERED, f"Expected REGISTERED status, got {referral_rec.status}"
        assert referral_rec.referrer_vendor_id == vendor_a.id
        print("✅ TEST 4 PASSED: Vendor B successfully registered with Vendor A referral code")

        # --- TEST 5: Prevent Multiple Referrers ---
        vendor_c = Vendor(
            full_name="Vendor Charlie",
            email="charlievendor@serwex.in",
            phone="9876543212",
            password="HashedPassword123",
            referral_code=generate_referral_code(db, "Vendor Charlie"),
            status="approved",
            admin_status="active"
        )
        db.add(vendor_c)
        db.commit()
        db.refresh(vendor_c)

        second_ref_attempt = process_vendor_referral_registration(db, vendor_b, vendor_c.referral_code)
        assert second_ref_attempt == False, "Second referral overwrite should be rejected!"
        print("✅ TEST 5 PASSED: Second referral claim on existing vendor successfully rejected")

        # --- TEST 6: In-Progress / Accepted Booking Does NOT Trigger Reward ---
        booking_1 = Booking(
            user_id=1,
            vendor_id=vendor_b.id,
            category_id=1,
            subcategory_id=1,
            address="Test Address",
            status=BookingStatus.accepted
        )
        db.add(booking_1)
        db.commit()
        db.refresh(booking_1)

        res_accepted = process_first_booking_referral_reward(db, booking_1)
        assert res_accepted == False, "Accepted booking should NOT trigger referral reward"

        db.refresh(referral_rec)
        assert referral_rec.status == ReferralStatus.REGISTERED, "Status should remain REGISTERED"
        print("✅ TEST 6 PASSED: Non-completed booking (accepted) does not trigger reward")

        # --- TEST 7: Completed Booking Triggers Referral Reward Qualification & Wallet Credits ---
        booking_1.status = BookingStatus.completed
        db.commit()

        reward_res = process_first_booking_referral_reward(db, booking_1)
        assert reward_res == True, "First completed booking should have triggered referral reward!"

        db.refresh(referral_rec)
        assert referral_rec.status == ReferralStatus.REWARDED, f"Expected REWARDED status, got {referral_rec.status}"
        assert referral_rec.qualified_booking_id == booking_1.id, "Qualified booking ID mismatch"
        assert referral_rec.rewarded_at is not None, "Rewarded timestamp missing"

        # Check Vendor A (Referrer) Wallet & WalletTransaction
        wallet_a = db.query(Wallet).filter(Wallet.vendor_id == vendor_a.id).first()
        assert wallet_a is not None, "Vendor A wallet missing"
        assert wallet_a.balance == 100.0, f"Expected ₹100.0 in Vendor A wallet, got {wallet_a.balance}"

        tx_a = db.query(WalletTransaction).filter(WalletTransaction.vendor_id == vendor_a.id).first()
        assert tx_a is not None, "Vendor A transaction record missing"
        assert tx_a.amount == 100.0
        assert tx_a.transaction_type == "REFERRAL_BONUS_REFERRER"
        assert tx_a.reference_id == f"REF_BONUS_REFERRER_{referral_rec.id}"

        # Check Vendor B (Referred Vendor) Wallet & WalletTransaction
        wallet_b = db.query(Wallet).filter(Wallet.vendor_id == vendor_b.id).first()
        assert wallet_b is not None, "Vendor B wallet missing"
        assert wallet_b.balance == 50.0, f"Expected ₹50.0 in Vendor B wallet, got {wallet_b.balance}"

        tx_b = db.query(WalletTransaction).filter(WalletTransaction.vendor_id == vendor_b.id).first()
        assert tx_b is not None, "Vendor B transaction record missing"
        assert tx_b.amount == 50.0
        assert tx_b.transaction_type == "REFERRAL_BONUS_NEW_VENDOR"
        assert tx_b.reference_id == f"REF_BONUS_REFERRED_{referral_rec.id}"

        print(f"✅ TEST 7 PASSED: First completed booking qualified & rewarded! Vendor A: +₹{wallet_a.balance}, Vendor B: +₹{wallet_b.balance}")

        # --- TEST 8: Idempotency Check on Second Booking / Duplicate Call ---
        booking_2 = Booking(
            user_id=1,
            vendor_id=vendor_b.id,
            category_id=1,
            subcategory_id=1,
            address="Test Address 2",
            status=BookingStatus.completed
        )
        db.add(booking_2)
        db.commit()

        duplicate_reward_res = process_first_booking_referral_reward(db, booking_2)
        assert duplicate_reward_res == False, "Subsequent completed booking should NOT trigger reward again!"

        db.refresh(wallet_a)
        db.refresh(wallet_b)
        assert wallet_a.balance == 100.0, f"Vendor A balance changed to {wallet_a.balance} on duplicate trigger!"
        assert wallet_b.balance == 50.0, f"Vendor B balance changed to {wallet_b.balance} on duplicate trigger!"

        print("✅ TEST 8 PASSED: System is fully idempotent — no duplicate rewards on subsequent bookings")

        print("=" * 60)
        print("ALL VENDOR REFERRAL & REWARD SYSTEM TESTS PASSED SUCCESSFULLY! 🎉")
        print("=" * 60)

    finally:
        db.close()

if __name__ == "__main__":
    run_referral_system_tests()
