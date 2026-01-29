from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"  # Order is ready for pickup/delivery
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class IssueType(str, Enum):
    MISSING_ITEM = "missing_item"
    WRONG_ORDER = "wrong_order"
    LATE_DELIVERY = "late_delivery"
    QUALITY = "quality"
    REFUND_REQUEST = "refund_request"

class IssueStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class ConversationState(str, Enum):
    GREETING = "greeting"
    BROWSING_MENU = "browsing_menu"
    BUILDING_ORDER = "building_order"
    CONFIRMING_ORDER = "confirming_order"
    TRACKING_ORDER = "tracking_order"
    RESOLVING_ISSUE = "resolving_issue"
    ENDED = "ended"

class IntentType(str, Enum):
    GREETING = "greeting"
    INQUIRY = "inquiry"
    ORDERING = "ordering"
    COMPLAINT = "complaint"
    TRACKING = "tracking"
    FAREWELL = "farewell"
    CANCEL = "cancel"
    REMOVE = "remove"
    QUERY_ORDER = "query_order"
    CONFIRM_ORDER = "confirm_order"
    ESCALATE = "escalate"
    UNCLEAR = "unclear"
