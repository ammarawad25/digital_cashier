from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from src.models.database import Session as SessionModel, Customer
from src.models.enums import ConversationState
from datetime import datetime, timedelta
import uuid
import json
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class ContextManager:
    """Manages conversation context and session state
    
    Responsibilities:
    - Create and manage conversation sessions
    - Track conversation history with memory limits
    - Manage order drafts and state transitions
    - Ensure data consistency and cleanup
    """
    
    def __init__(self, db: Session):
        """Initialize context manager
        
        Args:
            db: SQLAlchemy database session
        """
        try:
            self.db = db
            self.max_history_messages = 20  # Reduced for speed (was 50)
            self.max_message_length = 2000  # Reduced for memory efficiency
            logger.info("ContextManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ContextManager: {e}")
            raise
    
    def get_or_create_session(
        self,
        customer_phone: str,
        session_id: Optional[str] = None
    ) -> SessionModel:
        """Get existing session or create new one with validation
        
        Args:
            customer_phone: Customer phone number
            session_id: Optional existing session ID
        
        Returns:
            SessionModel instance
        """
        try:
            # Validate phone number
            if not customer_phone or not customer_phone.strip():
                raise ValueError("customer_phone cannot be empty")
            
            # Try to get existing valid session by session_id
            if session_id:
                try:
                    session = self.db.query(SessionModel).filter(
                        SessionModel.id == str(session_id)
                    ).first()
                    
                    if session and session.expires_at > datetime.utcnow():
                        logger.info(f"Retrieved existing session: {session_id}")
                        return session
                    elif session:
                        logger.info(f"Session {session_id} expired, will look for another or create new one")
                except SQLAlchemyError as e:
                    logger.warning(f"Error retrieving session {session_id}: {e}")
            
            # Get or create customer
            customer = self.db.query(Customer).filter(
                Customer.phone == customer_phone
            ).first()
            
            if not customer:
                customer = Customer(
                    name="Unknown",
                    phone=customer_phone,
                    email=f"{customer_phone}@temp.com"
                )
                self.db.add(customer)
                self.db.flush()  # Get customer ID
                logger.info(f"Created new customer: {customer.id}")
            else:
                # Customer exists - try to find an active session for this customer
                try:
                    existing_session = self.db.query(SessionModel).filter(
                        SessionModel.customer_id == customer.id,
                        SessionModel.expires_at > datetime.utcnow()
                    ).order_by(SessionModel.updated_at.desc()).first()
                    
                    if existing_session:
                        # Clear the order draft to start fresh conversation
                        existing_session.current_order_draft = None
                        self.db.commit()
                        logger.info(f"Found existing active session {existing_session.id} for customer {customer.id} - cleared order draft")
                        return existing_session
                except SQLAlchemyError as e:
                    logger.warning(f"Error finding existing session for customer {customer.id}: {e}")
            
            # No valid session found - create a new one
            new_session = SessionModel(
                customer_id=customer.id,
                channel="voice",
                conversation_history="[]",
                conversation_state=ConversationState.GREETING,
                current_order_draft=None,  # Start with no order
                expires_at=datetime.utcnow() + timedelta(hours=2)
            )
            self.db.add(new_session)
            self.db.commit()
            self.db.refresh(new_session)
            
            logger.info(f"Created new session: {new_session.id} for customer: {customer.id}")
            return new_session
        
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_or_create_session: {e}", exc_info=True)
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_or_create_session: {e}", exc_info=True)
            raise
    
    def add_message_to_history(
        self,
        session: SessionModel,
        role: str,
        content: str,
        max_messages: Optional[int] = None
    ):
        """Add message to history with automatic pruning and validation
        
        Args:
            session: Current session
            role: Message role (user/assistant)
            content: Message content
            max_messages: Maximum messages to keep (default: self.max_history_messages)
        """
        try:
            if not session:
                raise ValueError("session cannot be None")
            
            if not content:
                logger.warning("Attempted to add empty message to history")
                return
            
            # Truncate overly long messages
            if len(content) > self.max_message_length:
                logger.warning(f"Truncating message from {len(content)} to {self.max_message_length} chars")
                content = content[:self.max_message_length] + "..."
            
            # Load and validate history
            try:
                history = json.loads(session.conversation_history or "[]")
                if not isinstance(history, list):
                    logger.warning("Invalid history format, resetting")
                    history = []
            except json.JSONDecodeError:
                logger.error("Failed to decode conversation history, resetting")
                history = []
            
            # Add new message
            history.append({
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Prune old messages for memory efficiency
            max_msg = max_messages or self.max_history_messages
            if len(history) > max_msg:
                # Keep first message (usually greeting) and recent messages
                history = [history[0]] + history[-(max_msg-1):]
                logger.debug(f"Pruned history to {len(history)} messages")
            
            # Save back to session
            session.conversation_history = json.dumps(history)
            session.updated_at = datetime.utcnow()
            self.db.commit()
        
        except SQLAlchemyError as e:
            logger.error(f"Database error adding message to history: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error adding message to history: {e}")
            raise
    
    def get_recent_context(
        self,
        session: SessionModel,
        num_messages: int = 10
    ) -> list:
        """Get recent conversation context for better agent responses"""
        history = json.loads(session.conversation_history or "[]")
        return history[-num_messages:] if len(history) > num_messages else history
    
    def get_conversation_history(
        self,
        session: SessionModel,
        limit: int = 10
    ) -> list:
        """Get conversation history with optional limit"""
        history = json.loads(session.conversation_history or "[]")
        return history[-limit:] if limit and len(history) > limit else history
    
    def update_conversation_state(
        self,
        session: SessionModel,
        new_state: ConversationState
    ):
        session.conversation_state = new_state
        session.updated_at = datetime.utcnow()
        self.db.commit()
    
    def update_order_draft(
        self,
        session: SessionModel,
        order_draft: Dict
    ):
        """Update session order draft with validation
        
        Args:
            session: Current session
            order_draft: Order draft dictionary
        """
        try:
            if not session:
                raise ValueError("session cannot be None")
            
            if not isinstance(order_draft, dict):
                raise ValueError("order_draft must be a dictionary")
            
            # Validate order draft structure
            if "items" not in order_draft:
                logger.warning("Order draft missing 'items' key")
                order_draft["items"] = []
            
            session.current_order_draft = json.dumps(order_draft)
            session.updated_at = datetime.utcnow()
            self.db.commit()
            logger.debug(f"Updated order draft for session {session.id}")
        
        except SQLAlchemyError as e:
            logger.error(f"Database error updating order draft: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error updating order draft: {e}")
            raise
    
    def clear_order_draft(self, session: SessionModel):
        """Clear current order draft
        
        Args:
            session: Current session
        """
        try:
            if not session:
                raise ValueError("session cannot be None")
            
            session.current_order_draft = None
            session.updated_at = datetime.utcnow()
            self.db.commit()
            logger.debug(f"Cleared order draft for session {session.id}")
        
        except SQLAlchemyError as e:
            logger.error(f"Database error clearing order draft: {e}")
            self.db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error clearing order draft: {e}")
            raise
