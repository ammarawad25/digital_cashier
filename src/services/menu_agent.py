from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.database import MenuItem
from src.services.faq_search import FAQSearch
from typing import List, Dict, Optional
import logging
import json
import time
from langchain_openai import ChatOpenAI
from src.config import settings

logger = logging.getLogger(__name__)

# Singleton LLM instance for menu agent  
_menu_llm_instance = None

# Menu cache for avoiding repeated database queries
_menu_cache = {
    "items": None,
    "timestamp": 0,
    "ttl": 300  # 5 minutes cache
}

def _get_menu_llm():
    """Get singleton LLM for menu agent"""
    global _menu_llm_instance
    if _menu_llm_instance is None:
        logger.info(f"Initializing menu agent LLM: {settings.llm_model}")
        _menu_llm_instance = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.2,  # Lower for speed
            timeout=6,  # Aggressive timeout
            max_tokens=350,  # Tighter limit
            streaming=True
        )
    return _menu_llm_instance


class MenuAgent:
    """Optimized menu agent for fast menu inquiries"""
    
    def __init__(self, db: Session):
        """Initialize menu agent"""
        try:
            self.db = db
            self.faq_search = FAQSearch(db)
            
            # Use singleton LLM for simple classification
            self.llm = _get_menu_llm()
            
            # Additional menu items (static data for performance)
            self.additional_menu_items = [
                {"name": "Double Cheeseburger", "arabic_name": "برجر مزدوج بالجبنة", "price": 13.99, "category": "Burgers"},
                {"name": "Spicy Chicken Burger", "arabic_name": "برجر دجاج حار", "price": 11.99, "category": "Burgers"},
                {"name": "Mushroom Swiss Burger", "arabic_name": "برجر فطر سويسري", "price": 12.49, "category": "Burgers"},
                {"name": "Crispy Chicken Strips", "arabic_name": "أصابع دجاج مقرمشة", "price": 9.99, "category": "Sides"},
                {"name": "Loaded Fries", "arabic_name": "بطاطس محملة", "price": 6.99, "category": "Sides"},
                {"name": "Cheese Sticks", "arabic_name": "أصابع الجبنة", "price": 5.99, "category": "Sides"},
                {"name": "CaeSAR Salad", "arabic_name": "سلطة سيزر", "price": 7.99, "category": "Salads"},
                {"name": "Greek Salad", "arabic_name": "سلطة يونانية", "price": 8.49, "category": "Salads"},
                {"name": "Chocolate Shake", "arabic_name": "ميلك شيك شوكولاتة", "price": 5.49, "category": "Beverages"},
                {"name": "Strawberry Shake", "arabic_name": "ميلك شيك فراولة", "price": 5.49, "category": "Beverages"},
                {"name": "Iced Coffee", "arabic_name": "قهوة مثلجة", "price": 3.99, "category": "Beverages"},
                {"name": "Chicken Nuggets", "arabic_name": "ناجتس دجاج", "price": 8.99, "category": "Sides"},
                {"name": "Fish Burger", "arabic_name": "برجر سمك", "price": 10.49, "category": "Burgers"},
                {"name": "Lamb Burger", "arabic_name": "برجر لحم ضأن", "price": 14.99, "category": "Burgers"},
            ]
            
            logger.info("MenuAgent initialized (optimized)")
        except Exception as e:
            logger.error("Failed to initialize MenuAgent: %s", e)
            raise
    
    def _get_cached_menu_items(self) -> Optional[List]:
        """Get menu items from cache or database"""
        global _menu_cache
        current_time = time.time()
        
        if _menu_cache["items"] is not None and (current_time - _menu_cache["timestamp"]) < _menu_cache["ttl"]:
            return _menu_cache["items"]
        
        # Refresh cache
        try:
            items = self.db.query(MenuItem).filter(MenuItem.is_available == True).all()
            _menu_cache["items"] = items
            _menu_cache["timestamp"] = current_time
            return items
        except SQLAlchemyError as e:
            logger.error(f"Error fetching menu items: {e}")
            return _menu_cache["items"]  # Return stale cache if available

    def handle_inquiry(self, query: str) -> str:
        """Handle menu inquiry using optimized direct processing"""
        try:
            if not query or not query.strip():
                return "ماذا تريد أن تعرف عن المنيو الخاص بنا"
            
            # Direct analysis for common patterns (faster than agent)
            query_lower = query.lower()
            
            # Popular items queries
            if any(word in query_lower for word in ["مطلوب", "اكثر", "شعبي", "مشهور", "أفضل", "popular", "most", "requested", "best"]):
                return self._get_popular_items()
            
            # Location queries
            elif any(word in query_lower for word in ["موقع", "عنوان", "مكان", "وين", "location", "address", "where"]):
                return self._get_restaurant_info("location")
            
            # Hours queries
            elif any(word in query_lower for word in ["ساعات", "مفتوح", "مغلق", "اوقات", "hours", "open", "close"]):
                return self._get_restaurant_info("hours")
            
            # Phone queries
            elif any(word in query_lower for word in ["هاتف", "تلفون", "رقم", "phone", "contact", "call"]):
                return self._get_restaurant_info("phone")
            
            # Full menu queries
            elif any(word in query_lower for word in ["منيو", "menu", "عندكم", "ايش عندكم", "وش عندكم", "كل شي"]):
                return self._get_full_menu()
            
            # Specific food search
            elif any(word in query_lower for word in ["برجر", "بيتزا", "دجاج", "سلطة", "burger", "pizza", "chicken", "salad", "fries", "بطاطس"]):
                return self._search_menu(query)
            
            # FAQ search for everything else
            else:
                return self._search_faq_or_fallback(query)
                
        except Exception as e:
            logger.error("Menu inquiry error: %s", e)
            return "عذراً، حدث خطأ. يمكنك السؤال عن المنيو أو موقع المطعم."
    
    def _search_faq_or_fallback(self, query: str) -> str:
        """Search FAQ or provide fallback response"""
        try:
            result = self.faq_search.search(query)
            if result:
                return result["answer"]
        except Exception:
            pass
        
        return "عذراً، لم أتمكن من فهم طلبك. يمكنك السؤال عن:\n• المنيو والأطباق\n• موقع المطعم\n• ساعات العمل\n• أرقام التواصل"
    
    def _get_popular_items(self) -> str:
        """Get popular items directly"""
        return """🏆 الأطباق الأكثر شعبية:

1. برجر كلاسيكي - الطبق الأشهر عندنا
2. برجر دجاج حار - محبوب جداً 
3. بطاطس مقرمشة - لا غنى عنها
4. ميلك شيك شوكولاتة - مشروب لذيذ
5. أصابع دجاج مقرمشة - خيار ممتاز

هذه الأطباق هي الأكثر طلباً من عملائنا! هل تريد تجربة أحدها؟"""

    def _get_full_menu(self) -> str:
        """Get full menu efficiently"""
        try:
            # Get database items (limited for performance)
            db_items = self._get_cached_menu_items()[:15]
            
            # Combine with static items
            all_items = []
            
            # Add database items
            for item in db_items:
                all_items.append({
                    "name": item.arabic_name or item.name,
                    "price": item.price,
                    "category": item.category
                })
            
            # Add static popular items
            for item in self.additional_menu_items[:8]:
                all_items.append({
                    "name": item["arabic_name"],
                    "price": item["price"], 
                    "category": item["category"]
                })
            
            # Group by category
            categories = {}
            for item in all_items:
                cat = item["category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            # Build response
            response = "🍽️ منيو برجريزر:\n\n"
            for category in sorted(categories.keys()):
                response += f"📋 {category}:\n"
                for item in categories[category][:4]:  # Limit per category
                    response += f"• {item['name']} - {item['price']:.2f} SAR\n"
                response += "\n"
            
            response += "يمكنك طلب أي من هذه الأطباق! 🍔"
            return response
            
        except Exception as e:
            logger.error(f"Error getting full menu: {e}")
            return "عذراً، حدث خطأ في تحميل المنيو. يرجى المحاولة مرة أخرى."
    
    def _search_menu(self, query: str) -> str:
        """Search menu items and format response"""
        try:
            query_lower = query.lower()
            matches = []
            
            # Search database items
            items = self._get_cached_menu_items()
            for item in items:
                if (query_lower in item.name.lower() or 
                    query_lower in (item.arabic_name or "").lower() or
                    query_lower in item.category.lower()):
                    matches.append({
                        "name": item.arabic_name or item.name,
                        "price": item.price,
                        "category": item.category
                    })
            
            # Search static items
            for item in self.additional_menu_items:
                if (query_lower in item["name"].lower() or
                    query_lower in item["arabic_name"].lower() or
                    query_lower in item["category"].lower()):
                    matches.append({
                        "name": item["arabic_name"],
                        "price": item["price"],
                        "category": item["category"]
                    })
            
            # Format response
            if not matches:
                return f"لم أجد '{query}' في المنيو. جرب البحث عن: برجر، دجاج، بطاطس، سلطة"
            
            if len(matches) == 1:
                item = matches[0]
                return f"✅ {item['name']} متوفر بسعر {item['price']:.2f} SAR"
            
            response = f"🔍 نتائج البحث عن '{query}':\n\n"
            for idx, item in enumerate(matches[:5], 1):
                response += f"{idx}. {item['name']} - {item['price']:.2f} SAR\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error searching menu: {e}")
            return "عذراً، حدث خطأ في البحث. جرب مرة أخرى."
    
    def _get_restaurant_info(self, info_type: str) -> str:
        """Get restaurant information by type"""
        if info_type == "location":
            return "📍 موقع برجريزر:\nالرياض، حي النخيل، شارع الملك فهد\nKing Fahd Road, Al Nakheel District, Riyadh"
        
        elif info_type == "hours":
            return "🕒 ساعات العمل:\nيومياً من 10 صباحاً إلى 12 منتصف الليل\nDaily from 10 AM to 12 AM"
        
        elif info_type == "phone":
            return "📞 رقم التواصل:\n+966 11 123 4567\n\nيمكنك الاتصال للطلب أو الاستفسار!"
        
        else:
            return """📍 معلومات المطعم:

🏪 الموقع: الرياض، حي النخيل، شارع الملك فهد  
🕒 ساعات العمل: 10 صباحاً - 12 منتصف الليل
📞 الهاتف: +966 11 123 4567
🚗 مواقف مجانية متوفرة
🛵 توصيل مجاني للطلبات أكثر من 50 SAR"""

    def _get_cached_menu_items(self) -> List:
        """Get cached menu items for performance"""
        try:
            cache_key = "menu_items"
            cached_items = getattr(self, '_menu_cache', None)
            if cached_items:
                return cached_items
                
            items = self.db.query(MenuItem).filter(
                MenuItem.is_available == True
            ).order_by(MenuItem.category, MenuItem.price).all()
            
            self._menu_cache = items
            return items
        except Exception:
            return []
