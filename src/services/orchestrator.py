# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from src.models.schemas import ConversationResponse, IntentResult
from src.models.enums import IntentType, ConversationState, Sentiment
from src.services.context_manager import ContextManager
from src.services.intent_detection import IntentDetection
from src.services.menu_agent import MenuAgent
from src.services.order_processing_agent import OrderProcessingAgent
from src.services.issue_resolution_agent import IssueResolutionAgent
from src.services.audit_logger import AuditLogger
from src.config import settings
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Main orchestrator for multi-agent conversation system
    
    Responsibilities:
    - Route messages to appropriate specialized agents
    - Manage conversation state and context
    - Handle error recovery and fallbacks
    - Ensure data consistency across agents
    """
    
    def __init__(self, db: Session):
        """Initialize orchestrator with all required agents
        
        Args:
            db: SQLAlchemy database session
        """
        try:
            self.db = db
            self.context_manager = ContextManager(db)
            self.intent_detection = IntentDetection(db)
            self.menu_agent = MenuAgent(db)
            self.order_agent = OrderProcessingAgent(db)
            self.issue_agent = IssueResolutionAgent(db)
            self.audit_logger = AuditLogger(db)
            
            logger.info("ConversationOrchestrator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationOrchestrator: {e}")
            raise
    
    def _sanitize_input(self, message: str) -> str:
        """Sanitize and clean user input"""
        message = ' '.join(message.split())
        return message.strip()
    
    def _has_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        return any('\u0600' <= char <= '\u06FF' for char in text)
    
    def process_message(
        self,
        message: str,
        customer_phone: str,
        session_id: Optional[str] = None,
        language: str = "ar"
    ) -> ConversationResponse:
        """Process customer message through multi-agent system
        
        Args:
            message: Customer's message text
            customer_phone: Customer phone number for identification
            session_id: Optional session ID for continuation
            language: Language code (default: "ar" for Arabic)
        
        Returns:
            ConversationResponse with agent's response and metadata
        """
        try:
            # Input validation
            if not message or not message.strip():
                logger.warning("Empty message received")
                return ConversationResponse(
                    response="عذراً، لم أتلق أي رسالة. هل يمكنك إعادة المحاولة؟" if language == "ar" else "Sorry, I didn't receive your message. Can you try again?",
                    session_id=session_id or "",
                    conversation_state=ConversationState.GREETING,
                    confidence=0.0,
                    intent=IntentType.UNCLEAR
                )
            
            if not customer_phone:
                logger.error("Missing customer phone")
                raise ValueError("customer_phone is required")
            
            # Sanitize input
            message = self._sanitize_input(message)
            
            # Get or create session with error handling
            try:
                session = self.context_manager.get_or_create_session(customer_phone, session_id)
            except Exception as e:
                logger.error(f"Session creation failed: {e}")
                raise
            
            # Add message to history
            self.context_manager.add_message_to_history(session, "user", message)
            
            # 🚀 OPTIMIZED: Direct processing without extra LLM analysis call
            # The intent detection already does classification - no need for separate query analysis
            try:
                response = self._process_simple_query(message, session, language)
                
                # Add response to history
                self.context_manager.add_message_to_history(session, "assistant", response.response)
                return response
                
            except Exception as processing_error:
                logger.warning(f"Query processing failed: {processing_error}")
                # Return fallback response
                fallback_msg = "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى." if language == "ar" else "Sorry, an error occurred. Please try again."
                return ConversationResponse(
                    response=fallback_msg,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=0.0,
                    intent=IntentType.UNCLEAR
                )
        
        except Exception as e:
            logger.error(f"Critical error in process_message: {e}", exc_info=True)
            # Return safe fallback response
            return ConversationResponse(
                response="عذراً، حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى." if language == "ar" else "Sorry, an unexpected error occurred. Please try again.",
                session_id=session_id or "",
                conversation_state=ConversationState.GREETING,
                confidence=0.0,
                intent=IntentType.UNCLEAR
            )
    
    def _process_simple_query(self, message: str, session, language: str = "ar") -> ConversationResponse:
        """Process a single query using the original orchestrator logic"""
        try:
            # Get conversation history for context (OPTIMIZED: Only last 4 messages)
            conversation_history_full = json.loads(session.conversation_history)
            conversation_history = conversation_history_full[-4:] if len(conversation_history_full) > 4 else conversation_history_full
            
            # Build session context for context-aware intent detection
            session_context = {
                "has_order_draft": bool(session.current_order_draft),
                "order_items_count": 0,
                "conversation_state": session.conversation_state.value if session.conversation_state else "unknown"
            }
            if session.current_order_draft:
                try:
                    draft = json.loads(session.current_order_draft)
                    session_context["order_items_count"] = len(draft.get("items", []))
                except:
                    pass
            
            # Detect intent with fallback handling and context awareness
            try:
                intent_result = self.intent_detection.detect(message, conversation_history, session_context)
            except Exception as e:
                logger.error(f"Intent detection failed: {e}")
                # Fallback to unclear intent
                intent_result = IntentResult(
                    intent=IntentType.UNCLEAR,
                    confidence=0.0,
                    entities={},
                    sentiment=Sentiment.NEUTRAL
                )
            
            # Handle low confidence with escalation logic
            if intent_result.confidence < settings.escalation_threshold:
                return self._handle_unclear_intent(session, intent_result, language)
            
            # Reset unclear count on successful intent detection
            if session.unclear_count and session.unclear_count > 0:
                session.unclear_count = 0
                self.db.commit()
            
            # Route to appropriate agent
            return self._route_to_agent(intent_result, message, session, language)
            
        except Exception as e:
            logger.error(f"Simple query processing failed: {e}")
            error_response = "عذراً، حدث خطأ. يرجى المحاولة مرة أخرى." if language == "ar" else "Sorry, an error occurred. Please try again."
            return ConversationResponse(
                response=error_response,
                session_id=session.id,
                conversation_state=session.conversation_state,
                confidence=0.0,
                intent=IntentType.UNCLEAR
            )
    
    def _handle_unclear_intent(self, session, intent_result, language: str) -> ConversationResponse:
        """Handle unclear intent with escalation tracking and smart clarification"""
        session.unclear_count = (session.unclear_count or 0) + 1
        self.db.commit()
        
        # Provide context-aware clarification based on partial understanding
        partial_intent = intent_result.intent if intent_result.confidence > 0.3 else None
        
        if language == "ar":
            if session.unclear_count == 1:
                # First attempt - be helpful and provide context
                if partial_intent == IntentType.ORDERING:
                    message = """عذراً، لم أفهم تماماً ما تريد طلبه. 

يمكنك قول:
• "بدي برجر كلاسيكي"
• "أريد بيتزا بيبروني وبطاطس"
• "أطلب وجبة دجاج"

ما الذي تريد طلبه؟"""
                elif partial_intent == IntentType.INQUIRY:
                    message = """عذراً، لم أفهم استفسارك بوضوح.

يمكنك السؤال عن:
• المنيو والأطباق المتوفرة
• الأسعار
• موقع المطعم وساعات العمل
• معلومات التوصيل

ماذا تريد أن تعرف؟"""
                elif partial_intent == IntentType.TRACKING:
                    message = """عذراً، لم أفهم ما تريد تتبعه.

للاستفسار عن طلبك:
• "وين طلبي؟"
• "كم باقي على الطلب؟"
• "حالة الطلب رقم 12345"

ما هو رقم طلبك أو ماذا تريد أن تعرف؟"""
                else:
                    message = """عذراً، لم أفهم طلبك بوضوح. 

هل يمكنك إعادة صياغته بطريقة أخرى؟

مثلاً:
• أريد برجر وبطاطس (للطلب)
• ما هي الوجبات المتاحة؟ (للاستفسار)
• أين طلبي؟ (للتتبع)"""
            
            elif session.unclear_count == 2:
                # Second attempt - be more specific
                message = """آسف، ما زلت غير متأكد مما تريد. 

حاول أن تكون أكثر تحديداً:
• للطلب: اذكر أسماء الأطباق مباشرة
• للاستفسار: اسأل عن المنيو أو الأسعار أو الموقع
• للتتبع: اذكر رقم الطلب أو قل "وين طلبي"

ماذا تريد بالضبط؟"""
            
            else:
                # Third attempt - escalate
                message = """معذرة، أواجه صعوبة في فهمك. 

هل تريد التحدث مع موظف خدمة العملاء؟ 
قل "موظف" أو "تحويل لموظف" وسأحولك فوراً."""
        
        else:  # English
            if session.unclear_count == 1:
                if partial_intent == IntentType.ORDERING:
                    message = """Sorry, I didn't fully understand what you want to order.

You can say:
• "I want a classic burger"
• "Order pepperoni pizza and fries"
• "Get me a chicken meal"

What would you like to order?"""
                elif partial_intent == IntentType.INQUIRY:
                    message = """Sorry, I didn't understand your question clearly.

You can ask about:
• Menu and available dishes
• Prices
• Restaurant location and hours
• Delivery information

What would you like to know?"""
                elif partial_intent == IntentType.TRACKING:
                    message = """Sorry, I didn't understand what you want to track.

To check your order:
• "Where is my order?"
• "Order status for #12345"
• "How long until my order is ready?"

What's your order number or what do you want to know?"""
                else:
                    message = """Sorry, I didn't understand your request clearly.

Could you rephrase it?

For example:
• "I want a burger and fries" (to order)
• "What's on the menu?" (to inquire)
• "Where is my order?" (to track)"""
            
            elif session.unclear_count == 2:
                message = """I'm still not sure what you need.

Please be more specific:
• For ordering: Mention dish names directly
• For questions: Ask about menu, prices, or location
• For tracking: Provide your order number

What exactly do you need?"""
            
            else:
                message = """I'm having difficulty understanding you.

Would you like to speak with a customer service representative?
Say "agent" or "transfer to human" and I'll connect you."""
        
        return ConversationResponse(
            response=message,
            session_id=session.id,
            conversation_state=session.conversation_state,
            confidence=intent_result.confidence,
            intent=IntentType.UNCLEAR
        )
    
    def _route_to_agent(self, intent_result: IntentResult, message: str, session, language: str) -> ConversationResponse:
        """Route message to appropriate agent based on intent"""
        try:
            # Check if this is first message (show welcome)
            conversation_history = self.context_manager.get_conversation_history(session, limit=1)
            if not conversation_history or len(conversation_history) == 0:
                # First interaction - show welcome message
                if language == "ar":
                    welcome_text = """مرحباً! أهلاً بك في خدمة برجريزر للطلبات.

أنا هنا لمساعدتك في:
- تقديم طلب طعام
- الاستفسار عن المنيو
- تتبع طلبك
- الإبلاغ عن مشكلة

كيف يمكنني مساعدتك اليوم؟"""
                else:
                    welcome_text = """Welcome to Burgerizzer ordering service.

I'm here to help you with:
- Placing food orders
- Menu inquiries
- Tracking your order
- Reporting issues

How can I help you today?"""
                
                self.context_manager.add_message_to_history(session, "assistant", welcome_text)
                self.context_manager.update_conversation_state(session, ConversationState.GREETING)
                return ConversationResponse(
                    response=welcome_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=1.0,
                    intent=IntentType.GREETING
                )
            
            if intent_result.intent == IntentType.GREETING:
                self.context_manager.update_conversation_state(session, ConversationState.GREETING)
                if language == "ar":
                    response_text = """مرحباً!  أهلاً بك في خدمة الطلبات.

كيف يمكنني مساعدتك اليوم؟

 تقديم طلب طعام
 الاستفسار عن المنيو
 تتبع طلبك
 الإبلاغ عن مشكلة

قل لي ماذا تحتاج!"""
                else:
                    response_text = """Hello!  Welcome to our ordering service.

How can I help you today?

 Place a food order
 Inquire about menu
 Track your order
 Report an issue

Let me know what you need!"""
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
            
            elif intent_result.intent == IntentType.INQUIRY:
                try:
                    self.context_manager.update_conversation_state(session, ConversationState.BROWSING_MENU)
                    response_text = self.menu_agent.handle_inquiry(message)
                    self.context_manager.add_message_to_history(session, "assistant", response_text)
                    return ConversationResponse(
                        response=response_text,
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=intent_result.confidence,
                        intent=intent_result.intent
                    )
                except Exception as e:
                    logger.error(f"Menu agent failed: {e}")
                    fallback = "عذراً، حدث خطأ عند البحث في المنيو. هل يمكنك المحاولة مرة أخرى؟" if language == "ar" else "Sorry, error searching menu. Can you try again?"
                    self.context_manager.add_message_to_history(session, "assistant", fallback)
                    return ConversationResponse(
                        response=fallback,
                        session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=0.5,
                    intent=intent_result.intent
                )
            
            elif intent_result.intent == IntentType.ORDERING:
                try:
                    self.context_manager.update_conversation_state(session, ConversationState.BUILDING_ORDER)
                    result = self.order_agent.process_order_request(message, session, intent_result.entities)
                    
                    if result["success"] and result.get("order_draft"):
                        self.context_manager.update_order_draft(session, result["order_draft"])
                    
                    # IMPORTANT: Always include current order draft, even on errors
                    # This ensures the receipt persists through unclear requests or not-found items
                    current_draft = None
                    if session.current_order_draft:
                        try:
                            current_draft = json.loads(session.current_order_draft)
                        except:
                            pass
                    
                    # Build response with order_draft (use current draft if result doesn't have one)
                    response = ConversationResponse(
                        response=result["message"],
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=intent_result.confidence,
                        intent=intent_result.intent,
                        order_draft=result.get("order_draft") or current_draft  # Always include current draft
                    )
                    
                    self.context_manager.add_message_to_history(session, "assistant", response.response)
                    return response
                except Exception as e:
                    logger.error(f"Order processing failed: {e}")
                    # Rollback any partial changes
                    self.db.rollback()
                    fallback = "عذراً، حدث خطأ عند معالجة طلبك. هل يمكنك إعادة المحاولة؟" if language == "ar" else "Sorry, error processing your order. Can you try again?"
                    self.context_manager.add_message_to_history(session, "assistant", fallback)
                    return ConversationResponse(
                        response=fallback,
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=0.5,
                        intent=intent_result.intent
                    )
            
            elif intent_result.intent == IntentType.COMPLAINT:
                try:
                    self.context_manager.update_conversation_state(session, ConversationState.RESOLVING_ISSUE)
                    result = self.issue_agent.handle_complaint(
                        message,
                        session.customer_id,
                        intent_result.entities
                    )
                    response_text = result["message"]
                    self.context_manager.add_message_to_history(session, "assistant", response_text)
                    return ConversationResponse(
                        response=response_text,
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=intent_result.confidence,
                        intent=intent_result.intent
                    )
                except Exception as e:
                    logger.error(f"Issue resolution failed: {e}")
                    # Rollback any partial changes
                    self.db.rollback()
                    fallback = "عذراً، حدث خطأ. دعني أحولك إلى موظف لمساعدتك..." if language == "ar" else "Sorry, error occurred. Let me transfer you to an agent..."
                    self.context_manager.add_message_to_history(session, "assistant", fallback)
                    # Auto-escalate on error
                    self.audit_logger.log(
                        action="auto_escalated_on_error",
                        customer_id=session.customer_id,
                        details={"error": str(e)}
                    )
                    return ConversationResponse(
                        response=fallback,
                        session_id=session.id,
                        conversation_state=ConversationState.ENDED,
                        confidence=0.5,
                        intent=IntentType.ESCALATE
                    )
            
            elif intent_result.intent == IntentType.TRACKING:
                # Get order_id from entities or use latest order
                order_id = intent_result.entities.get("order_id")
                
                from src.models.database import Order
                order = None
                
                if order_id:
                    order = self.db.query(Order).filter(Order.id.like(f"{order_id}%")).first()
                else:
                    # Get most recent order for this customer
                    order = self.db.query(Order).filter(
                        Order.customer_id == session.customer_id
                    ).order_by(Order.created_at.desc()).first()
                
                if not order:
                    response_text = "لم أتمكن من إيجاد طلبك. هل يمكنك تزويدي برقم الطلب؟"
                else:
                    status_ar = {
                        "PENDING": "قيد التحضير",
                        "READY": "جاهز للاستلام",
                        "DELIVERED": "تم التسليم",
                        "CANCELLED": "ملغي"
                    }
                    status_text = status_ar.get(order.status.value, order.status.value)
                    
                    from datetime import datetime
                    if order.status.value == "PENDING" and order.estimated_ready_time:
                        time_diff = (order.estimated_ready_time - datetime.utcnow()).total_seconds()
                        if time_diff > 0:
                            minutes = int(time_diff / 60)
                            response_text = f"طلبك رقم #{str(order.order_number)[:8]}\n\nحالة: {status_text}\nسيكون جاهز خلال {minutes} دقيقة"
                        else:
                            response_text = f"طلبك رقم #{str(order.order_number)[:8]}\n\nحالة: {status_text}\nطلبك جاهز للاستلام"
                    else:
                        response_text = f"طلبك رقم #{str(order.order_number)[:8]}\n\nحالة: {status_text}"
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
            
            elif intent_result.intent == IntentType.REMOVE:
                # Remove item from current order
                result = self.order_agent.remove_item(message, session, intent_result.entities)
                
                # Check if this should retry as an ordering intent (compound message)
                if not result["success"] and result.get("should_retry_as_order"):
                    logger.info("Retrying compound message as ordering intent")
                    # Retry as ordering intent
                    try:
                        self.context_manager.update_conversation_state(session, ConversationState.BUILDING_ORDER)
                        order_result = self.order_agent.process_order_request(message, session, intent_result.entities)
                        
                        if order_result["success"] and order_result.get("order_draft"):
                            self.context_manager.update_order_draft(session, order_result["order_draft"])
                        
                        # Get current draft for fallback
                        current_draft = None
                        if session.current_order_draft:
                            try:
                                current_draft = json.loads(session.current_order_draft)
                            except:
                                pass
                        
                        response = ConversationResponse(
                            response=order_result["message"],
                            session_id=session.id,
                            conversation_state=session.conversation_state,
                            confidence=intent_result.confidence,
                            intent=IntentType.ORDERING,  # Change intent to ORDERING
                            order_draft=order_result.get("order_draft") or current_draft
                        )
                        
                        self.context_manager.add_message_to_history(session, "assistant", response.response)
                        return response
                        
                    except Exception as e:
                        logger.error(f"Failed to retry as ordering: {e}")
                        # Fall back to original remove result
                
                if result["success"] and result.get("order_draft"):
                    self.context_manager.update_order_draft(session, result["order_draft"])
                
                # Get current draft for fallback on errors
                current_draft = None
                if session.current_order_draft:
                    try:
                        current_draft = json.loads(session.current_order_draft)
                    except:
                        pass
                
                response = ConversationResponse(
                    response=result["message"],
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent,
                    order_draft=result.get("order_draft") or current_draft  # Always include current draft
                )
                
                self.context_manager.add_message_to_history(session, "assistant", response.response)
                return response
            
            elif intent_result.intent == IntentType.QUERY_ORDER:
                # Answer questions about order
                result = self.order_agent.query_order(message, session, intent_result.entities)
                response_text = result["message"]
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
            
            elif intent_result.intent == IntentType.CONFIRM_ORDER:
                # Submit current order
                if not session.current_order_draft:
                    response_text = "❌ لا يوجد طلب لتأكيده.\n\n📋 أضف بعض المنتجات أولاً"
                    self.context_manager.add_message_to_history(session, "assistant", response_text)
                    return ConversationResponse(
                        response=response_text,
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=intent_result.confidence,
                        intent=intent_result.intent
                    )
                
                # Submit order and clear draft
                try:
                    result = self.order_agent.submit_order(session)
                    response_text = result["message"]
                    
                    if result["success"]:
                        # Update conversation state to greeting for new session
                        self.context_manager.update_conversation_state(session, ConversationState.GREETING)
                        
                        self.context_manager.add_message_to_history(session, "assistant", response_text)
                        return ConversationResponse(
                            response=response_text,
                            session_id=session.id,
                            conversation_state=session.conversation_state,
                            confidence=intent_result.confidence,
                            intent=intent_result.intent,
                            order_draft=None,  # Clear the order draft
                            order_cleared=True,  # Indicate order was cleared
                            order_number=result.get("order_number"),  # Pass order number to frontend
                            receipt_data=result.get("receipt_data")  # Pass receipt data for table display
                        )
                    else:
                        self.context_manager.add_message_to_history(session, "assistant", response_text)
                        return ConversationResponse(
                            response=response_text,
                            session_id=session.id,
                            conversation_state=session.conversation_state,
                            confidence=intent_result.confidence,
                            intent=intent_result.intent,
                            order_draft=json.loads(session.current_order_draft) if session.current_order_draft else None
                        )
                    
                except Exception as e:
                    logger.error(f"Order submission failed: {e}")
                    response_text = "❌ عذراً، حدث خطأ عند تأكيد الطلب.\n\n🔄 يرجى المحاولة مرة أخرى"
                    self.context_manager.add_message_to_history(session, "assistant", response_text)
                    return ConversationResponse(
                        response=response_text,
                        session_id=session.id,
                        conversation_state=session.conversation_state,
                        confidence=0.5,
                        intent=IntentType.UNCLEAR
                    )
            
            elif intent_result.intent == IntentType.CANCEL:
                # Clear the current order draft
                self.context_manager.clear_order_draft(session)
                self.context_manager.update_conversation_state(session, ConversationState.GREETING)
                if language == "ar":
                    response_text = """✅ تم إلغاء الطلب السابق وبدء طلب جديد.

📋 ماذا تريد أن تطلب اليوم؟"""
                else:
                    response_text = """✅ Previous order cancelled. New order started.

📋 What would you like to order today?"""                
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent,
                    order_draft={"items": [], "subtotal": 0, "tax": 0, "delivery_fee": 0, "total": 0}
                )
            
            elif intent_result.intent == IntentType.ESCALATE:
                # Escalate to human agent
                self.context_manager.update_conversation_state(session, ConversationState.ENDED)
                if language == "ar":
                    response_text = """جاري تحويلك إلى موظف خدمة العملاء...

سيتواصل معك أحد ممثلينا قريباً لمساعدتك.

شكراً لصبرك."""
                else:
                    response_text = """Transferring you to a customer service representative...

Thank you for your patience."""
                
                self.audit_logger.log(
                    action="escalated_to_human",
                    customer_id=session.customer_id,
                    details={"reason": message, "session_id": str(session.id)}
                )
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
            
            elif intent_result.intent == IntentType.FAREWELL:
                self.context_manager.update_conversation_state(session, ConversationState.ENDED)
                if language == "ar":
                    response_text = """شكراً لك! 

أتمنى لك يوماً سعيداً. 
إذا احتجت أي شيء، أنا هنا دائماً لمساعدتك!

مع السلامة"""
                else:
                    response_text = """Thank you!

Have a great day!
If you need anything else, I'm always here to help.

Goodbye!"""
                
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
            
            else:
                response_text = "أنا هنا لمساعدتك! يمكنك السؤال عن المنيو تقديم طلب، أو الإبلاغ عن مشكلة."
                self.context_manager.add_message_to_history(session, "assistant", response_text)
                return ConversationResponse(
                    response=response_text,
                    session_id=session.id,
                    conversation_state=session.conversation_state,
                    confidence=intent_result.confidence,
                    intent=intent_result.intent
                )
        except Exception as e:
            logger.error(f"Critical error in _route_to_agent: {e}", exc_info=True)
            # Fallback response on critical error
            fallback = "عذراً، حدث خطأ. دعني أحولك لموظف..." if language == "ar" else "Sorry, error occurred. Let me transfer you..."
            return ConversationResponse(
                response=fallback,
                session_id=session.id,
                conversation_state=ConversationState.ENDED,
                confidence=0.0,
                intent=IntentType.ESCALATE
            )
