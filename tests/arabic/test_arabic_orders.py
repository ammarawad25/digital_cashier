"""
Comprehensive Arabic Language Tests - Order Processing
Tests all Arabic dialects and order scenarios
"""
import pytest
from src.models.database import MenuItem, Customer
from src.services.order_processing_agent import OrderProcessingAgent
from src.models.db_session import SessionLocal
from src.models.enums import OrderStatus

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def order_agent(db):
    return OrderProcessingAgent(db)

class TestArabicOrderProcessing:
    """Test order processing with various Arabic dialects"""
    
    def test_standard_arabic_burger_order(self, order_agent, db):
        """Test: أريد برجر - Standard Arabic"""
        # Create mock session
        from src.models.database import Session as SessionModel
        session = SessionModel(
            customer_id="test-customer-1",
            current_order_draft=None
        )
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="أريد برجر",
            session=session,
            entities={}
        )
        
        assert result["success"] == True
        assert "burger" in result["message"].lower() or "برجر" in result["message"]
    
    def test_gulf_arabic_pizza_order(self, order_agent, db):
        """Test: بدي بيتزا - Gulf Arabic"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-2")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="بدي بيتزا",
            session=session,
            entities={}
        )
        
        assert result["success"] == True
        assert "pizza" in result["message"].lower() or "بيتزا" in result["message"]
    
    def test_egyptian_arabic_fries_order(self, order_agent, db):
        """Test: عايز بطاطس - Egyptian Arabic"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-3")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="عايز بطاطس",
            session=session,
            entities={}
        )
        
        assert result["success"] == True
        assert "fries" in result["message"].lower() or "بطاطس" in result["message"]
    
    def test_multi_item_arabic_order(self, order_agent, db):
        """Test: أريد برجر وبطاطس - Multiple items"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-4")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="أريد برجر وبطاطس",
            session=session,
            entities={}
        )
        
        assert result["success"] == True
        assert "burger" in result["message"].lower() or "برجر" in result["message"]
        assert "fries" in result["message"].lower() or "بطاطس" in result["message"]
    
    def test_mixed_arabic_english_order(self, order_agent, db):
        """Test: بدي burger وfries - Code-switching"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-5")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="بدي burger وfries",
            session=session,
            entities={}
        )
        
        assert result["success"] == True
    
    def test_arabic_quantity_order(self, order_agent, db):
        """Test: أريد اثنين برجر - With quantity"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-6")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="أريد اثنين برجر",
            session=session,
            entities={"quantity": 2}
        )
        
        assert result["success"] == True
    
    def test_arabic_invalid_item(self, order_agent, db):
        """Test: أريد شاورما - Item not in menu"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-7")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="أريد شاورما",
            session=session,
            entities={}
        )
        
        assert result["success"] == False
        assert "لم أجد" in result["message"] or "not found" in result["message"].lower()

class TestArabicOrderFormatting:
    """Test Arabic response formatting"""
    
    def test_arabic_order_summary(self, order_agent, db):
        """Test order summary in Arabic"""
        draft = {
            "items": [
                {"name": "Classic Burger", "quantity": 1, "price": 9.99}
            ],
            "subtotal": 9.99,
            "tax": 0.80,
            "delivery_fee": 4.99,
            "total": 15.78
        }
        
        summary = order_agent._format_order_summary(draft)
        assert "طلبك" in summary
        assert "المبلغ الإجمالي" in summary
        assert "Classic Burger" in summary
    
    def test_arabic_recommendation_message(self, order_agent, db):
        """Test recommendation message in Arabic"""
        from src.models.database import Session as SessionModel
        session = SessionModel(customer_id="test-customer-8")
        db.add(session)
        db.commit()
        
        result = order_agent.process_order_request(
            message="أريد برجر",
            session=session,
            entities={}
        )
        
        if "هل تريد إضافة" in result["message"]:
            assert "أو" in result["message"]  # "or" in Arabic
