"""
Voice Transcription Service using Local Whisper Model
Optimized for Arabic language transcription
Uses locally installed Whisper from https://github.com/openai/whisper

OPTIMIZATION: Singleton pattern for Whisper model to avoid reloading on every request
"""
import whisper
import tempfile
import os
from typing import Optional
from src.config import settings
import logging

logger = logging.getLogger(__name__)

# Singleton instance for the transcription service
_transcription_service_instance = None
_whisper_model = None

def get_transcription_service():
    """Get singleton instance of VoiceTranscriptionService - avoids reloading model"""
    global _transcription_service_instance
    if _transcription_service_instance is None:
        _transcription_service_instance = VoiceTranscriptionService()
    return _transcription_service_instance

def _get_whisper_model():
    """Lazy load Whisper model as singleton - CRITICAL for performance"""
    global _whisper_model
    if _whisper_model is None:
        model_size = settings.whisper_model_size
        logger.info(f"Loading Whisper model ({model_size})... (one-time initialization)")
        print(f"Loading Whisper model ({model_size})...")
        _whisper_model = whisper.load_model(model_size)
        logger.info(f"Whisper model ({model_size}) loaded successfully!")
        print(f"Whisper model ({model_size}) loaded successfully!")
    return _whisper_model


class VoiceTranscriptionService:
    def __init__(self):
        # Use singleton model - only loads once across all instances
        self.model = _get_whisper_model()
    
    def transcribe(
        self, 
        audio_path: str, 
        language: str = "ar",
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio to text using local Whisper model
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: 'ar' for Arabic)
            prompt: Optional context prompt to improve accuracy
            
        Returns:
            dict with 'text' and 'language' keys
        """
        try:
            # Default prompt for Arabic food ordering context
            if not prompt:
                prompt = "طلب طعام، برجر، بيتزا، بطاطس، مشروب"
            
            print(f"Transcribing audio file: {audio_path}")
            
            # Transcribe using local Whisper model
            result = self.model.transcribe(
                audio_path,
                language=language,
                initial_prompt=prompt,
                fp16=False  # Use fp32 for better compatibility
            )
            
            transcribed_text = result["text"].strip()
            
            # # Check audio duration and transcription length
            # duration = result.get("duration", 0)
            # if duration < 0.2:  # Less than 0.2 seconds
            #     return {
            #         "success": False,
            #         "error": "Audio too short. Please speak for at least 200ms.",
            #         "text": "",
            #         "language": language
            #     }
            
            # # Check if transcription is empty or too short
            # if not transcribed_text or len(transcribed_text) < 2:
            #     return {
            #         "success": False,
            #         "error": "No speech detected. Please speak clearly.",
            #         "text": "",
            #         "language": language
            #     }
            
            print(f"Transcription successful: {transcribed_text[:100]}...")
            
            return {
                "text": transcribed_text,
                "language": result.get("language", language),
                "success": True
            }
            
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return {
                "text": "",
                "language": language,
                "success": False,
                "error": str(e)
            }
    
    def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        language: str = "ar"
    ) -> dict:
        """
        Transcribe audio from bytes
        
        Args:
            audio_bytes: Audio data as bytes
            filename: Filename with extension (for format detection)
            language: Language code
            
        Returns:
            Transcription result dict
        """
        # Save bytes to temporary file since local Whisper needs a file path
        temp_file = None
        try:
            # Create temporary file with appropriate extension
            suffix = os.path.splitext(filename)[1] or '.webm'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(audio_bytes)
            temp_file.close()
            
            print(f"Saved audio to temp file: {temp_file.name} ({len(audio_bytes)} bytes)")
            
            # Transcribe the temporary file
            result = self.transcribe(temp_file.name, language=language)
            
            return result
            
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                    print(f"Cleaned up temp file: {temp_file.name}")
                except Exception as e:
                    print(f"Warning: Could not delete temp file: {e}")
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect language from audio
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Language code (e.g., 'ar', 'en')
        """
        try:
            # Transcribe without language constraint to detect it
            result = self.model.transcribe(audio_path, fp16=False)
            detected_lang = result.get('language', 'ar')
            print(f"Detected language: {detected_lang}")
            return detected_lang
            
        except Exception as e:
            print(f"Language detection error: {e}")
            return 'ar'  # Default to Arabic
