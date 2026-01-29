from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.database import Issue, Order
from src.models.enums import IssueType, IssueStatus, Sentiment
from src.services.resolution_policies import PolicyEngine
from src.services.audit_logger import AuditLogger
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class IssueResolutionAgent:
    """Specialized agent for handling customer complaints and issues
    
    Responsibilities:
    - Classify and categorize issues
    - Apply resolution policies automatically
    - Determine when escalation is needed
    - Track sentiment and customer satisfaction
    """
    
    def __init__(self, db: Session):
        """Initialize issue resolution agent
        
        Args:
            db: SQLAlchemy database session
        """
        try:
            self.db = db
            self.policy_engine = PolicyEngine()
            self.audit_logger = AuditLogger(db)
            logger.info("IssueResolutionAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize IssueResolutionAgent: {e}")
            raise
    
    
    def handle_complaint(self, message: str, customer_id: str, entities: Dict) -> Dict:
        """Handle customer complaint with policy-based resolution
        
        Args:
            message: Customer's complaint message
            customer_id: Customer identifier
            entities: Extracted entities (order_id, etc.)
        
        Returns:
            Dict with success status, message, and resolution details
        """
        try:
            # Validate inputs
            if not message or not message.strip():
                return {
                    "success": False,
                    "message": "يرجى وصف المشكلة لمساعدتك."
                }
            
            if not customer_id:
                logger.error("Missing customer_id in handle_complaint")
                return {
                    "success": False,
                    "message": "عذراً، حدث خطف. يرجى المحاولة مرة أخرى."
                }
            
            # Classify issue type
            issue_type = self._classify_issue(message)
            order_id = entities.get("order_id")
            
            # Find relevant order
            order = None
            try:
                if order_id:
                    order = self.db.query(Order).filter(Order.id == str(order_id)).first()
                else:
                    # Get most recent order for customer
                    order = self.db.query(Order).filter(
                        Order.customer_id == customer_id
                    ).order_by(Order.created_at.desc()).first()
            except SQLAlchemyError as e:
                logger.error(f"Database error finding order: {e}")
            
            if not order:
                return {
                    "success": False,
                    "message": "لم أتمكن من إيجاد طلبك. هل يمكنك تزويدي برقم الطلب؟"
                }
            
            # Apply resolution policy
            try:
                policy_result = self.policy_engine.resolve(
                    issue_type=issue_type,
                    order_total=order.total
                )
            except Exception as e:
                logger.error(f"Policy engine failed: {e}")
                # Fallback to escalation
                return {
                    "success": True,
                    "message": "عذراً على الإزعاج. دعني أحولك إلى مشرف لمساعدتك...",
                    "escalated": True
                }
            
            # Detect sentiment
            sentiment = self._detect_sentiment(message)
            
            # Create issue record with transaction safety
            try:
                issue = Issue(
                    order_id=order.id,
                    customer_id=customer_id,
                    issue_type=issue_type,
                    description=message[:500],  # Limit description length
                    sentiment=sentiment,
                    status=IssueStatus.ESCALATED if policy_result.requires_escalation else IssueStatus.RESOLVED,
                    compensation_amount=policy_result.compensation_amount,
                    resolution=policy_result.resolution_message[:500],  # Limit resolution length
                    resolved_at=datetime.utcnow() if not policy_result.requires_escalation else None
                )
                self.db.add(issue)
                self.db.commit()
                
                # Audit log
                try:
                    self.audit_logger.log(
                        action="issue_resolved" if not policy_result.requires_escalation else "issue_escalated",
                        customer_id=customer_id,
                        details={
                            "issue_id": str(issue.id),
                            "issue_type": issue_type.value,
                            "escalated": policy_result.requires_escalation,
                            "compensation": policy_result.compensation_amount
                        }
                    )
                except Exception as e:
                    logger.warning(f"Audit logging failed: {e}")
                
                if policy_result.requires_escalation:
                    return {
                        "success": True,
                        "message": f"{policy_result.resolution_message}. سيتواصل معك المشرف قريباً.",
                        "escalated": True
                    }
                
                return {
                    "success": True,
                    "message": policy_result.resolution_message,
                    "escalated": False,
                    "compensation": policy_result.compensation_amount
                }
            
            except SQLAlchemyError as e:
                logger.error(f"Database error creating issue: {e}", exc_info=True)
                self.db.rollback()
                return {
                    "success": False,
                    "message": "عذراً، حدث خطأ عند حفظ البلاغ. دعني أحولك إلى موظف...",
                    "escalated": True
                }
        
        except Exception as e:
            logger.error(f"Unexpected error handling complaint: {e}", exc_info=True)
            return {
                "success": False,
                "message": "عذراً على الإزعاج. دعني أحولك إلى مشرف لمساعدتك...",
                "escalated": True
            }
    
    def _classify_issue(self, message: str) -> IssueType:
        message_lower = message.lower()
        
        arabic_missing = ["ناقص", "مافي", "ما في", "نسيتوا", "ما جاء", "ما جا"]
        arabic_wrong = ["غلط", "خطأ", "غير صحيح", "مو صحيح"]
        arabic_late = ["متأخر", "تأخر", "بطيء", "وين الطلب"]
        arabic_quality = ["بارد", "سيء", "رديء", "مو حلو"]
        
        if any(word in message_lower for word in arabic_missing + ["missing", "didn't get", "forgot"]):
            return IssueType.MISSING_ITEM
        elif any(word in message_lower for word in arabic_wrong + ["wrong", "incorrect", "mistake"]):
            return IssueType.WRONG_ORDER
        elif any(word in message_lower for word in arabic_late + ["late", "slow", "delay", "waiting"]):
            return IssueType.LATE_DELIVERY
        elif any(word in message_lower for word in arabic_quality + ["cold", "quality", "bad", "terrible"]):
            return IssueType.QUALITY
        else:
            return IssueType.REFUND_REQUEST
    
    def _detect_sentiment(self, message: str) -> Sentiment:
        message_lower = message.lower()
        
        negative_words = ["terrible", "awful", "disgusting", "angry", "disappointed", "سيء", "رديء", "زعلان", "غاضب", "محبط"]
        if any(word in message_lower for word in negative_words):
            return Sentiment.NEGATIVE
        
        positive_words = ["thanks", "thank you", "appreciate", "great", "شكراً", "شكرا", "ممتاز", "جيد", "رائع"]
        if any(word in message_lower for word in positive_words):
            return Sentiment.POSITIVE
        
        return Sentiment.NEUTRAL
