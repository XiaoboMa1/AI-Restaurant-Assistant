"""
Unified Storage Management Interface
Provides a consistent interface for data access operations
"""
import json
from typing import Dict, List, Any, Optional
from ..database.crud import crud


class StorageManager:
    """
    Unified storage manager - provides consistent interface for all data operations
    Delegates to SQLite database layer for actual storage
    """

    def __init__(self):
        """Initialize storage manager"""
        self.crud = crud

    # User management
    def create_user(self, username: str, password: str, profile: Dict[str, Any] = None) -> int:
        """Create new user"""
        user = self.crud.create_user(username, password, profile or {})
        return user.id

    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        user = self.crud.verify_user(username, password)
        return user is not None

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        user = self.crud.get_user_by_username(username)
        if not user:
            return None

        # Parse profile JSON
        try:
            profile = json.loads(user.profile_json) if user.profile_json else {}
        except (json.JSONDecodeError, TypeError):
            profile = {}

        return {
            "id": user.id,
            "username": user.username,
            "profile": profile,
            "created_at": user.created_at
        }

    def update_user_profile(self, username: str, profile: Dict[str, Any]):
        """Update user profile"""
        self.crud.update_user_profile(username, profile)

    def update_user_password(self, username: str, new_password: str):
        """Update user password"""
        self.crud.update_user_password(username, new_password)

    def list_users(self) -> List[str]:
        """List all usernames"""
        return self.crud.list_users()

    def delete_user(self, username: str) -> bool:
        """Delete user account"""
        return self.crud.delete_user(username)

    # Booking management
    def create_booking(self, username: str, booking_data: Dict[str, Any]) -> str:
        """Create new booking"""
        user = self.crud.get_user_by_username(username)
        if not user:
            raise ValueError(f"User {username} not found")

        booking = self.crud.create_booking(
            user_id=user.id,
            booking_reference=booking_data["booking_reference"],
            visit_date=booking_data["visit_date"],
            visit_time=booking_data["visit_time"],
            party_size=booking_data["party_size"],
            status=booking_data.get("status", "confirmed"),
            special_requests=booking_data.get("special_requests"),
            customer_info=booking_data.get("customer_info", {})
        )
        return booking.booking_reference

    def get_booking(self, booking_reference: str) -> Optional[Dict[str, Any]]:
        """Get booking by reference"""
        booking = self.crud.get_booking_by_reference(booking_reference)
        if not booking:
            return None

        try:
            customer_info = json.loads(booking.customer_info_json) if booking.customer_info_json else {}
        except (json.JSONDecodeError, TypeError):
            customer_info = {}

        return {
            "booking_reference": booking.booking_reference,
            "visit_date": booking.visit_date,
            "visit_time": booking.visit_time,
            "party_size": booking.party_size,
            "status": booking.status,
            "special_requests": booking.special_requests,
            "customer_info": customer_info,
            "created_at": booking.created_at
        }

    def get_user_bookings(self, username: str) -> List[Dict[str, Any]]:
        """Get all bookings for user"""
        user = self.crud.get_user_by_username(username)
        if not user:
            return []

        bookings = self.crud.get_user_bookings(user.id)
        result = []

        for booking in bookings:
            try:
                customer_info = json.loads(booking.customer_info_json) if booking.customer_info_json else {}
            except (json.JSONDecodeError, TypeError):
                customer_info = {}

            result.append({
                "booking_reference": booking.booking_reference,
                "visit_date": booking.visit_date,
                "visit_time": booking.visit_time,
                "party_size": booking.party_size,
                "status": booking.status,
                "special_requests": booking.special_requests,
                "customer_info": customer_info,
                "created_at": booking.created_at
            })

        return result

    def update_booking(self, booking_reference: str, updates: Dict[str, Any]) -> bool:
        """Update booking"""
        # Convert customer_info dict to JSON string if present
        if "customer_info" in updates:
            updates["customer_info_json"] = json.dumps(updates.pop("customer_info"))

        return self.crud.update_booking(booking_reference, **updates)

    def delete_booking(self, booking_reference: str) -> bool:
        """Delete booking"""
        return self.crud.delete_booking(booking_reference)

    # Session management
    def save_session(self, username: str, session_data: Dict[str, Any]):
        """Save user session data"""
        user = self.crud.get_user_by_username(username)
        if not user:
            raise ValueError(f"User {username} not found")

        self.crud.save_chat_session(user.id, session_data)

    def get_session(self, username: str) -> Dict[str, Any]:
        """Get user session data"""
        user = self.crud.get_user_by_username(username)
        if not user:
            return {}

        return self.crud.get_chat_session(user.id)

    def clear_session(self, username: str):
        """Clear user session"""
        user = self.crud.get_user_by_username(username)
        if user:
            self.crud.clear_chat_session(user.id)

    # Legacy compatibility methods (deprecated but maintained for backward compatibility)
    def set_current_user(self, username: str):
        """Set current user (legacy method - no longer used)"""
        pass  # This method is kept for backward compatibility but does nothing

    def get_current_user(self) -> Optional[str]:
        """Get current user (legacy method - no longer used)"""
        return None  # This method is kept for backward compatibility


# Global storage manager instance
storage = StorageManager() 