# app/api/routes/tracking_routes.py
# Production-Ready Live Vendor Tracking APIs & WebSocket Manager
# Rules Enforced:
# 1. Vendor navigates ONLY to Booked Service Location (booking_latitude, booking_longitude).
# 2. Customer Live GPS is NEVER shared with vendor and NEVER used for arrival.
# 3. Arrival is calculated strictly between Vendor Live Location and Booked Service Location.
# 4. Backend is the sole authoritative source of tracking status.

import math
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import (
    APIRouter, Depends, HTTPException, Query, Body, status, 
    WebSocket, WebSocketDisconnect
)
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from app.core.security import (
    get_db, get_current_vendor, get_current_user, get_current_identity,
    SECRET_KEY, ALGORITHM
)
from app.models.booking_model import Booking, BookingStatus
from app.models.user import User
from app.models.service_provider_model import ServiceProvider as Vendor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Live Tracking"])

VENDOR_ARRIVAL_RADIUS_METERS = 50.0  # Configurable arrival radius in meters

# ─────────────────────────────────────────────
# UTILS: Haversine distance & ETA calculation
# ─────────────────────────────────────────────

def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in meters between two GPS coordinates."""
    if any(v is None for v in [lat1, lng1, lat2, lng2]):
        return float('inf')
    R = 6371000.0  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_eta_minutes(distance_meters: float, avg_speed_kmh: float = 25.0) -> int:
    """Estimate ETA in minutes based on distance in meters and city traffic speed."""
    if distance_meters == float('inf') or distance_meters < 0:
        return 0
    distance_km = distance_meters / 1000.0
    hours = distance_km / max(avg_speed_kmh, 5.0)
    return max(1, round(hours * 60))


# ─────────────────────────────────────────────
# WEBSOCKET CONNECTION MANAGER
# ─────────────────────────────────────────────

class TrackingConnectionManager:
    """Manages active WebSocket connections for order tracking."""
    def __init__(self):
        # Maps order_id -> List of WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, order_id: int, websocket: WebSocket):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = []
        self.active_connections[order_id].append(websocket)
        logger.info(f"🔌 WebSocket client connected to order {order_id} tracking channel (total: {len(self.active_connections[order_id])})")

    def disconnect(self, order_id: int, websocket: WebSocket):
        if order_id in self.active_connections:
            if websocket in self.active_connections[order_id]:
                self.active_connections[order_id].remove(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        logger.info(f"🔌 WebSocket client disconnected from order {order_id} tracking channel")

    async def broadcast_to_order(self, order_id: int, payload: dict):
        if order_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[order_id]:
                try:
                    await connection.send_json(payload)
                except Exception as e:
                    logger.warning(f"Error sending payload to WS connection: {e}")
                    disconnected.append(connection)
            for dead_conn in disconnected:
                self.disconnect(order_id, dead_conn)


tracking_ws_manager = TrackingConnectionManager()


# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class VendorLocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy: Optional[float] = Field(None, ge=0.0)
    timestamp: Optional[datetime] = None


# ─────────────────────────────────────────────
# REST ENDPOINTS
# ─────────────────────────────────────────────

@router.post("/{order_id}/tracking/start", response_model=dict)
def start_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(get_current_vendor),
):
    """
    Vendor starts live tracking for an accepted order.
    Sets tracking_status to ACTIVE.
    """
    booking = db.query(Booking).filter(Booking.id == order_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Order not found")

    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized: Order not assigned to you")

    if booking.status != BookingStatus.accepted:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start tracking for order in status {booking.status}. Order must be accepted."
        )

    booking.tracking_status = "ACTIVE"
    if not booking.tracking_started_at:
        booking.tracking_started_at = datetime.utcnow()

    # Initial vendor coordinates
    if vendor.latitude is not None and vendor.longitude is not None:
        booking.latest_vendor_latitude = vendor.latitude
        booking.latest_vendor_longitude = vendor.longitude
        booking.latest_vendor_location_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(booking)

    logger.info(f"🟢 Tracking STARTED for order #{order_id} by vendor #{vendor.id}")
    return {
        "success": True,
        "message": "Tracking started",
        "order_id": booking.id,
        "tracking_status": booking.tracking_status,
        "tracking_started_at": booking.tracking_started_at.isoformat() if booking.tracking_started_at else None,
    }


@router.get("/{order_id}/tracking", response_model=dict)
def get_order_tracking_info(
    order_id: int,
    db: Session = Depends(get_db),
    identity=Depends(get_current_identity),
):
    """
    Fetch authoritative tracking state for an order.
    Returns destination (Booked Service Location), latest vendor location, status, distance, and ETA.
    """
    booking = db.query(Booking).filter(Booking.id == order_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Order not found")

    # Access control: Owner User, Assigned Vendor, or Admin
    is_owner = isinstance(identity, User) and identity.id == booking.user_id
    is_vendor = isinstance(identity, Vendor) and identity.id == booking.serviceprovider_id
    is_admin = isinstance(identity, User) and getattr(identity, "is_superuser", False)

    if not (is_owner or is_vendor or is_admin):
        raise HTTPException(status_code=403, detail="Unauthorized access to order tracking")

    # Authoritative vendor position
    vendor = booking.service_provider
    vendor_lat = booking.latest_vendor_latitude if booking.latest_vendor_latitude is not None else (vendor.latitude if vendor else None)
    vendor_lng = booking.latest_vendor_longitude if booking.latest_vendor_longitude is not None else (vendor.longitude if vendor else None)
    vendor_updated_at = booking.latest_vendor_location_updated_at or (vendor.last_device_update if vendor else None)

    # Destination is strictly the Booked Service Location
    dest_lat = booking.booking_latitude
    dest_lng = booking.booking_longitude

    distance_meters = None
    eta_minutes = None

    if vendor_lat is not None and vendor_lng is not None and dest_lat is not None and dest_lng is not None:
        distance_meters = round(calculate_haversine_distance(vendor_lat, vendor_lng, dest_lat, dest_lng), 1)
        eta_minutes = estimate_eta_minutes(distance_meters)

    return {
        "order_id": booking.id,
        "order_status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        "tracking_status": booking.tracking_status or ("ACTIVE" if booking.status == BookingStatus.accepted else "NOT_STARTED"),
        "destination": {
            "address": booking.address,
            "latitude": dest_lat,
            "longitude": dest_lng,
        },
        "vendor": {
            "id": vendor.id if vendor else booking.serviceprovider_id,
            "name": vendor.full_name if vendor else "Provider",
            "phone": vendor.phone if vendor else None,
            "latitude": vendor_lat,
            "longitude": vendor_lng,
            "updated_at": vendor_updated_at.isoformat() if vendor_updated_at else None,
        },
        "distance_meters": distance_meters,
        "eta_minutes": eta_minutes,
        "arrival_radius_meters": VENDOR_ARRIVAL_RADIUS_METERS,
        "tracking_started_at": booking.tracking_started_at.isoformat() if booking.tracking_started_at else None,
        "vendor_arrived_at": booking.vendor_arrived_at.isoformat() if booking.vendor_arrived_at else None,
    }


@router.post("/{order_id}/tracking/vendor-location", response_model=dict)
async def update_vendor_order_location(
    order_id: int,
    payload: VendorLocationUpdateRequest,
    db: Session = Depends(get_db),
    vendor: Vendor = Depends(get_current_vendor),
):
    """
    Vendor posts live GPS coordinates while travelling to the booked location.
    Updates DB, checks arrival against Booked Location, and broadcasts realtime event via WebSocket.
    """
    booking = db.query(Booking).filter(Booking.id == order_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Order not found")

    if booking.serviceprovider_id != vendor.id:
        raise HTTPException(status_code=403, detail="Unauthorized: Order not assigned to you")

    current_tracking_status = booking.tracking_status or ("ACTIVE" if booking.status == BookingStatus.accepted else "NOT_STARTED")
    if current_tracking_status not in ["ACTIVE", "NOT_STARTED"]:
        return {
            "success": False,
            "message": f"Tracking is not active for this order (status: {current_tracking_status})",
            "tracking_status": current_tracking_status,
        }

    # Stale location check
    now = datetime.utcnow()
    if payload.timestamp and booking.latest_vendor_location_updated_at:
        if payload.timestamp < booking.latest_vendor_location_updated_at:
            logger.warning(f"Rejected stale GPS update for order #{order_id}")
            return {
                "success": False,
                "message": "Ignored stale location update",
                "tracking_status": current_tracking_status,
            }

    # Update Vendor entity
    vendor.latitude = payload.latitude
    vendor.longitude = payload.longitude
    vendor.last_device_update = now

    # Update Booking tracking fields
    booking.latest_vendor_latitude = payload.latitude
    booking.latest_vendor_longitude = payload.longitude
    booking.latest_vendor_location_updated_at = now

    if booking.tracking_status != "ACTIVE":
        booking.tracking_status = "ACTIVE"
        if not booking.tracking_started_at:
            booking.tracking_started_at = now

    # Calculate distance strictly against BOOKED SERVICE LOCATION
    dest_lat = booking.booking_latitude
    dest_lng = booking.booking_longitude
    distance_meters = None
    eta_minutes = None
    has_arrived = False

    if dest_lat is not None and dest_lng is not None:
        distance_meters = round(calculate_haversine_distance(payload.latitude, payload.longitude, dest_lat, dest_lng), 1)
        eta_minutes = estimate_eta_minutes(distance_meters)

        # Arrival validation
        accuracy_ok = payload.accuracy is None or payload.accuracy <= 50.0
        if distance_meters <= VENDOR_ARRIVAL_RADIUS_METERS and accuracy_ok:
            has_arrived = True
            booking.tracking_status = "ARRIVED"
            booking.vendor_arrived_at = now
            booking.tracking_ended_at = now
            logger.info(f"🎯 VENDOR ARRIVED for order #{order_id}! (Distance: {distance_meters}m)")

    db.commit()
    db.refresh(booking)

    # Broadcast event via WebSocket
    event_name = "vendor_arrived" if has_arrived else "vendor_location_updated"
    event_data = {
        "event": event_name,
        "order_id": booking.id,
        "tracking_status": booking.tracking_status,
        "vendor": {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "accuracy": payload.accuracy,
            "timestamp": now.isoformat(),
        },
        "destination": {
            "address": booking.address,
            "latitude": dest_lat,
            "longitude": dest_lng,
        },
        "distance_meters": distance_meters,
        "eta_minutes": eta_minutes,
        "arrived_at": booking.vendor_arrived_at.isoformat() if booking.vendor_arrived_at else None,
    }

    await tracking_ws_manager.broadcast_to_order(booking.id, event_data)

    return {
        "success": True,
        "order_id": booking.id,
        "tracking_status": booking.tracking_status,
        "distance_meters": distance_meters,
        "eta_minutes": eta_minutes,
        "has_arrived": has_arrived,
    }


# ─────────────────────────────────────────────
# WEBSOCKET ROUTE
# ─────────────────────────────────────────────

@router.websocket("/ws/{order_id}")
async def tracking_websocket_endpoint(
    websocket: WebSocket,
    order_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for realtime tracking channel.
    URL: ws://<host>/api/orders/ws/{order_id}?token=<jwt>
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return

    # Authenticate JWT token
    authenticated_id = None
    role = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        role = payload.get("role", "user")
        if sub is not None:
            authenticated_id = int(sub)
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    if not authenticated_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
        return

    # Authorize access to order
    booking = db.query(Booking).filter(Booking.id == order_id).first()
    if not booking:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Order not found")
        return

    is_authorized = False
    if role == "vendor" and booking.serviceprovider_id == authenticated_id:
        is_authorized = True
    elif role == "user" and booking.user_id == authenticated_id:
        is_authorized = True
    elif role == "admin":
        is_authorized = True

    if not is_authorized:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return

    await tracking_ws_manager.connect(order_id, websocket)

    try:
        # Send initial tracking state on connect
        vendor = booking.service_provider
        vendor_lat = booking.latest_vendor_latitude or (vendor.latitude if vendor else None)
        vendor_lng = booking.latest_vendor_longitude or (vendor.longitude if vendor else None)
        dest_lat = booking.booking_latitude
        dest_lng = booking.booking_longitude
        dist = round(calculate_haversine_distance(vendor_lat, vendor_lng, dest_lat, dest_lng), 1) if (vendor_lat and dest_lat) else None

        await websocket.send_json({
            "event": "connected",
            "order_id": booking.id,
            "tracking_status": booking.tracking_status or ("ACTIVE" if booking.status == BookingStatus.accepted else "NOT_STARTED"),
            "destination": {
                "address": booking.address,
                "latitude": dest_lat,
                "longitude": dest_lng,
            },
            "vendor": {
                "latitude": vendor_lat,
                "longitude": vendor_lng,
            },
            "distance_meters": dist,
            "eta_minutes": estimate_eta_minutes(dist) if dist else None,
        })

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})

    except WebSocketDisconnect:
        tracking_ws_manager.disconnect(order_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error on order #{order_id}: {e}")
        tracking_ws_manager.disconnect(order_id, websocket)
