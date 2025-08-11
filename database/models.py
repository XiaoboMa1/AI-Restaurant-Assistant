"""
数据库模型定义 - SQLite + SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    profile_json = Column(Text, nullable=False, default='{}')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class Booking(Base):
    """预订记录表"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    booking_reference = Column(String(50), unique=True, nullable=False, index=True)
    restaurant = Column(String(100), nullable=False, default='TheHungryUnicorn')
    visit_date = Column(String(20), nullable=False)  # YYYY-MM-DD格式
    visit_time = Column(String(20), nullable=False)  # HH:MM:SS格式
    party_size = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default='confirmed')  # confirmed, cancelled, updated
    special_requests = Column(Text)
    customer_info_json = Column(Text)  # 存储客户信息JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="bookings")


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = 'chat_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    history_json = Column(Text, nullable=False, default='[]')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="sessions")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/restaurant_booking.db"):
        self.db_path = db_path
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 创建引擎和会话
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 创建表
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()


# 全局数据库管理器实例
db_manager = DatabaseManager()