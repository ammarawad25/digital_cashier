import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base, Customer, MenuItem, FAQ
from src.services.orchestrator import ConversationOrchestrator
from src.data.seed_data import generate_menu_items, generate_faqs, generate_customers

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    generate_menu_items(session)
    generate_faqs(session)
    
    customer = Customer(
        name="Test Customer",
        phone="+15555555555",
        email="test@example.com"
    )
    session.add(customer)
    session.commit()
    
    yield session
    session.close()

def test_greeting_flow(db_session):
    orchestrator = ConversationOrchestrator(db_session)
    
    response = orchestrator.process_message(
        message="Hello",
        customer_phone="+15555555555"
    )
    
    assert response is not None
    assert response.confidence > 0.6

def test_menu_inquiry_flow(db_session):
    orchestrator = ConversationOrchestrator(db_session)
    
    response = orchestrator.process_message(
        message="What vegan options do you have?",
        customer_phone="+15555555555"
    )
    
    assert response is not None
    assert "vegan" in response.response.lower() or "veggie" in response.response.lower()

def test_faq_flow(db_session):
    orchestrator = ConversationOrchestrator(db_session)
    
    response = orchestrator.process_message(
        message="What are your hours?",
        customer_phone="+15555555555"
    )
    
    assert response is not None
    assert "11am" in response.response or "10pm" in response.response

def test_order_flow(db_session):
    orchestrator = ConversationOrchestrator(db_session)
    
    response = orchestrator.process_message(
        message="I want to order a burger",
        customer_phone="+15555555555"
    )
    
    assert response is not None
    assert "burger" in response.response.lower() or "order" in response.response.lower()
