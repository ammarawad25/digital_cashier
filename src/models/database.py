from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import json
from .enums import OrderStatus, IssueType, IssueStatus, Sentiment, ConversationState

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True)
    loyalty_points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")
    sessions = relationship("Session", back_populates="customer")
    issues = relationship("Issue", back_populates="customer")

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    arabic_name = Column(String, nullable=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    dietary_tags = Column(Text, default="[]")
    allergens = Column(Text, default="[]")
    is_available = Column(Boolean, default=True)
    brand = Column(String, nullable=False)
    
    order_items = relationship("OrderItem", back_populates="menu_item")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    fulfillment_type = Column(String, nullable=False)
    order_number = Column(String, nullable=True)  # Readable order number like BRG-20260127-1234
    delivery_address = Column(String)
    estimated_ready_time = Column(DateTime)  # When order will be ready
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(String(36), ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    customizations = Column(Text, default="{}")
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    issue_type = Column(SQLEnum(IssueType), nullable=False)
    description = Column(Text, nullable=False)
    resolution = Column(Text)
    status = Column(SQLEnum(IssueStatus), default=IssueStatus.OPEN)
    sentiment = Column(SQLEnum(Sentiment), default=Sentiment.NEUTRAL)
    compensation_amount = Column(Float)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="issues")
    customer = relationship("Customer", back_populates="issues")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"))
    channel = Column(String, default="voice")
    conversation_history = Column(Text, default="[]")
    current_order_draft = Column(Text)
    conversation_state = Column(SQLEnum(ConversationState), default=ConversationState.GREETING)
    unclear_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=2))
    
    customer = relationship("Customer", back_populates="sessions")

class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    question = Column(String, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    keywords = Column(Text, default="[]")
    brand = Column(String)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(String(36))
    session_id = Column(String(36))
    action = Column(String, nullable=False)
    details = Column(Text, default="{}")
    performed_by = Column(String, default="system")
    severity = Column(String, default="info")
