"""
Consolidated Arabic Language Tests
Tests all 4 priority agents with Arabic natural language
"""
import pytest
from src.services.orchestrator import ConversationOrchestrator
from src.services.order_processing_agent import OrderProcessingAgent
from src.services.issue_resolution_agent import IssueResolutionAgent
from src.services.menu_agent import MenuAgent
from src.services.context_manager import ContextManager
from src.models.db_session import SessionLocal
from src.models.database import Customer
from src.models.enums import IntentType

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def customer(db):
    customer = Customer(
        name="Ahmed Test",
        phone="+966501234567",
        email="ahmed@test.sa"
    )
    db.add(customer)
    db.commit()
    return customer

class TestArabicOrchestrator:
    """Test orchestrator with Arabic inputs"""
    
    def test_arabic_greeting(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        response = orchestrator.process_message("مرحبا", customer.phone)
        
        assert response.intent == IntentType.GREETING
        assert response.confidence >= 0.8
        assert "مرحباً" in response.response or "مساعدتك" in response.response
    
    def test_arabic_order_intent(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        response = orchestrator.process_message("أريد برجر", customer.phone)
        
        assert response.intent == IntentType.ORDERING
        assert response.confidence >= 0.8
    
    def test_arabic_menu_inquiry(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        response = orchestrator.process_message("عندكم أكل نباتي؟", customer.phone)
        
        assert response.intent == IntentType.INQUIRY
        assert response.confidence >= 0.8
    
    def test_arabic_complaint(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        response = orchestrator.process_message("الطلب جاني ناقص", customer.phone)
        
        assert response.intent == IntentType.COMPLAINT
        assert response.confidence >= 0.8
    
    def test_unclear_retry_logic(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        context_manager = ContextManager(db)
        
        # First unclear message
        response1 = orchestrator.process_message("مممم", customer.phone)
        session = context_manager.get_or_create_session(customer.phone)
        
        # Should trigger retry message if confidence is low
        if response1.confidence < 0.6:
            assert "عذراً" in response1.response or "أفهم" in response1.response
            assert session.unclear_count > 0

class TestArabicOrderProcessing:
    """Test order processing with Arabic items"""
    
    def test_single_arabic_item(self, db, customer):
        agent = OrderProcessingAgent(db)
        context_manager = ContextManager(db)
        session = context_manager.get_or_create_session(customer.phone)
        
        result = agent.process_order_request("أريد برجر", session, {"items": ["برجر"]})
        
        assert result["success"] == True
        assert "طلبك" in result["message"]
        assert "burger" in result["message"].lower() or "برجر" in result["message"]
    
    def test_multiple_arabic_items(self, db, customer):
        agent = OrderProcessingAgent(db)
        context_manager = ContextManager(db)
        session = context_manager.get_or_create_session(customer.phone)
        
        result = agent.process_order_request("بدي بيتزا وبطاطس", session, {"items": ["بيتزا", "بطاطس"]})
        
        assert result["success"] == True
        assert "طلبك" in result["message"]
    
    def test_mixed_arabic_english(self, db, customer):
        agent = OrderProcessingAgent(db)
        context_manager = ContextManager(db)
        session = context_manager.get_or_create_session(customer.phone)
        
        result = agent.process_order_request("أريد burger وfries", session, {"items": ["burger", "fries"]})
        
        assert result["success"] == True
    
    def test_different_dialects(self, db, customer):
        agent = OrderProcessingAgent(db)
        context_manager = ContextManager(db)
        session = context_manager.get_or_create_session(customer.phone)
        
        # Gulf Arabic
        result1 = agent.process_order_request("ودي برجر", session, {"items": ["برجر"]})
        assert result1["success"] == True
        
        # Egyptian Arabic  
        result2 = agent.process_order_request("عايز بيتزا", session, {"items": ["بيتزا"]})
        assert result2["success"] == True

class TestArabicIssueResolution:
    """Test issue resolution with Arabic complaints"""
    
    def test_missing_item_arabic(self, db, customer):
        agent = IssueResolutionAgent(db)
        
        # Create a test order first would be needed in real scenario
        result = agent.handle_complaint("الطلب جاني ناقص البطاطس", customer.id, {})
        
        # Should handle gracefully even without order
        assert "لم أتمكن" in result["message"] or result["success"] == True
    
    def test_late_delivery_arabic(self, db, customer):
        agent = IssueResolutionAgent(db)
        result = agent.handle_complaint("الطلب متأخر كثير", customer.id, {})
        
        assert "لم أتمكن" in result["message"] or result["success"] == True
    
    def test_quality_issue_arabic(self, db, customer):
        agent = IssueResolutionAgent(db)
        result = agent.handle_complaint("الأكل جاني بارد ورديء", customer.id, {})
        
        assert "لم أتمكن" in result["message"] or result["success"] == True

class TestArabicMenuAgent:
    """Test menu agent with Arabic queries"""
    
    def test_vegan_query_arabic(self, db):
        agent = MenuAgent(db)
        response = agent.handle_inquiry("عندكم أكل نباتي؟")
        
        assert response is not None
        assert len(response) > 0
    
    def test_pizza_query_arabic(self, db):
        agent = MenuAgent(db)
        response = agent.handle_inquiry("وش عندكم من بيتزا؟")
        
        assert response is not None
        assert "pizza" in response.lower() or "بيتزا" in response.lower()
    
    def test_salad_query_arabic(self, db):
        agent = MenuAgent(db)
        response = agent.handle_inquiry("عندكم سلطات؟")
        
        # Should either find salad or give helpful response
        assert response is not None

class TestArabicEndToEnd:
    """End-to-end Arabic conversation flow"""
    
    def test_complete_order_flow_arabic(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        
        # Greeting
        r1 = orchestrator.process_message("السلام عليكم", customer.phone)
        assert r1.confidence >= 0.8
        
        # Order
        r2 = orchestrator.process_message("أريد برجر من فضلك", customer.phone, r1.session_id)
        assert r2.intent == IntentType.ORDERING
        
    def test_mixed_dialect_conversation(self, db, customer):
        orchestrator = ConversationOrchestrator(db)
        
        # Gulf dialect
        r1 = orchestrator.process_message("وين المنيو؟", customer.phone)
        assert r1.confidence >= 0.7
        
        # Egyptian dialect
        r2 = orchestrator.process_message("عايز أطلب", customer.phone, r1.session_id)
        assert r2.confidence >= 0.7
        
        # Standard Arabic
        r3 = orchestrator.process_message("أريد طعام", customer.phone, r1.session_id)
        assert r3.confidence >= 0.7

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
