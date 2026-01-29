from fastapi import APIRouter, UploadFile, File, HTTPException
from src.utils.llm_helpers import get_openai_client
import tempfile
import os
from langsmith import traceable

router = APIRouter()

@router.post("/voice-to-text")
@traceable(name="voice_to_text")
async def voice_to_text(audio: UploadFile = File(...)):
    """
    Convert Arabic voice audio to text using Whisper API
    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
    """
    # Accept both audio/* and empty content types (some browsers send empty for webm)
    valid_content_types = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "video/webm"]
    if audio.content_type and not any(ct in audio.content_type for ct in valid_content_types):
        # Only reject if content type is present and invalid
        if not audio.content_type.startswith("audio/") and not audio.content_type.startswith("video/"):
            raise HTTPException(status_code=400, detail=f"Invalid content type: {audio.content_type}. Expected audio file.")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Get singleton OpenAI client
        client = get_openai_client()
        
        # Transcribe using Whisper with Arabic language hint
        with open(tmp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ar",  # Arabic language hint
                response_format="text"
            )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return {
            "success": True,
            "text": transcript,
            "language": "ar"
        }
        
    except Exception as e:
        # Clean up temp file on error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
