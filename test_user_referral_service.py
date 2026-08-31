import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User, UserStatus
from app.models.vendor_model import Vendor
from app.models.booking_model import Booking, BookingStatus
from app.models.user_referral_model import UserReferral, ReferralStatus
from app.models.wallet_model import Wallet, WalletTransaction
from app.models.app_config_model import AppConfig

from app.services.referral_service import (
    generate_unique_user_referral_code,
    process_user_referral_registration,
    process_first_user_booking_referral_reward,
    get_or_create_user_wallet
)

class TestUserReferralService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Seed AppConfig
        config = AppConfig(
            user_referrer_reward_amount=50.0,
            user_referred_reward_amount=50.0
        )
        self.db.add(config)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        # Clean all tables
        with self.engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())

    def test_generate_unique_user_referral_code(self):
        user_a = User(name="User A", email="usera@example.com", mobile="9876543210")
        self.db.add(user_a)
        self.db.commit()
        self.db.refresh(user_a)

        code = generate_unique_user_referral_code(self.db, user_a)
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith("SERWEX-U"))
        self.assertEqual(user_a.referral_code, code)

    def test_process_user_referral_registration_success(self):
        referrer = User(name="Referrer", email="referrer@example.com", mobile="9000000001", referral_code="SERWEX-U10001")
        new_user = User(name="New User", email="newuser@example.com", mobile="9000000002")
        self.db.add_all([referrer, new_user])
        self.db.commit()

        success, msg = process_user_referral_registration(self.db, new_user, "SERWEX-U10001")
        self.assertTrue(success)
        
        # Verify database record created with REGISTERED status
        ref_record = self.db.query(UserReferral).filter(UserReferral.referred_user_id == new_user.id).first()
        self.assertIsNotNone(ref_record)
        self.assertEqual(ref_record.status, ReferralStatus.REGISTERED)
        self.assertEqual(ref_record.referrer_user_id, referrer.id)

        # Critical Rule Verification: Registration alone must NOT generate any wallet rewards!
        referrer_wallet = self.db.query(Wallet).filter(Wallet.user_id == referrer.id).first()
        self.assertIsNone(referrer_wallet)

    def test_prevent_self_referral(self):
        user_a = User(name="User A", email="usera@example.com", mobile="9000000003", referral_code="SERWEX-U10003")
        self.db.add(user_a)
        self.db.commit()

        success, msg = process_user_referral_registration(self.db, user_a, "SERWEX-U10003")
        self.assertFalse(success)
        self.assertIn("Self-referral", msg)

    def test_prevent_vendor_referral_cross_type(self):
        vendor = Vendor(full_name="Vendor A", email="vendor@example.com", phone="9000000004", password="pass", referral_code="SERWEX-V10004")
        new_user = User(name="New User", email="user4@example.com", mobile="9000000005")
        self.db.add_all([vendor, new_user])
        self.db.commit()

        success, msg = process_user_referral_registration(self.db, new_user, "SERWEX-V10004")
        self.assertFalse(success)
        self.assertIn("Vendor referral code", msg)

    def test_prevent_multiple_referrers(self):
        user_a = User(name="User A", email="usera@example.com", mobile="9000000006", referral_code="SERWEX-U10006")
        user_b = User(name="User B", email="userb@example.com", mobile="9000000007")
        user_c = User(name="User C", email="userc@example.com", mobile="9000000008", referral_code="SERWEX-U10008")
        self.db.add_all([user_a, user_b, user_c])
        self.db.commit()

        # First referral by User A succeeds
        success1, msg1 = process_user_referral_registration(self.db, user_b, "SERWEX-U10006")
        self.assertTrue(success1)

        # Second referral attempt by User C must be rejected
        success2, msg2 = process_user_referral_registration(self.db, user_b, "SERWEX-U10008")
        self.assertFalse(success2)

    def test_cancelled_booking_does_not_qualify(self):
        referrer = User(name="Referrer", email="ref9@example.com", mobile="9000000009", referral_code="SERWEX-U10009")
        new_user = User(name="New User", email="new9@example.com", mobile="9000000010")
        self.db.add_all([referrer, new_user])
        self.db.commit()

        process_user_referral_registration(self.db, new_user, "SERWEX-U10009")

        # Cancelled booking created for new_user
        booking = Booking(user_id=new_user.id, address="Test Addr", status=BookingStatus.cancelled)
        self.db.add(booking)
        self.db.commit()

        result = process_first_user_booking_referral_reward(self.db, booking)
        self.assertFalse(result)

        ref_record = self.db.query(UserReferral).filter(UserReferral.referred_user_id == new_user.id).first()
        self.assertEqual(ref_record.status, ReferralStatus.REGISTERED)

    def test_first_completed_booking_qualifies_and_rewards(self):
        referrer = User(name="Referrer", email="ref11@example.com", mobile="9000000011", referral_code="SERWEX-U10011")
        new_user = User(name="New User", email="new11@example.com", mobile="9000000012")
        self.db.add_all([referrer, new_user])
        self.db.commit()

        process_user_referral_registration(self.db, new_user, "SERWEX-U10011")

        # 1st Completed booking
        booking = Booking(user_id=new_user.id, address="Test Addr", status=BookingStatus.completed)
        self.db.add(booking)
        self.db.commit()

        result = process_first_user_booking_referral_reward(self.db, booking)
        self.assertTrue(result)

        # Check referral record status updated to REWARDED
        ref_record = self.db.query(UserReferral).filter(UserReferral.referred_user_id == new_user.id).first()
        self.assertEqual(ref_record.status, ReferralStatus.REWARDED)
        self.assertIsNotNone(ref_record.rewarded_at)

        # Check Referrer Wallet (random reward between 5 and 40)
        referrer_wallet = self.db.query(Wallet).filter(Wallet.user_id == referrer.id).first()
        self.assertIsNotNone(referrer_wallet)
        self.assertGreaterEqual(referrer_wallet.balance, 5.0)
        self.assertLessEqual(referrer_wallet.balance, 40.0)
        initial_referrer_bal = referrer_wallet.balance

        # Check Referred User Wallet (random reward between 5 and 40)
        new_user_wallet = self.db.query(Wallet).filter(Wallet.user_id == new_user.id).first()
        self.assertIsNotNone(new_user_wallet)
        self.assertGreaterEqual(new_user_wallet.balance, 5.0)
        self.assertLessEqual(new_user_wallet.balance, 40.0)
        initial_user_bal = new_user_wallet.balance

        # Verify idempotency: Repeating completion event for same or subsequent booking does NOT credit again
        booking2 = Booking(user_id=new_user.id, address="Test Addr 2", status=BookingStatus.completed)
        self.db.add(booking2)
        self.db.commit()

        result2 = process_first_user_booking_referral_reward(self.db, booking2)
        self.assertFalse(result2)

        # Balance remains unchanged (no duplicate reward)
        self.db.refresh(referrer_wallet)
        self.db.refresh(new_user_wallet)
        self.assertEqual(referrer_wallet.balance, initial_referrer_bal)
        self.assertEqual(new_user_wallet.balance, initial_user_bal)

if __name__ == "__main__":
    unittest.main()
