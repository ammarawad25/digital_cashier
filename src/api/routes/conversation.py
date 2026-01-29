from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from src.models.db_session import get_db
from src.models.schemas import ConversationRequest, ConversationResponse
from src.services.orchestrator import ConversationOrchestrator
from src.services.voice_transcription import get_transcription_service
from typing import Optional

router = APIRouter()

@router.post("/message", response_model=ConversationResponse)
async def process_conversation_message(
    request: ConversationRequest,
    db: Session = Depends(get_db)
):
    try:
        orchestrator = ConversationOrchestrator(db)
        
        if not request.customer_phone:
            raise HTTPException(status_code=400, detail="customer_phone is required")
        
        response = orchestrator.process_message(
            message=request.message,
            customer_phone=request.customer_phone,
            session_id=request.session_id
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/voice")
async def process_voice_message(
    audio: UploadFile = File(...),
    customer_phone: str = Form(...),
    session_id: Optional[str] = Form(None),
    language: str = Form("ar"),
    db: Session = Depends(get_db)
):
    """
    Process voice message - transcribe and handle conversation
    
    Args:
        audio: Audio file (webm, mp3, wav, etc.)
        customer_phone: Customer phone number
        session_id: Optional session ID for continuing conversation
        language: Language code (default: 'ar' for Arabic)
    
    Returns:
        Transcription and conversation response
    """
    import traceback
    
    try:
        # Log request details
        print(f"Voice endpoint called: phone={customer_phone}, language={language}, filename={audio.filename}, content_type={audio.content_type}")
        
        # Validate inputs
        if not customer_phone or customer_phone.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="customer_phone is required and cannot be empty"
            )
        
        # Read audio file
        audio_bytes = await audio.read()
        print(f"Audio bytes received: {len(audio_bytes)} bytes")
        
        # Validate audio data
        if not audio_bytes or len(audio_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail="Audio file is empty or invalid"
            )
        
        # Transcribe audio using SINGLETON service (model already loaded)
        print("Starting transcription...")
        transcription_service = get_transcription_service()
        transcription_result = transcription_service.transcribe_from_bytes(
            audio_bytes=audio_bytes,
            filename=audio.filename,
            language=language
        )
        
        print(f"Transcription result: success={transcription_result['success']}, text={transcription_result.get('text', '')[:100]}")
        
        if not transcription_result["success"]:
            error_detail = f"Transcription failed: {transcription_result.get('error')}"
            print(f"ERROR: {error_detail}")
            raise HTTPException(
                status_code=400, 
                detail=error_detail
            )
        
        # Sanitize transcription text
        transcribed_text = transcription_result["text"].strip()
        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="Transcription resulted in empty text. Please speak more clearly."
            )
        
        # Process conversation
        orchestrator = ConversationOrchestrator(db)
        response = orchestrator.process_message(
            message=transcribed_text,
            customer_phone=customer_phone,
            session_id=session_id,
            language=language
        )
        
        return {
            "transcription": transcribed_text,
            "language": transcription_result["language"],
            "response": response.response,
            "session_id": response.session_id,
            "conversation_state": response.conversation_state,
            "confidence": response.confidence,
            "intent": response.intent,
            "order_draft": response.order_draft,
            "order_cleared": response.order_cleared,  # Include order_cleared flag for UI
            "order_number": response.order_number,  # Include order number
            "receipt_data": response.receipt_data  # Include receipt data for table display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "customer_phone": customer_phone,
            "language": language
        }
        print(f"Voice endpoint error: {error_details}")  # For debugging
        raise HTTPException(
            status_code=500, 
            detail=f"Server error processing voice: {str(e)}"
        )

