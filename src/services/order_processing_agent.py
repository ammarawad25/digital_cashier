from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func
from src.models.database import Order, OrderItem, MenuItem, Session as SessionModel
from src.models.enums import OrderStatus
from src.services.recommendations import RecommendationEngine
from src.services.audit_logger import AuditLogger
from typing import Dict, List
import json
import logging
import random
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from src.config import settings

logger = logging.getLogger(__name__)

# Singleton LLM instance for order processing agent
_order_llm_instance = None

def _get_order_llm():
    """Get singleton LLM for order processing agent"""
    global _order_llm_instance
    if _order_llm_instance is None:
        logger.info(f"Initializing order processing LLM: {settings.llm_model}")
        _order_llm_instance = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.0,  # Zero for maximum consistency and speed
            timeout=10,  # Aggressive timeout for extraction
            max_retries=1,  # Reduce retries for speed
            max_tokens=250,  # Further limit for speed
            streaming=True
        )
    return _order_llm_instance


class OrderProcessingAgent:
    """Simplified order processing agent focused on direct item processing
    
    Responsibilities:
    - Parse and validate order requests
    - Manage order drafts and modifications
    - Handle order submission with transaction safety
    - Provide order queries and summaries
    """
    
    def __init__(self, db: Session):
        """Initialize order processing agent
        
        Args:
            db: SQLAlchemy database session
        """
        try:
            self.db = db
            self.recommendation_engine = RecommendationEngine()
            self.audit_logger = AuditLogger(db)
            
            # Use singleton LLM for simple extraction tasks only
            self.llm = _get_order_llm()
            # No need for current_session attribute in optimized version
            
            logger.info("OrderProcessingAgent initialized (optimized)")
        except Exception as e:
            logger.error("Failed to initialize OrderProcessingAgent: %s", e)
            raise
    
    def process_order_request(self, message: str, session: SessionModel, entities: Dict) -> Dict:
        """Process order request - simplified direct approach"""
        try:
            
            # Check if this is a compound message (contains both remove and add)
            message_lower = message.lower()
            has_remove_keywords = any(word in message_lower for word in ["احذف", "حذف", "شيل", "ازالة", "remove", "delete"])
            has_add_keywords = any(word in message_lower for word in ["أضف", "اضف", "أريد", "بدي", "عايز", "add", "want"])
            
            compound_result = None
            
            if has_remove_keywords and has_add_keywords:
                logger.info("Processing compound message with both remove and add operations")
                # Handle remove operations first if there's an existing order
                if session.current_order_draft:
                    try:
                        # Extract items to remove using keywords
                        remove_items = self._extract_items_to_remove(message)
                        if remove_items:
                            remove_result = self.remove_item(message, session, {"items": remove_items})
                            if remove_result["success"]:
                                compound_result = f"{remove_result['message']}\n\n📝 والآن أضيف المنتجات الجديدة:\n"
                    except Exception as e:
                        logger.warning(f"Remove operation in compound message failed: {e}")
            
            # Extract items to ADD (filter out remove keywords)
            add_only_message = self._filter_message_for_add_only(message)
            
            # Extract items from entities if available
            items = entities.get("items", [])
            if items:
                result = self._process_items_directly(items, entities, session)
            else:
                # If no entities, try to extract items using simple LLM call on filtered message
                try:
                    extracted_items = self._extract_items_with_llm(add_only_message)
                    if extracted_items:
                        result = self._process_items_directly(extracted_items, {}, session)
                    else:
                        result = {
                            "success": False, 
                            "message": "عذراً، لم أتمكن من فهم المنتجات الجديدة في طلبك. يرجى ذكر اسم الوجبة بوضوح."
                        }
                except Exception as llm_error:
                    logger.warning(f"LLM extraction failed: {llm_error}")
                    result = {
                        "success": False, 
                        "message": "عذراً، لم أتمكن من فهم طلبك. يرجى ذكر اسم الوجبة بوضوح."
                    }
            
            # Combine compound result if exists
            if compound_result and result["success"]:
                result["message"] = compound_result + result["message"]
            
            return result
            
        except Exception as e:
            logger.error("Order processing failed: %s", e, exc_info=True)
            return {"success": False, "message": "عذراً، حدث خطأ عند معالجة طلبك. جاري تحويلك الي احد موظفينا."}

    def _extract_items_with_llm(self, message: str) -> List[Dict]:
        """Extract items from message using intelligent LLM extraction
        Handles contextual references and attributes like 'the burger is classic'
        Returns list of dicts with 'name' and 'quantity' keys
        """
        try:
            from langchain.schema import HumanMessage
            
            # Enhanced prompt to handle contextual references and attributes
            prompt = f'''Extract food items with quantities and attributes from: "{message}"

IMPORTANT RULES:
1. Resolve contextual references ("the burger", "it", etc.) by combining with attributes mentioned later
2. If an attribute is mentioned ("classic", "large", "spicy"), attach it to the relevant item
3. Combine item name with its attributes into a single descriptive name
4. Arabic numbers: واحد=1, اثنين=2, ثلاثة=3, أربعة=4, خمسة=5, etc.

Examples:
- "1 burger and 2 fries, the burger is classic" → [{{"name":"classic burger","quantity":1}},{{"name":"fries","quantity":2}}]
- "أريد برجر وبطاطس، البرجر كلاسيكي" → [{{"name":"برجر كلاسيكي","quantity":1}},{{"name":"بطاطس","quantity":1}}]
- "2 pizzas, one pepperoni and one veggie" → [{{"name":"pepperoni pizza","quantity":1}},{{"name":"veggie pizza","quantity":1}}]
- "محتاج اتنين برجر واحد بطاطس، البرجر خالي كلاسيكي" → [{{"name":"برجر كلاسيكي","quantity":2}},{{"name":"بطاطس","quantity":1}}]

Return JSON array ONLY: [{{"name":"item with attributes","quantity":number}}]
Return [] if no items found.'''

            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            
            # Parse JSON response
            if content.startswith('[') and content.endswith(']'):
                try:
                    items = json.loads(content)
                    # Validate and clean items
                    validated = []
                    for item in items:
                        if isinstance(item, dict) and "name" in item:
                            name = item["name"].strip()
                            quantity = max(1, int(item.get("quantity", 1)))
                            if name:  # Only add if name is not empty
                                validated.append({"name": name, "quantity": quantity})
                        elif isinstance(item, str) and item.strip():
                            validated.append({"name": item.strip(), "quantity": 1})
                    return validated
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"JSON parsing failed: {e}, trying ast")
                    try:
                        import ast
                        items = ast.literal_eval(content)
                        if isinstance(items, list):
                            validated = []
                            for item in items:
                                if isinstance(item, dict):
                                    name = str(item.get("name", "")).strip()
                                    quantity = max(1, int(item.get("quantity", 1)))
                                    if name:
                                        validated.append({"name": name, "quantity": quantity})
                                elif isinstance(item, str) and item.strip():
                                    validated.append({"name": item.strip(), "quantity": 1})
                            return validated
                    except Exception:
                        pass
            
            return []
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return []
    
    def _process_items_directly(self, items: List, entities: Dict, session: SessionModel) -> Dict:
        """Enhanced processing with confidence checking and better item handling"""
        try:
            # Load order draft
            order_draft = json.loads(session.current_order_draft) if session.current_order_draft else {"items": []}
            if order_draft.get("items"):
                order_draft["items"] = self._aggregate_items(order_draft["items"])
            
            found_items = []
            not_found = []
            suggestions = []
            print(items)
            for item in items:
                # Each item should be a dict with "name" and "quantity" keys
                # Handle legacy string format for backwards compatibility
                if isinstance(item, str):
                    item_name = item
                    item_quantity = 1
                elif isinstance(item, dict):
                    item_name = item.get("name", item.get("item", ""))
                    item_quantity = item.get("quantity", 1)
                else:
                    logger.warning(f"Invalid item format: {item}")
                    continue
                
                # Get match with confidence
                menu_item, confidence = self._find_menu_item(item_name)
                
                # Confidence-based decision flow
                if menu_item and confidence >= 0.85:  # High confidence: add directly
                    quantity_to_add = self._parse_quantity(item_quantity)
                    existing_item = next(
                        (itm for itm in order_draft["items"] if itm["id"] == str(menu_item.id)),
                        None
                    )
                    if existing_item:
                        existing_item["quantity"] += quantity_to_add
                    else:
                        order_draft["items"].append({
                            "id": str(menu_item.id),
                            "name": menu_item.name,
                            "arabic_name": menu_item.arabic_name or menu_item.name,
                            "price": menu_item.price,
                            "category": menu_item.category,
                            "quantity": quantity_to_add
                        })
                    found_items.append(f"{quantity_to_add} {menu_item.arabic_name or menu_item.name}")
                    
                elif menu_item and 0.6 <= confidence < 0.85:  # Medium confidence: ask for confirmation
                    # Add to suggestions for user to confirm
                    suggestions.append(f"{menu_item.arabic_name or menu_item.name} (هل تقصد هذا؟)")
                    not_found.append(item_name)
                    
                else:  # Low confidence or no match
                    not_found.append(item_name)
                    # Suggest similar items
                    similar = self._find_similar_items(item_name)
                    if similar:
                        suggestions.extend(similar[:2])  # Max 2 suggestions per unfound item
            
            if not found_items and not_found:
                suggestion_text = ""
                if suggestions:
                    suggestion_text = f"\n\nهل تقصد: {', '.join(suggestions)}؟"
                return {"success": False, "message": f"عذراً، لم أجد '{', '.join(not_found)}' في المنيو.{suggestion_text}"}
            
            # Calculate totals
            totals = self._calculate_totals(order_draft["items"])
            order_draft.update(totals)
            
            # Save updated draft
            session.current_order_draft = json.dumps(order_draft)
            self.db.commit()
            
            # Build response message
            success_msg = f"تم إضافة {', '.join(found_items)} إلى طلبك."
            
            if not_found:
                suggestion_text = ""
                if suggestions:
                    suggestion_text = f" هل تقصد: {', '.join(suggestions)}؟"
                success_msg += f"\n\n(لم نجد: {', '.join(not_found)}){suggestion_text}"
            
            # Add recommendations
            try:
                recommendations = self.recommendation_engine.get_recommendations(order_draft["items"])
                if recommendations:
                    success_msg += f"\n\nهل تريد إضافة {' أو '.join(recommendations[:2])}؟"
            except Exception:
                pass
            
            return {"success": True, "message": success_msg, "order_draft": order_draft}
            
        except Exception as e:
            logger.error(f"Error processing items directly: {e}")
            return {"success": False, "message": "عذراً، حدث خطأ عند معالجة طلبك. جاري تحويلك الي احد موظفينا."}
    
    def submit_order(self, session: SessionModel) -> Dict:
        """Submit order with transaction safety and validation
        
        Args:
            session: Current conversation session with order draft
        
        Returns:
            Dict with success status, message, and order details
        """
        if not session.current_order_draft:
            return {
                "success": False,
                "message": "لا يوجد طلب لتقديمه."
            }
        
        try:
            draft = json.loads(session.current_order_draft)
            
            # Validate draft has items
            if not draft.get("items"):
                return {
                    "success": False,
                    "message": "الطلب فارغ. أضف منتجات أولاً."
                }
            
            # Begin transaction
            # Generate readable order number
            date_str = datetime.now().strftime("%Y%m%d")
            random_suffix = random.randint(1000, 9999)
            order_number = f"BRG-{date_str}-{random_suffix}"
            
            order = Order(
                customer_id=session.customer_id,
                status=OrderStatus.PENDING,
                subtotal=draft["subtotal"],
                tax=draft["tax"],
                delivery_fee=draft.get("delivery_fee", 0),
                total=draft["total"],
                fulfillment_type="drive-thru",
                order_number=order_number
            )
            self.db.add(order)
            self.db.flush()  # Get order ID before adding items
            
            # Store readable order number in draft for receipt display
            draft["order_number"] = order_number
            
            # Schedule order to be ready in 1 minute
            order.estimated_ready_time = datetime.utcnow() + timedelta(minutes=1)
            order.status = OrderStatus.PENDING
            
            # Add order items
            for item_data in draft["items"]:
                # Validate menu item still exists and is available
                menu_item = self.db.query(MenuItem).filter(
                    MenuItem.id == item_data["id"],
                    MenuItem.is_available == True
                ).first()
                
                if not menu_item:
                    logger.warning(f"Menu item {item_data['id']} no longer available")
                    # Rollback and return error
                    self.db.rollback()
                    return {
                        "success": False,
                        "message": f"عذراً، {item_data.get('arabic_name', item_data['name'])} لم يعد متاحاً. يرجى تحديث طلبك."
                    }
                
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item_data["id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["price"]
                )
                self.db.add(order_item)
            
            # Commit transaction
            self.db.commit()
            
            # Clear order draft after successful submission
            session.current_order_draft = None
            self.db.commit()
            
            # Audit log
            try:
                self.audit_logger.log(
                    action="order_created",
                    customer_id=session.customer_id,
                    session_id=session.id,
                    details={"order_id": str(order.id), "total": draft["total"], "items_count": len(draft["items"])}
                )
            except Exception as e:
                logger.warning(f"Audit logging failed: {e}")
            
            # Format beautiful confirmation message with receipt data
            confirmation_msg = f"""✅ تم تأكيد طلبك بنجاح!

📋 رقم الطلب: {order_number}
💰 المبلغ الإجمالي: {draft['total']:.2f} SAR

🚚 سيتم التحضير خلال 15 دقيقة

🙏 شكراً لاختيارنا!"""
            
            # Prepare receipt data for frontend table display
            receipt_data = {
                "order_number": order_number,
                "items": draft.get("items", []),
                "subtotal": draft.get("subtotal", 0),
                "tax": draft.get("tax", 0),
                "delivery_fee": draft.get("delivery_fee", 0),
                "total": draft.get("total", 0),
                "fulfillment_type": draft.get("fulfillment_type", "delivery")
            }
            
            return {
                "success": True,
                "message": confirmation_msg,
                "order_id": str(order.id),
                "order_number": order_number,  # Readable format (e.g., BRG-20260127-1234)
                "order_cleared": True,  # Indicate order was cleared
                "receipt_data": receipt_data  # Include full receipt for display
            }
        
        except SQLAlchemyError as e:
            logger.error(f"Database error submitting order: {e}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "message": "عذراً، حدث خطأ عند حفظ طلبك. يرجى المحاولة مرة أخرى."
            }
        except Exception as e:
            logger.error(f"Unexpected error submitting order: {e}", exc_info=True)
            self.db.rollback()
            return {
                "success": False,
                "message": "عذراً، حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى."
            }
    
    def _generate_readable_order_number(self) -> str:
        """Generate a readable order number in format: BRG-YYYYMMDD-XXXX
        Example: BRG-20260127-1234
        """
        date_str = datetime.now().strftime("%Y%m%d")
        random_suffix = random.randint(1000, 9999)
        return f"BRG-{date_str}-{random_suffix}"
    
    def _parse_quantity(self, quantity_input) -> int:
        """Parse and validate quantity input
        
        Args:
            quantity_input: Quantity as int, str, or dict
        
        Returns:
            Validated integer quantity (min: 1, max: 50)
        """
        try:
            if isinstance(quantity_input, int):
                quantity = quantity_input
            elif isinstance(quantity_input, str):
                quantity = int(quantity_input)
            elif isinstance(quantity_input, dict) and "value" in quantity_input:
                quantity = int(quantity_input["value"])
            else:
                logger.warning(f"Invalid quantity format: {quantity_input}")
                return 1
            
            # Clamp to reasonable bounds
            return max(1, min(50, quantity))
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse quantity '{quantity_input}': {e}")
            return 1
    
    def remove_item(self, message: str, session: SessionModel, entities: Dict) -> Dict:
        """Remove item(s) from current order"""
        # Check if this is a compound message (remove + add)
        message_lower = message.lower()
        has_add_keywords = any(word in message_lower for word in ["أضف", "اضف", "أريد", "بدي", "عايز", "add", "want"])
        
        if not session.current_order_draft:
            if has_add_keywords:
                # This is a compound message - handle the add part instead
                return {
                    "success": False,
                    "message": "لا يوجد طلب حالي للحذف منه.\n\nولكن يمكنني إضافة المنتجات الجديدة لك! \n\nماذا تريد أن تطلب؟",
                    "should_retry_as_order": True
                }
            else:
                return {
                    "success": False,
                    "message": "❌ لا يوجد طلب حالي لحذف منه.\n\n📋 أضف بعض المنتجات أولاً لبدء طلب جديد!"
                }
        
        order_draft = json.loads(session.current_order_draft)
        items = entities.get("items", [])
        
        if not items:
            items = self._extract_items_from_message(message)
        
        if not items:
            return {
                "success": False,
                "message": "لم أتمكن من تحديد المنتج المطلوب حذفه. ماذا تريد حذفه؟"
            }
        
        removed_items = []
        not_found = []
        
        for item in items:
            # Handle both dict format (from intent) and string format (from extraction)
            if isinstance(item, dict):
                item_name = item.get("name", "")
                quantity_to_remove = self._parse_quantity(item.get("quantity", 1))
            else:
                item_name = item
                quantity_to_remove = 1
            
            menu_item, confidence = self._find_menu_item(item_name)
            if menu_item:
                # Find item in current order
                existing_item = next(
                    (item for item in order_draft["items"] if item["id"] == str(menu_item.id)),
                    None
                )
                
                if existing_item:
                    if existing_item["quantity"] <= quantity_to_remove:
                        # Remove item completely
                        order_draft["items"].remove(existing_item)
                        removed_items.append(f"{menu_item.arabic_name or menu_item.name} (كل الكمية)")
                    else:
                        # Reduce quantity
                        existing_item["quantity"] -= quantity_to_remove
                        removed_items.append(f"{quantity_to_remove} {menu_item.arabic_name or menu_item.name}")
                else:
                    not_found.append(menu_item.arabic_name or menu_item.name)
            else:
                not_found.append(item_name)
        
        if not removed_items:
            return {
                "success": False,
                "message": f"لم أجد '{', '.join(not_found)}' في طلبك الحالي."
            }
        
        # Recalculate totals
        if order_draft["items"]:
            totals = self._calculate_totals(order_draft["items"])
            order_draft.update(totals)
        else:
            # Order is now empty
            order_draft = {"items": [], "subtotal": 0, "tax": 0, "delivery_fee": 0, "total": 0}
        
        response = f"تم حذف {', '.join(removed_items)} من طلبك."
        
        if not_found:
            response += f"\n\n(لم نجد في الطلب: {', '.join(not_found)})"
        
        return {
            "success": True,
            "message": response,
            "order_draft": order_draft
        }
    
    def query_order(self, message: str, session: SessionModel, entities: Dict) -> Dict:
        """Answer questions about current order or order by ID"""
        order_id = entities.get("order_id")
        
        # Also try to extract order number from message
        if not order_id:
            import re
            # Look for patterns like #12345678, 12345678, order 12345678
            order_pattern = r'#?([0-9]{8})'
            match = re.search(order_pattern, message)
            if match:
                order_id = match.group(1)
        
        if order_id:
            # Query specific order by ID (support both full ID and 8-digit order number)
            order = self.db.query(Order).filter(
                (Order.id.like(f"{order_id}%")) |  # Order number search
                (Order.id == order_id)  # Full ID search
            ).first()
            if not order:
                return {
                    "success": False,
                    "message": f"❌ لم أجد طلب برقم {order_id}\n\n🔍 تأكد من رقم الطلب وحاول مرة أخرى"
                }
            
            # Load order items
            order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            items_info = []
            for oi in order_items:
                menu_item = self.db.query(MenuItem).filter(MenuItem.id == oi.menu_item_id).first()
                if menu_item:
                    items_info.append({
                        "name": menu_item.name,
                        "arabic_name": menu_item.arabic_name,
                        "quantity": oi.quantity,
                        "price": oi.unit_price
                    })
            
            # Format completed order response
            items_summary = "\n".join([
                f"• {item['quantity']}x {item['arabic_name'] or item['name']} ({item['price']:.2f} SAR)"
                for item in items_info
            ])
            
            status_text = {
                "PENDING": "🔄 قيد التحضير",
                "CONFIRMED": "✅ تم التأكيد", 
                "PREPARING": "👨‍🍳 يتم التحضير",
                "OUT_FOR_DELIVERY": "🚚 في الطريق إليك",
                "DELIVERED": "✅ تم التسليم",
                "CANCELLED": "❌ ملغي"
            }.get(order.status.value, order.status.value)
            
            response = f"""📋 طلب رقم: #{order.order_number or 'N/A'}
📊 الحالة: {status_text}

🛒 التفاصيل:
{items_summary}

💰 الإجمالي: {order.total:.2f} SAR
📅 تاريخ الطلب: {order.created_at.strftime('%Y-%m-%d %H:%M')}"""
            
            return {
                "success": True,
                "message": response
            }
        
        # Query current order
        if not session.current_order_draft:
            return {
                "success": False,
                "message": "لا يوجد طلب حالي."
            }
        
        order_draft = json.loads(session.current_order_draft)
        return self._format_order_query_response(message, order_draft["items"], order_draft["total"], order_draft["subtotal"])
    
    def _format_order_query_response(self, message: str, items: List[Dict], total: float, subtotal: float, is_completed: bool = False) -> Dict:
        """Format response for order queries"""
        message_lower = message.lower()
        
        # Check what the user is asking about
        if any(word in message_lower for word in ["كم", "how much", "total", "سعر", "مبلغ", "price"]):
            # Asking about price/total
            response = f"المبلغ الإجمالي {'للطلب' if is_completed else 'الحالي'}: {total:.2f} SAR\n"
            response += f"المجموع الفرعي: {subtotal:.2f} SAR"
        elif any(word in message_lower for word in ["how many", "عدد", "كم عدد"]):
            # Asking about quantity
            # Check if asking about specific item
            item_counts = {}
            for item in items:
                name = item.get("arabic_name") or item.get("name")
                if name in item_counts:
                    item_counts[name] += item["quantity"]
                else:
                    item_counts[name] = item["quantity"]
            
            # Check if asking about specific item type
            if "برجر" in message_lower or "burger" in message_lower:
                burger_count = sum(
                    item["quantity"] for item in items 
                    if (isinstance(item.get("category"), str) and "burger" in item.get("category", "").lower()) 
                    or (isinstance(item.get("arabic_name"), str) and "برجر" in item.get("arabic_name", "").lower())
                )
                response = f"عدد البرجر {'في الطلب' if is_completed else 'الحالي'}: {burger_count}"
            else:
                total_items = sum(item["quantity"] for item in items)
                response = f"عدد المنتجات {'في الطلب' if is_completed else 'الحالي'}: {total_items}\n\n"
                for name, count in item_counts.items():
                    response += f"• {name}: {count}\n"
        elif any(word in message_lower for word in ["what", "ماذا", "ما هو", "شو"]):
            # Asking what's in the order
            response = f"{'الطلب يحتوي' if is_completed else 'طلبك الحالي يحتوي'} على:\n\n"
            for item in items:
                name = item.get("arabic_name") or item.get("name")
                response += f"• {item['quantity']}x {name} ({item['price']:.2f} SAR)\n"
            response += f"\nالإجمالي: {total:.2f} SAR"
        else:
            # Generic order summary
            total_items = sum(item["quantity"] for item in items)
            response = f"{'الطلب' if is_completed else 'طلبك الحالي'}:\n"
            response += f"• عدد المنتجات: {total_items}\n"
            response += f"• الإجمالي: {total:.2f} SAR"
        
        return {
            "success": True,
            "message": response
        }
    
    def _find_menu_item(self, item_name: str) -> tuple:
        """Optimized menu item matching with multi-strategy approach
        
        Returns:
            tuple: (MenuItem, confidence_score) or (None, 0.0)
        """
        if not item_name or not isinstance(item_name, str):
            return None, 0.0
        
        item_lower = item_name.lower().strip()
        
        # Get all available menu items (cached would be better in production)
        all_items = self.db.query(MenuItem).filter(
            MenuItem.is_available == True
        ).all()
        
        if not all_items:
            return None, 0.0
        
        # Strategy 1: Exact match (highest confidence)
        for menu_item in all_items:
            if menu_item.name.lower() == item_lower or \
               (menu_item.arabic_name and menu_item.arabic_name.lower() == item_lower):
                return menu_item, 1.0
        
        # Strategy 2: LLM-based intelligent matching (best for complex queries)
        try:
            matched_item, confidence = self._llm_based_menu_matching(item_name, all_items)
            if matched_item and confidence >= 0.85:
                logger.info(f"LLM matched '{item_name}' → '{matched_item.name}' (conf: {confidence:.2f})")
                return matched_item, confidence
        except Exception as e:
            logger.warning(f"LLM matching failed: {e}")
        
        # Strategy 3: Direct substring matching (fast and reliable)
        matches = []
        for menu_item in all_items:
            # English name contains search term
            if item_lower in menu_item.name.lower():
                matches.append((menu_item, 0.95))
                continue
            # Search term contains item name
            if menu_item.name.lower() in item_lower:
                matches.append((menu_item, 0.93))
                continue
            # Arabic name matching
            if menu_item.arabic_name:
                arabic_lower = menu_item.arabic_name.lower()
                if item_lower in arabic_lower or arabic_lower in item_lower:
                    matches.append((menu_item, 0.92))
        
        if matches:
            # Return best match
            best = max(matches, key=lambda x: x[1])
            return best[0], best[1]
        
        # Strategy 4: Enhanced keyword mapping (specific → general)
        keyword_map = self._get_keyword_mappings()
        
        for keywords, category_filter in keyword_map:
            if any(kw in item_lower for kw in keywords):
                # Try to find matching item
                for menu_item in all_items:
                    if category_filter(menu_item, item_lower):
                        return menu_item, 0.88
        
        # Strategy 5: Fuzzy similarity matching (last resort)
        best_match, best_score = self._fuzzy_match(item_lower, all_items)
        if best_match and best_score >= 0.6:
            logger.info(f"Fuzzy matched '{item_name}' → '{best_match.name}' (score: {best_score:.2f})")
            return best_match, best_score
        
        return None, 0.0
    
    def _get_keyword_mappings(self) -> List[tuple]:
        """Get keyword to item type mappings with filters
        Returns list of (keywords, filter_function) tuples
        """
        def normalize_text(text):
            """Normalize Arabic text for comparison"""
            import re
            # Remove diacritics
            text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
            # Normalize alef variations
            text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            # Normalize taa marbouta
            text = text.replace('ة', 'ه')
            # Normalize yaa variations
            text = text.replace('ى', 'ي')
            return text.lower().strip()
        
        return [
            # Burgers - specific types first
            (['كلاسيكي', 'classic'], 
             lambda item, query: 'classic' in item.name.lower() and 'burger' in item.name.lower()),
            (['جبنة', 'جبن', 'cheese'], 
             lambda item, query: 'cheese' in item.name.lower() and 'burger' in item.name.lower()),
            (['دجاج', 'chicken'], 
             lambda item, query: 'chicken' in item.name.lower()),
            (['نباتي', 'veggie'], 
             lambda item, query: 'veggie' in item.name.lower()),
            (['بيكون', 'bacon'], 
             lambda item, query: 'bacon' in item.name.lower()),
            # Generic burger (after specific types)
            (['برجر', 'برغر', 'burger'], 
             lambda item, query: 'burger' in item.name.lower()),
            
            # Pizza types
            (['ببروني', 'بيبروني', 'pepperoni'], 
             lambda item, query: 'pepperoni' in item.name.lower()),
            (['مارجريتا', 'margherita'], 
             lambda item, query: 'margherita' in item.name.lower()),
            (['بيتزا', 'pizza'], 
             lambda item, query: 'pizza' in item.name.lower()),
            
            # Sides
            (['بطاطس', 'بطاطا', 'فرايز', 'فرويز', 'fries'], 
             lambda item, query: 'fries' in item.name.lower()),
            (['حلقات', 'بصل', 'onion rings'], 
             lambda item, query: 'onion' in item.name.lower()),
            
            # Beverages
            (['كولا', 'كوكا', 'cola', 'coca'], 
             lambda item, query: 'cola' in item.name.lower()),
            (['مشروب', 'صودا', 'سودا', 'soda'], 
             lambda item, query: 'soda' in item.name.lower() or item.category == 'Beverages'),
        ]
    
    def _fuzzy_match(self, query: str, menu_items: List[MenuItem]) -> tuple:
        """Calculate fuzzy similarity scores for all items
        
        Returns:
            tuple: (best_match, best_score) or (None, 0.0)
        """
        import re
        
        def normalize_arabic(text):
            text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
            text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
            text = text.replace('ة', 'ه').replace('ى', 'ي')
            return text.lower().strip()
        
        def calc_similarity(s1, s2):
            """Calculate word overlap similarity"""
            words1 = set(s1.split())
            words2 = set(s2.split())
            
            if not words1 or not words2:
                return 0.0
            
            # Exact match bonus
            if s1 == s2:
                return 1.0
            
            # Substring match
            if s1 in s2 or s2 in s1:
                return 0.75
            
            # Word overlap
            common = words1 & words2
            if common:
                union = words1 | words2
                return len(common) / len(union) * 0.7
            
            return 0.0
        
        normalized_query = normalize_arabic(query)
        best_match = None
        best_score = 0.0
        
        for item in menu_items:
            # Check English name
            score = calc_similarity(query, item.name.lower())
            if score > best_score:
                best_score = score
                best_match = item
            
            # Check Arabic name
            if item.arabic_name:
                normalized_item = normalize_arabic(item.arabic_name)
                score = calc_similarity(normalized_query, normalized_item)
                if score > best_score:
                    best_score = score
                    best_match = item
        
        return best_match, best_score
    
    def _llm_based_menu_matching(self, user_input: str, menu_items: List[MenuItem]) -> tuple[MenuItem, float]:
        """Use LLM to intelligently match user input to menu items with confidence
        
        Args:
            user_input: What the user said
            menu_items: List of available menu items
            
        Returns:
            tuple[MenuItem, float]: (best match, confidence) or (None, 0.0)
        """
        from langchain.schema import HumanMessage
        
        # Build compact menu representation
        menu_repr = []
        for idx, item in enumerate(menu_items):
            menu_repr.append({
                "id": idx,
                "name": item.name,
                "arabic_name": item.arabic_name,
                "category": item.category
            })
        
        prompt = f"""Match user input to menu item. Consider Arabic spelling variations, typos, and phonetic similarities.

User said: "{user_input}"

Available items: {json.dumps(menu_repr, ensure_ascii=False)}

Return JSON ONLY:
{{
  "match_id": <id or null>,
  "confidence": <0.0-1.0>,
  "reasoning": "why this match"
}}

Confidence guide:
- 1.0: Perfect exact match
- 0.9: Very likely (minor spelling variation)
- 0.7: Probable (phonetic similarity, common typo)
- 0.5: Possible but uncertain
- 0.3: Weak match
- 0.0: No match"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = json.loads(response.content.strip())
            
            match_id = result.get("match_id")
            confidence = float(result.get("confidence", 0.0))
            reasoning = result.get("reasoning", "")
            
            if match_id is not None and 0 <= match_id < len(menu_items):
                matched_item = menu_items[match_id]
                logger.info(f"LLM match reasoning: {reasoning}")
                return matched_item, confidence
            else:
                return None, 0.0
                
        except Exception as e:
            logger.error(f"LLM matching error: {e}")
            return None, 0.0
    
    def _aggregate_items(self, items: List[Dict]) -> List[Dict]:
        """Aggregate duplicate items by ID, combining quantities"""
        aggregated = {}
        for item in items:
            item_id = item["id"]
            if item_id in aggregated:
                aggregated[item_id]["quantity"] += item["quantity"]
            else:
                aggregated[item_id] = item.copy()
        return list(aggregated.values())
    
    def _calculate_totals(self, items: List[Dict]) -> Dict:
        subtotal = sum(item["price"] * item["quantity"] for item in items)
        tax = subtotal * 0.15  # 15% KSA tax rate
        delivery_fee = 0.0  # No delivery fee for drive-thru pickup
        total = subtotal + tax + delivery_fee
        
        return {
            "subtotal": round(subtotal, 2),
            "tax": round(tax, 2),
            "delivery_fee": delivery_fee,
            "total": round(total, 2)
        }
    
    def _format_order_summary(self, draft: Dict) -> str:
        """Format order summary with proper line breaks and structure"""
        items_list = []
        for item in draft["items"]:
            items_list.append(f"• {item['quantity']}x {item['name']} ({item['price']:.2f} SAR)")
        
        items_text = "\n".join(items_list)
        
        summary = f""" طلبك الحالي:
{items_text}

 الملخص:
• المجموع الفرعي: {draft['subtotal']:.2f} SAR
• الضريبة: {draft['tax']:.2f} SAR
• رسوم التوصيل: {draft['delivery_fee']:.2f} SAR
----------------
• الإجمالي: {draft['total']:.2f} SAR"""
        
        return summary

    def _parse_json_robustly(self, text: str) -> Dict:
        """Robustly parse JSON from potentially malformed LLM responses
        
        Args:
            text: Raw text that might contain JSON with extra content
            
        Returns:
            Parsed dictionary or empty dict if parsing fails
        """
        import re
        
        if not text or not text.strip():
            return {}
            
        try:
            # First try direct JSON parsing
            return json.loads(text.strip())
        except json.JSONDecodeError:
            try:
                # Try to extract JSON from text that might have extra content
                # Look for JSON-like patterns with nested braces
                json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                matches = re.findall(json_pattern, text)
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
                        
                # Try to extract content between first { and last }
                start_idx = text.find('{')
                end_idx = text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_text = text[start_idx:end_idx+1]
                    return json.loads(json_text)
                    
                logger.warning(f"Could not extract valid JSON from: {text}")
                return {}
            except Exception as e:
                logger.error(f"Error in robust JSON parsing: {e}")
                return {}

    def _filter_message_for_add_only(self, message: str) -> str:
        """Filter message to extract only the ADD part, removing REMOVE keywords and items"""
        try:
            import re
            
            # Find the add part of the message (after واضف or add keywords)
            add_keywords = ['واضف', 'أضف', 'اضف', 'أريد', 'and add', 'add']
            
            for keyword in add_keywords:
                # Look for pattern like 'واضف بطاطس' or 'add fries'
                pattern = rf'{keyword}\s+(.+?)$'
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    add_part = match.group(1).strip()
                    # Clean up common separators
                    add_part = re.sub(r'[,،وو]+$', '', add_part)
                    return add_part
            
            # Fallback: return the original message
            return message
            
        except Exception as e:
            logger.error(f"Error filtering message for add-only: {e}")
            return message
    
    def _extract_items_to_remove(self, message: str) -> List[str]:
        """Extract items to remove from compound messages"""
        try:
            # Look for remove patterns and extract items after them
            import re
            
            # Split message around remove keywords
            remove_keywords = ['احذف', 'حذف', 'شيل', 'remove', 'delete']
            
            items_to_remove = []
            for keyword in remove_keywords:
                # Find patterns like 'احذف المشروب' or 'احذف 1 مشروب غازي'
                pattern = rf'{keyword}\s+(?:\d+\s+)?([\u0600-\u06FF\w\s]+?)(?:،|و|واضف|add|want|$)'
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    # Clean up the match and add to removal list
                    cleaned = match.strip().rstrip('،و')
                    if cleaned:
                        items_to_remove.append(cleaned)
            
            return items_to_remove
        except Exception as e:
            logger.error(f"Error extracting items to remove: {e}")
            return []
    
    def _extract_items_from_message(self, message: str) -> List[str]:
        """Extract item names from message for remove operations"""
        try:
            # Use the same LLM extraction method as for adding items
            return self._extract_items_with_llm(message)
        except Exception as e:
            logger.error(f"Error extracting items from message: {e}")
            return []
    
    def _find_similar_items(self, item_name: str) -> List[str]:
        """Find similar items for suggestions using intelligent matching"""
        try:
            if not isinstance(item_name, str) or not item_name:
                return []
            
            item_lower = item_name.lower().strip()
            
            # Normalize Arabic text
            def normalize_arabic(text):
                import re
                arabic_diacritics = re.compile(r'[\u064B-\u065F\u0670]')
                text = arabic_diacritics.sub('', text)
                text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
                text = text.replace('ة', 'ه')
                return text.lower().strip()
            
            normalized_item = normalize_arabic(item_lower)
            
            # Enhanced category mappings
            category_hints = {
                'فرويز': 'Sides',
                'فرايز': 'Sides',
                'بطاطس': 'Sides',
                'بطاطا': 'Sides',
                'سودا': 'Beverages',
                'صودا': 'Beverages',
                'مشروب': 'Beverages',
                'عصير': 'Beverages',
                'برجر': 'Burgers',
                'برغر': 'Burgers',
                'بيتزا': 'Pizza',
                'دجاج': 'Chicken',
                'وينجز': 'Sides',
                'أجنحة': 'Sides',
                'سلطة': 'Sides'
            }
            
            suggestions = []
            matched_categories = []
            
            # Find categories based on keywords
            for hint, category in category_hints.items():
                if normalize_arabic(hint) in normalized_item or normalized_item in normalize_arabic(hint):
                    matched_categories.append(category)
            
            # Get items from matched categories
            if matched_categories:
                for category in matched_categories:
                    items = self.db.query(MenuItem).filter(
                        MenuItem.category == category,
                        MenuItem.is_available == True
                    ).limit(3).all()
                    suggestions.extend([item.arabic_name or item.name for item in items])
                    if len(suggestions) >= 3:
                        break
            
            # If no category match, try fuzzy matching on all items
            if not suggestions:
                def similarity_score(s1, s2):
                    s1, s2 = normalize_arabic(s1), normalize_arabic(s2)
                    if s1 in s2 or s2 in s1:
                        return 0.8
                    words1 = set(s1.split())
                    words2 = set(s2.split())
                    if words1 & words2:
                        return len(words1 & words2) / max(len(words1), len(words2)) * 0.6
                    return 0.0
                
                all_items = self.db.query(MenuItem).filter(
                    MenuItem.is_available == True
                ).all()
                
                scored_items = []
                for item in all_items:
                    if item.arabic_name:
                        score = similarity_score(item_lower, item.arabic_name)
                        if score > 0.3:
                            scored_items.append((score, item.arabic_name or item.name))
                
                # Sort by score and take top 3
                scored_items.sort(reverse=True)
                suggestions = [name for _, name in scored_items[:3]]
            
            # If still no suggestions, return popular items from common categories
            if not suggestions:
                popular_categories = ['Burgers', 'Sides', 'Beverages']
                for category in popular_categories:
                    items = self.db.query(MenuItem).filter(
                        MenuItem.category == category,
                        MenuItem.is_available == True
                    ).limit(1).all()
                    suggestions.extend([item.arabic_name or item.name for item in items])
                    if len(suggestions) >= 3:
                        break
            
            return suggestions[:3]
        except Exception as e:
            logger.warning(f"Error finding similar items: {e}")
            return []
