import unittest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.vendor_model import Vendor
from app.models.booking_model import Booking, BookingStatus
from app.models.vendor_earnings_model import VendorEarnings
from app.models.commission_tier_model import CommissionTier
from app.services.commission_service import (
    calculate_daily_commission_tier,
    get_vendor_daily_completed_bookings_count,
    get_vendor_current_commission_tier_status,
    record_vendor_booking_earnings,
    seed_default_commission_tiers,
    reset_commission_tiers_to_default,
    get_active_commission_tiers,
    DEFAULT_COMMISSION_TIER_STANDARD,
    DEFAULT_COMMISSION_TIER_5_TO_10,
    DEFAULT_COMMISSION_TIER_ABOVE_10
)

class TestDynamicCommissionService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Seed test vendor
        self.vendor = Vendor(
            full_name="Rajesh Kumar",
            email="rajesh@vendor.com",
            phone="9812345678",
            password="hash",
            referral_code="RAJESH1234"
        )
        self.db.add(self.vendor)
        self.db.commit()
        self.db.refresh(self.vendor)

    def tearDown(self):
        self.db.rollback()
        self.db.close()
        with self.engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())

    def test_default_commission_tier_percentages(self):
        """Test calculation of daily commission tiers with defaults."""
        # 1st to 4th booking -> 10%
        for i in range(1, 5):
            pct, name = calculate_daily_commission_tier(i, db=self.db)
            self.assertEqual(pct, DEFAULT_COMMISSION_TIER_STANDARD, f"Booking #{i} should have 10% commission")

        # 5th to 10th booking -> 7%
        for i in range(5, 11):
            pct, name = calculate_daily_commission_tier(i, db=self.db)
            self.assertEqual(pct, DEFAULT_COMMISSION_TIER_5_TO_10, f"Booking #{i} should have 7% commission")

        # > 10 bookings (11, 12, 20...) -> 5%
        for i in [11, 12, 20, 50]:
            pct, name = calculate_daily_commission_tier(i, db=self.db)
            self.assertEqual(pct, DEFAULT_COMMISSION_TIER_ABOVE_10, f"Booking #{i} should have 5% commission")

    def test_admin_update_tier_dynamically_changes_commission(self):
        """Test that updating a tier in DB directly updates the calculated commission."""
        # Seed defaults first
        seed_default_commission_tiers(self.db)

        # Admin changes Tier 2 (5-10 bookings) from 7% down to 6%
        tier2 = self.db.query(CommissionTier).filter(CommissionTier.min_bookings == 5).first()
        self.assertIsNotNone(tier2)
        tier2.commission_percentage = 6.0
        self.db.commit()

        # 6th booking of the day should now evaluate to 6.0% instead of 7.0%
        pct, name = calculate_daily_commission_tier(6, db=self.db)
        self.assertEqual(pct, 6.0)

    def test_admin_add_new_tier(self):
        """Test adding an ultra tier (e.g. >20 bookings -> 3% commission)."""
        # Seed defaults
        seed_default_commission_tiers(self.db)

        # Update Tier 3 to cap at 20
        tier3 = self.db.query(CommissionTier).filter(CommissionTier.min_bookings == 11).first()
        tier3.max_bookings = 20
        self.db.commit()

        # Add Tier 4 (21+ bookings -> 3%)
        tier4 = CommissionTier(
            tier_name="VIP Partner Tier (>20 Bookings)",
            min_bookings=21,
            max_bookings=None,
            commission_percentage=3.0,
            is_active=True
        )
        self.db.add(tier4)
        self.db.commit()

        pct15, _ = calculate_daily_commission_tier(15, db=self.db)
        self.assertEqual(pct15, 5.0)

        pct25, _ = calculate_daily_commission_tier(25, db=self.db)
        self.assertEqual(pct25, 3.0)

    def test_admin_reset_tiers_to_defaults(self):
        """Test resetting tiers back to default configuration."""
        # Modify tiers
        tier = CommissionTier(tier_name="Temporary", min_bookings=1, max_bookings=50, commission_percentage=1.0)
        self.db.add(tier)
        self.db.commit()

        # Reset
        tiers = reset_commission_tiers_to_default(self.db)
        self.assertEqual(len(tiers), 3)
        self.assertEqual(tiers[0].commission_percentage, 10.0)
        self.assertEqual(tiers[1].commission_percentage, 7.0)
        self.assertEqual(tiers[2].commission_percentage, 5.0)

    def test_record_vendor_earnings_daily_progression(self):
        """Test sequential booking earnings in a day follow the dynamic commission tier."""
        vendor_id = self.vendor.id

        # Simulate 12 bookings on the same day, each with total_paid = 1000.0
        for booking_num in range(1, 13):
            booking = Booking(
                id=booking_num,
                vendor_id=vendor_id,
                address="Test Address",
                status=BookingStatus.completed
            )
            self.db.add(booking)
            self.db.commit()

            earning = record_vendor_booking_earnings(
                db=self.db,
                booking_id=booking_num,
                vendor_id=vendor_id,
                total_paid=1000.0
            )

            if booking_num <= 4:
                self.assertEqual(earning.commission_percentage, 10.0)
                self.assertEqual(earning.commission_amount, 100.0)
                self.assertEqual(earning.final_amount, 900.0)
            elif 5 <= booking_num <= 10:
                self.assertEqual(earning.commission_percentage, 7.0)
                self.assertEqual(earning.commission_amount, 70.0)
                self.assertEqual(earning.final_amount, 930.0)
            else:
                self.assertEqual(earning.commission_percentage, 5.0)
                self.assertEqual(earning.commission_amount, 50.0)
                self.assertEqual(earning.final_amount, 950.0)

if __name__ == "__main__":
    unittest.main()
