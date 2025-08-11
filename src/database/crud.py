"""
Database CRUD Operations
"""
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .models import User, Booking, ChatSession, db_manager

# Password encryption context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DatabaseCRUD:
    """Database CRUD operations class"""
    
    # User operations
    def create_user(self, username: str, password: str, profile: Dict[str, Any] = None) -> User:
        """Create user"""
        with db_manager.get_session() as db:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                raise ValueError(f"User {username} already exists")
            
            # Hash password
            hashed_password = pwd_context.hash(password)
            
            user = User(
                username=username,
                hashed_password=hashed_password,
                profile_json=json.dumps(profile or {}, ensure_ascii=False)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
    
    def verify_user(self, username: str, password: str) -> Optional[User]:
        """Verify username and password"""
        with db_manager.get_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None
            
            if not pwd_context.verify(password, user.hashed_password):
                return None
                
            return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with db_manager.get_session() as db:
            return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        with db_manager.get_session() as db:
            return db.query(User).filter(User.id == user_id).first()
    
    def update_user_profile(self, username: str, profile: Dict[str, Any]):
        """Update user profile"""
        with db_manager.get_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise ValueError(f"User {username} does not exist")
            
            user.profile_json = json.dumps(profile, ensure_ascii=False)
            db.commit()
    
    def update_user_password(self, username: str, new_password: str):
        """Update user password"""
        with db_manager.get_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise ValueError(f"User {username} does not exist")
            
            user.hashed_password = pwd_context.hash(new_password)
            db.commit()
    
    def list_users(self) -> List[str]:
        """List all usernames"""
        with db_manager.get_session() as db:
            users = db.query(User.username).all()
            return [user.username for user in users]
    
    def delete_user(self, username: str) -> bool:
        """Delete user account"""
        with db_manager.get_session() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return False
            
            db.delete(user)
            db.commit()
            return True

    # Booking operations
    def create_booking(self, user_id: int, booking_reference: str, 
                      visit_date: str, visit_time: str, party_size: int,
                      status: str = "confirmed", special_requests: str = None,
                      customer_info: Dict[str, Any] = None) -> Booking:
        """Create new booking"""
        with db_manager.get_session() as db:
            booking = Booking(
                user_id=user_id,
                booking_reference=booking_reference,
                visit_date=visit_date,
                visit_time=visit_time,
                party_size=party_size,
                status=status,
                special_requests=special_requests,
                customer_info_json=json.dumps(customer_info or {}, ensure_ascii=False)
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)
            return booking
    
    def get_booking_by_reference(self, booking_reference: str) -> Optional[Booking]:
        """Get booking by reference number"""
        with db_manager.get_session() as db:
            return db.query(Booking).filter(Booking.booking_reference == booking_reference).first()
    
    def get_user_bookings(self, user_id: int) -> List[Booking]:
        """Get all bookings for user"""
        with db_manager.get_session() as db:
            return db.query(Booking).filter(Booking.user_id == user_id).all()
    
    def update_booking(self, booking_reference: str, **kwargs) -> bool:
        """Update booking"""
        with db_manager.get_session() as db:
            booking = db.query(Booking).filter(Booking.booking_reference == booking_reference).first()
            if not booking:
                return False
            
            for key, value in kwargs.items():
                if hasattr(booking, key) and key != 'id':
                    setattr(booking, key, value)
            
            db.commit()
            return True
    
    def delete_booking(self, booking_reference: str) -> bool:
        """Delete booking"""
        with db_manager.get_session() as db:
            booking = db.query(Booking).filter(Booking.booking_reference == booking_reference).first()
            if not booking:
                return False
            
            db.delete(booking)
            db.commit()
            return True
    
    # Chat session operations
    def save_chat_session(self, user_id: int, session_data: Dict[str, Any]):
        """Save chat session"""
        with db_manager.get_session() as db:
            # Check if session exists
            session = db.query(ChatSession).filter(ChatSession.user_id == user_id).first()
            
            if session:
                # Update existing session
                session.session_data_json = json.dumps(session_data, ensure_ascii=False)
                session.updated_at = db_manager.get_current_timestamp()
            else:
                # Create new session
                session = ChatSession(
                    user_id=user_id,
                    session_data_json=json.dumps(session_data, ensure_ascii=False)
                )
                db.add(session)
            
            db.commit()
    
    def get_chat_session(self, user_id: int) -> Dict[str, Any]:
        """Get chat session"""
        with db_manager.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.user_id == user_id).first()
            if session:
                return json.loads(session.session_data_json)
            return {}
    
    def clear_chat_session(self, user_id: int):
        """Clear chat session"""
        with db_manager.get_session() as db:
            session = db.query(ChatSession).filter(ChatSession.user_id == user_id).first()
            if session:
                db.delete(session)
                db.commit()


# Global CRUD instance
crud = DatabaseCRUD() 