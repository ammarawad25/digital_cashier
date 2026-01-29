import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.database import Base, FAQ
from src.services.faq_search import FAQSearch
import json

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    faqs = [
        FAQ(question="What are your hours?", answer="11am-10pm Mon-Fri", category="hours", keywords=json.dumps(["hours", "open", "time"])),
        FAQ(question="Do you deliver?", answer="Yes, within 5 miles", category="delivery", keywords=json.dumps(["deliver", "delivery"])),
        FAQ(question="What payment methods?", answer="Credit, debit, Apple Pay", category="payment", keywords=json.dumps(["payment", "pay", "card"])),
    ]
    for faq in faqs:
        session.add(faq)
    session.commit()
    
    yield session
    session.close()

def test_search_by_keyword(db_session):
    faq_search = FAQSearch(db_session)
    result = faq_search.search("hours")
    
    assert result is not None
    assert "11am-10pm" in result["answer"]

def test_search_delivery(db_session):
    faq_search = FAQSearch(db_session)
    result = faq_search.search("do you deliver")
    
    assert result is not None
    assert "5 miles" in result["answer"]

def test_no_match(db_session):
    faq_search = FAQSearch(db_session)
    result = faq_search.search("nonsense query")
    
    assert result is None
