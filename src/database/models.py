"""
Database Model Definitions - SQLite + SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class User(Base):
    """User table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)  # Password field
    profile_json = Column(Text, nullable=False, default='{}')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Booking(Base):
    """Booking record table"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    booking_reference = Column(String(50), unique=True, nullable=False, index=True)
    restaurant = Column(String(100), nullable=False, default='TheHungryUnicorn')
    visit_date = Column(String(20), nullable=False)  # YYYY-MM-DD format
    visit_time = Column(String(20), nullable=False)  # HH:MM:SS format
    party_size = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='confirmed')  # confirmed, cancelled, updated
    special_requests = Column(Text)
    customer_info_json = Column(Text)  # Store customer information JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bookings")


class ChatSession(Base):
    """Chat session table"""
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_data_json = Column(Text, nullable=False, default='{}')  # Fixed field name to match CRUD operations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class DatabaseManager:
    """Database manager"""
    
    def __init__(self, db_path: str = "data/restaurant_booking.db"):
        self.db_path = db_path
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine and session
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def get_current_timestamp(self):
        """Get current timestamp for updates"""
        return datetime.utcnow()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()