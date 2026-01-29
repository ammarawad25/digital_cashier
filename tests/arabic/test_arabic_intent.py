"""
Arabic Intent Detection Tests
Tests LLM's ability to understand Arabic across different dialects
"""
import pytest
from src.services.intent_detection import IntentDetection
from src.models.enums import IntentType, Sentiment
from src.models.db_session import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def intent_service(db):
    return IntentDetection(db)

class TestArabicIntentDetection:
    """Test intent detection for Arabic messages"""
    
    def test_arabic_greeting_intent(self, intent_service):
        """Test: مرحبا - Greeting"""
        result = intent_service.detect("مرحبا")
        assert result.intent == IntentType.GREETING
        assert result.confidence > 0.7
    
    def test_arabic_salam_greeting(self, intent_service):
        """Test: السلام عليكم - Islamic greeting"""
        result = intent_service.detect("السلام عليكم")
        assert result.intent == IntentType.GREETING
        assert result.confidence > 0.7
    
    def test_arabic_order_intent_standard(self, intent_service):
        """Test: أريد برجر - Standard Arabic order"""
        result = intent_service.detect("أريد برجر")
        assert result.intent == IntentType.ORDERING
        assert result.confidence > 0.7
        assert "items" in result.entities or "برجر" in str(result.entities)
    
    def test_arabic_order_intent_gulf(self, intent_service):
        """Test: بدي بيتزا - Gulf dialect order"""
        result = intent_service.detect("بدي بيتزا")
        assert result.intent == IntentType.ORDERING
        assert result.confidence > 0.7
    
    def test_arabic_order_intent_egyptian(self, intent_service):
        """Test: عايز بطاطس - Egyptian dialect order"""
        result = intent_service.detect("عايز بطاطس")
        assert result.intent == IntentType.ORDERING
        assert result.confidence > 0.7
    
    def test_arabic_inquiry_menu(self, intent_service):
        """Test: عندكم أكل نباتي؟ - Menu inquiry"""
        result = intent_service.detect("عندكم أكل نباتي؟")
        assert result.intent == IntentType.INQUIRY
        assert result.confidence > 0.7
    
    def test_arabic_inquiry_hours(self, intent_service):
        """Test: شو ساعات العمل؟ - Hours inquiry"""
        result = intent_service.detect("شو ساعات العمل؟")
        assert result.intent == IntentType.INQUIRY
        assert result.confidence > 0.7
    
    def test_arabic_complaint_missing(self, intent_service):
        """Test: الطلب جاني ناقص - Missing item complaint"""
        result = intent_service.detect("الطلب جاني ناقص البطاطس")
        assert result.intent == IntentType.COMPLAINT
        assert result.confidence > 0.7
        assert result.sentiment in [Sentiment.NEGATIVE, Sentiment.NEUTRAL]
    
    def test_arabic_complaint_late(self, intent_service):
        """Test: الطلب متأخر - Late delivery"""
        result = intent_service.detect("الطلب متأخر كثير")
        assert result.intent in [IntentType.COMPLAINT, IntentType.TRACKING]
        assert result.confidence > 0.7
    
    def test_arabic_complaint_quality(self, intent_service):
        """Test: الأكل بارد - Quality complaint"""
        result = intent_service.detect("الأكل جاني بارد ورديء")
        assert result.intent == IntentType.COMPLAINT
        assert result.confidence > 0.7
        assert result.sentiment == Sentiment.NEGATIVE
    
    def test_arabic_tracking_gulf(self, intent_service):
        """Test: وين طلبي - Gulf tracking question"""
        result = intent_service.detect("وين طلبي")
        assert result.intent == IntentType.TRACKING
        assert result.confidence > 0.7
    
    def test_arabic_tracking_standard(self, intent_service):
        """Test: متى يصل الطلب - Standard tracking"""
        result = intent_service.detect("متى يصل الطلب")
        assert result.intent == IntentType.TRACKING
        assert result.confidence > 0.7
    
    def test_mixed_arabic_english(self, intent_service):
        """Test: بدي burger وfries - Code-switching"""
        result = intent_service.detect("بدي burger وfries")
        assert result.intent == IntentType.ORDERING
        assert result.confidence > 0.7

class TestArabicSentimentDetection:
    """Test sentiment detection for Arabic"""
    
    def test_positive_arabic_sentiment(self, intent_service):
        """Test: ممتاز شكراً - Positive sentiment"""
        result = intent_service.detect("ممتاز شكراً على الخدمة")
        assert result.sentiment == Sentiment.POSITIVE
    
    def test_negative_arabic_sentiment(self, intent_service):
        """Test: سيء جداً - Negative sentiment"""
        result = intent_service.detect("الطلب سيء جداً وأنا زعلان")
        assert result.sentiment == Sentiment.NEGATIVE
    
    def test_neutral_arabic_sentiment(self, intent_service):
        """Test: أريد طلب - Neutral sentiment"""
        result = intent_service.detect("أريد تقديم طلب")
        assert result.sentiment == Sentiment.NEUTRAL

class TestArabicEntityExtraction:
    """Test entity extraction from Arabic messages"""
    
    def test_extract_food_items_arabic(self, intent_service):
        """Test extracting Arabic food item names"""
        result = intent_service.detect("أريد برجر بالجبنة وبيتزا")
        # Should extract items in some form
        assert result.entities is not None
        assert result.intent == IntentType.ORDERING
    
    def test_extract_quantity_arabic(self, intent_service):
        """Test extracting quantities from Arabic"""
        result = intent_service.detect("عايز اثنين برجر")
        assert result.intent == IntentType.ORDERING
    
    def test_extract_multiple_items(self, intent_service):
        """Test extracting multiple items"""
        result = intent_service.detect("بدي برجر وبطاطس ومشروب")
        assert result.intent == IntentType.ORDERING
        assert result.confidence > 0.7
