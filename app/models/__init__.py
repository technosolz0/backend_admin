# app/models/__init__.py

# Import all models in order to resolve relationships
from .user import User, UserStatus, LoginLog
from .user_address import UserAddress
from .category import Category
from .sub_category import SubCategory
from .service_provider_model import ServiceProvider
from .vendor_subcategory_charge import VendorSubcategoryCharge
from .booking_model import Booking, BookingStatus
from .payment_model import Payment

# Ensure all mappers are configured after all imports
from sqlalchemy.orm import configure_mappers
configure_mappers()

