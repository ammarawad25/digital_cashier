from sqlalchemy.orm import Session
from src.models.database import FAQ
from typing import Optional, Dict
import json

class FAQSearch:
    def __init__(self, db: Session):
        self.db = db
    
    def search(self, query: str) -> Optional[Dict]:
        query_lower = query.lower()
        
        faqs = self.db.query(FAQ).all()
        
        for faq in faqs:
            keywords = json.loads(faq.keywords)
            if any(keyword in query_lower for keyword in keywords):
                faq.usage_count += 1
                self.db.commit()
                return {
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }
            
            if query_lower in faq.question.lower():
                faq.usage_count += 1
                self.db.commit()
                return {
                    "question": faq.question,
                    "answer": faq.answer,
                    "category": faq.category
                }
        
        return None
