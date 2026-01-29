from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.api.routes import conversation, customer
from src.models.db_session import init_db
import asyncio
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Service Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
app.include_router(customer.router, prefix="/api", tags=["customer"])

# Serve static files from the built frontend
app.mount("/", StaticFiles(directory="src/static", html=True), name="static")

# Background task to update order statuses
async def update_order_statuses():
    """Background task to update order statuses to READY after 1 minute"""
    from src.models.db_session import SessionLocal
    from src.models.database import Order
    from src.models.enums import OrderStatus
    from datetime import datetime
    
    while True:
        try:
            await asyncio.sleep(10)  # Check every 10 seconds
            db = SessionLocal()
            try:
                # Update orders that are ready
                orders = db.query(Order).filter(
                    Order.status == OrderStatus.PENDING,
                    Order.estimated_ready_time <= datetime.utcnow()
                ).all()
                
                for order in orders:
                    order.status = OrderStatus.READY
                    print(f"Order {order.order_number} is now READY")
                
                if orders:
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            print(f"Error updating order statuses: {e}")


async def preload_models():
    """Preload all heavy models at startup for faster first request"""
    import time
    start = time.time()
    
    print("🚀 Preloading models for faster responses...")
    
    # Preload Whisper model (singleton)
    try:
        from src.services.voice_transcription import get_transcription_service
        get_transcription_service()
        print("✓ Whisper model loaded")
    except Exception as e:
        logger.warning(f"Failed to preload Whisper: {e}")
    
    # Preload LLM instances (singletons)
    try:
        from src.services.intent_detection import _get_fast_llm
        _get_fast_llm()
        print("✓ Intent detection LLM loaded")
    except Exception as e:
        logger.warning(f"Failed to preload intent LLM: {e}")
    
    try:
        from src.services.menu_agent import _get_menu_llm
        _get_menu_llm()
        print("✓ Menu agent LLM loaded")
    except Exception as e:
        logger.warning(f"Failed to preload menu LLM: {e}")
    
    try:
        from src.services.order_processing_agent import _get_order_llm
        _get_order_llm()
        print("✓ Order processing LLM loaded")
    except Exception as e:
        logger.warning(f"Failed to preload order LLM: {e}")
    
    elapsed = time.time() - start
    print(f"✅ All models preloaded in {elapsed:.2f}s - ready for fast responses!")


@app.on_event("startup")
async def startup_event():
    init_db()
    # Preload models in background to not block startup
    asyncio.create_task(preload_models())
    # Start background task
    asyncio.create_task(update_order_statuses())
