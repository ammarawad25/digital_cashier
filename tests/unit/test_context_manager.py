import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base, Customer, Session as SessionModel
from src.models.enums import ConversationState
from src.services.context_manager import ContextManager
from datetime import datetime
import json

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def test_customer(db_session):
    customer = Customer(
        name="Test User",
        phone="+1234567890",
        email="test@example.com"
    )
    db_session.add(customer)
    db_session.commit()
    return customer

def test_create_new_session(db_session, test_customer):
    context_mgr = ContextManager(db_session)
    session = context_mgr.get_or_create_session(test_customer.phone)
    
    assert session is not None
    assert session.customer_id == test_customer.id
    assert session.conversation_state == ConversationState.GREETING
    assert session.conversation_history == "[]"

def test_retrieve_existing_session(db_session, test_customer):
    context_mgr = ContextManager(db_session)
    session1 = context_mgr.get_or_create_session(test_customer.phone)
    session2 = context_mgr.get_or_create_session(test_customer.phone, session1.id)
    
    assert session1.id == session2.id

def test_add_message_to_history(db_session, test_customer):
    context_mgr = ContextManager(db_session)
    session = context_mgr.get_or_create_session(test_customer.phone)
    
    context_mgr.add_message_to_history(session, "user", "Hello")
    context_mgr.add_message_to_history(session, "assistant", "Hi there!")
    
    history = json.loads(session.conversation_history)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"

def test_update_conversation_state(db_session, test_customer):
    context_mgr = ContextManager(db_session)
    session = context_mgr.get_or_create_session(test_customer.phone)
    
    context_mgr.update_conversation_state(session, ConversationState.BUILDING_ORDER)
    
    assert session.conversation_state == ConversationState.BUILDING_ORDER

def test_update_order_draft(db_session, test_customer):
    context_mgr = ContextManager(db_session)
    session = context_mgr.get_or_create_session(test_customer.phone)
    
    order_draft = {"items": [{"name": "Burger", "quantity": 2}], "total": 17.98}
    context_mgr.update_order_draft(session, order_draft)
    
    stored_draft = json.loads(session.current_order_draft)
    assert stored_draft == order_draft
