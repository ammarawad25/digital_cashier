from typing import List, Dict

class RecommendationEngine:
    def __init__(self):
        self.rules = {
            "Burgers": ["Fries", "Onion Rings", "Soda", "Milkshake"],
            "Pizza": ["Garlic Bread", "Wings", "Soda", "Salad"],
            "Sides": ["Soda", "Dipping Sauce"],
            "Beverages": ["Dessert"],
        }
    
    def get_recommendations(self, items: List[Dict]) -> List[str]:
        recommendations = []
        existing_items = [item["name"] for item in items]
        
        for item in items:
            category = item.get("category", "")
            if category in self.rules:
                for rec in self.rules[category]:
                    if rec not in existing_items and rec not in recommendations:
                        recommendations.append(rec)
        
        return recommendations[:3]
