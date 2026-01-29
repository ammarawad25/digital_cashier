import pytest
from src.models.enums import IssueType
from src.services.resolution_policies import PolicyEngine

def test_missing_item_auto_resolve():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.MISSING_ITEM, order_total=30.0)
    
    assert result.can_auto_resolve == True
    assert result.compensation_amount == 30.0
    assert result.requires_escalation == False

def test_missing_item_escalate():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.MISSING_ITEM, order_total=75.0)
    
    assert result.requires_escalation == True

def test_late_delivery():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.LATE_DELIVERY, delay_minutes=45, order_total=100.0)
    
    assert result.can_auto_resolve == True
    assert result.compensation_amount == 20.0

def test_late_delivery_no_compensation():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.LATE_DELIVERY, delay_minutes=20, order_total=100.0)
    
    assert result.compensation_amount == 0

def test_wrong_order():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.WRONG_ORDER, order_total=50.0)
    
    assert result.can_auto_resolve == True
    assert result.compensation_amount == 50.0

def test_quality_issue():
    engine = PolicyEngine()
    result = engine.resolve(IssueType.QUALITY, order_total=25.0)
    
    assert result.can_auto_resolve == True
    assert result.compensation_amount == 12.5
