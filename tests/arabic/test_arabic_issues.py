"""
Arabic Issue Resolution Tests
Tests complaint handling in Arabic across different scenarios
"""
import pytest
from src.services.issue_resolution_agent import IssueResolutionAgent
from src.models.database import Order, Customer
from src.models.enums import IssueType, Sentiment
from src.models.db_session import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def issue_agent(db):
    return IssueResolutionAgent(db)

@pytest.fixture
def test_order(db):
    """Create a test order"""
    customer = Customer(
        id="test-customer-arabic",
        phone_number="+966501234567",
        name="Test Customer"
    )
    db.add(customer)
    
    order = Order(
        customer_id=customer.id,
        status="delivered",
        subtotal=20.00,
        tax=1.60,
        delivery_fee=4.99,
        total=26.59,
        fulfillment_type="delivery"
    )
    db.add(order)
    db.commit()
    
    return order

class TestArabicIssueClassification:
    """Test issue type classification from Arabic complaints"""
    
    def test_classify_missing_item_arabic(self, issue_agent):
        """Test: الطلب ناقص - Missing item"""
        issue_type = issue_agent._classify_issue("الطلب جاني ناقص البطاطس")
        assert issue_type == IssueType.MISSING_ITEM
    
    def test_classify_missing_item_variants(self, issue_agent):
        """Test various ways to say missing in Arabic"""
        messages = [
            "مافي بطاطس في الطلب",
            "ما جاء البرجر",
            "نسيتوا المشروب"
        ]
        for msg in messages:
            issue_type = issue_agent._classify_issue(msg)
            assert issue_type == IssueType.MISSING_ITEM
    
    def test_classify_late_delivery_arabic(self, issue_agent):
        """Test: الطلب متأخر - Late delivery"""
        issue_type = issue_agent._classify_issue("الطلب متأخر كثير")
        assert issue_type == IssueType.LATE_DELIVERY
    
    def test_classify_late_variants(self, issue_agent):
        """Test various ways to say late in Arabic"""
        messages = [
            "وين الطلب تأخر",
            "الطلب بطيء",
            "متأخر ساعة"
        ]
        for msg in messages:
            issue_type = issue_agent._classify_issue(msg)
            assert issue_type == IssueType.LATE_DELIVERY
    
    def test_classify_wrong_order_arabic(self, issue_agent):
        """Test: الطلب غلط - Wrong order"""
        issue_type = issue_agent._classify_issue("هذا مو طلبي، الطلب غلط")
        assert issue_type == IssueType.WRONG_ORDER
    
    def test_classify_wrong_variants(self, issue_agent):
        """Test various ways to say wrong in Arabic"""
        messages = [
            "الطلب خطأ",
            "غير صحيح",
            "مو صحيح"
        ]
        for msg in messages:
            issue_type = issue_agent._classify_issue(msg)
            assert issue_type == IssueType.WRONG_ORDER
    
    def test_classify_quality_issue_arabic(self, issue_agent):
        """Test: الأكل بارد - Quality issue"""
        issue_type = issue_agent._classify_issue("الأكل جاني بارد ورديء")
        assert issue_type == IssueType.QUALITY
    
    def test_classify_quality_variants(self, issue_agent):
        """Test various quality complaints in Arabic"""
        messages = [
            "الطعام سيء",
            "البرجر بارد",
            "مو حلو"
        ]
        for msg in messages:
            issue_type = issue_agent._classify_issue(msg)
            assert issue_type == IssueType.QUALITY

class TestArabicSentimentDetection:
    """Test sentiment detection in Arabic complaints"""
    
    def test_negative_sentiment_arabic(self, issue_agent):
        """Test negative sentiment detection"""
        sentiment = issue_agent._detect_sentiment("الطلب سيء جداً وأنا زعلان")
        assert sentiment == Sentiment.NEGATIVE
    
    def test_negative_variants(self, issue_agent):
        """Test various negative expressions"""
        messages = [
            "رديء جداً",
            "محبط",
            "غاضب من الخدمة"
        ]
        for msg in messages:
            sentiment = issue_agent._detect_sentiment(msg)
            assert sentiment == Sentiment.NEGATIVE
    
    def test_positive_sentiment_arabic(self, issue_agent):
        """Test positive sentiment detection"""
        sentiment = issue_agent._detect_sentiment("شكراً على الحل السريع، ممتاز")
        assert sentiment == Sentiment.POSITIVE
    
    def test_positive_variants(self, issue_agent):
        """Test various positive expressions"""
        messages = [
            "جيد جداً شكراً",
            "رائع",
            "ممتاز"
        ]
        for msg in messages:
            sentiment = issue_agent._detect_sentiment(msg)
            assert sentiment == Sentiment.POSITIVE
    
    def test_neutral_sentiment_arabic(self, issue_agent):
        """Test neutral sentiment"""
        sentiment = issue_agent._detect_sentiment("الطلب ناقص منتج")
        assert sentiment == Sentiment.NEUTRAL

class TestArabicIssueResolution:
    """Test end-to-end issue resolution with Arabic"""
    
    def test_handle_missing_item_complaint_arabic(self, issue_agent, test_order, db):
        """Test handling missing item in Arabic"""
        result = issue_agent.handle_complaint(
            message="الطلب جاني ناقص البطاطس",
            customer_id=test_order.customer_id,
            entities={"order_id": test_order.id}
        )
        
        assert result["success"] == True
        # Should contain Arabic in response or policy message
        assert "compensation" in result or "escalated" in result
    
    def test_handle_late_delivery_arabic(self, issue_agent, test_order, db):
        """Test handling late delivery in Arabic"""
        result = issue_agent.handle_complaint(
            message="الطلب متأخر ساعة كاملة",
            customer_id=test_order.customer_id,
            entities={"order_id": test_order.id}
        )
        
        assert result["success"] == True
    
    def test_no_order_found_arabic_response(self, issue_agent, db):
        """Test Arabic response when no order found"""
        result = issue_agent.handle_complaint(
            message="الطلب ناقص",
            customer_id="nonexistent-customer",
            entities={}
        )
        
        assert result["success"] == False
        assert "لم أتمكن من إيجاد طلبك" in result["message"]
