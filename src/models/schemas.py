from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from .enums import OrderStatus, IssueType, IssueStatus, Sentiment, ConversationState, IntentType

class ConversationRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    customer_phone: Optional[str] = None

class ConversationResponse(BaseModel):
    response: str
    session_id: UUID
    conversation_state: ConversationState
    confidence: float
    intent: IntentType
    order_draft: Optional[Dict] = None
    order_cleared: Optional[bool] = None
    order_number: Optional[str] = None
    receipt_data: Optional[Dict] = None
    
class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    entities: Dict
    sentiment: Sentiment

class OrderDraft(BaseModel):
    items: List[Dict]
    subtotal: float
    tax: float
    delivery_fee: float
    total: float
    
class PolicyResolution(BaseModel):
    can_auto_resolve: bool
    resolution_message: str
    compensation_amount: Optional[float] = None
    requires_escalation: bool

class OrderResponse(BaseModel):
    id: str
    order_number: Optional[str]
    status: OrderStatus
    subtotal: float
    tax: float
    delivery_fee: float
    total: float
    created_at: datetime
    estimated_ready_time: Optional[datetime]
    
    class Config:
        from_attributes = True
