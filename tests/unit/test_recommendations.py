import pytest
from src.services.recommendations import RecommendationEngine

def test_burger_recommendations():
    engine = RecommendationEngine()
    items = [{"name": "Burger", "category": "Burgers"}]
    recommendations = engine.get_recommendations(items)
    
    assert len(recommendations) > 0
    assert any("Fries" in r or "Soda" in r for r in recommendations)

def test_pizza_recommendations():
    engine = RecommendationEngine()
    items = [{"name": "Pizza", "category": "Pizza"}]
    recommendations = engine.get_recommendations(items)
    
    assert len(recommendations) > 0

def test_no_duplicate_recommendations():
    engine = RecommendationEngine()
    items = [
        {"name": "Burger", "category": "Burgers"},
        {"name": "Fries", "category": "Sides"}
    ]
    recommendations = engine.get_recommendations(items)
    
    assert "Fries" not in recommendations
