"""
Audio API routes for MoatTutor backend.

Provides endpoints for audio translation using OpenAI Whisper API.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from openai import OpenAI
from pydantic import BaseModel

from config import get_settings

router = APIRouter(prefix="/api/audio", tags=["audio"])

# Supported audio formats
SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}
SUPPORTED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/wav",
    "audio/webm",
    "audio/m4a",
    "audio/mpga",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class TranslationResponse(BaseModel):
    """Response model for audio translation."""
    
    success: bool
    text: Optional[str] = None
    message: str


def validate_audio_file(file: UploadFile) -> None:
    """
    Validate uploaded audio file.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If file validation fails
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Optionally validate MIME type (non-blocking)
    if file.content_type and file.content_type not in SUPPORTED_MIME_TYPES:
        # Log warning but don't block (some browsers send incorrect MIME types)
        print(f"Warning: Unexpected MIME type {file.content_type} for {file.filename}")


@router.post("/translate", response_model=TranslationResponse)
async def translate_audio(
    file: UploadFile = File(..., description="Audio file to translate"),
    model: str = Form(default="whisper-1", description="Model to use (only whisper-1 supported)"),
    response_format: str = Form(default="text", description="Response format (text or json)"),
    prompt: Optional[str] = Form(default=None, description="Optional prompt to guide translation"),
    temperature: Optional[float] = Form(default=None, description="Sampling temperature (0.0-1.0)"),
) -> TranslationResponse:
    """
    Translate audio from any language to English using OpenAI Whisper API.
    
    This endpoint accepts an audio file and translates it to English text.
    The translation is performed using OpenAI's Whisper model.
    
    Args:
        file: Audio file (mp3, mp4, mpeg, mpga, m4a, wav, webm)
        model: Model to use (only "whisper-1" is supported)
        response_format: Output format ("text" or "json")
        prompt: Optional context to guide translation
        temperature: Optional sampling temperature (0.0-1.0)
        
    Returns:
        TranslationResponse with translated text
        
    Raises:
        HTTPException: If validation fails or API call errors
    """
    # Validate file
    validate_audio_file(file)
    
    # Read file content
    try:
        audio_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read uploaded file: {str(e)}"
        )
    
    # Check file size
    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )
    
    # Get settings and create OpenAI client
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Create temporary file with proper cleanup (Windows-compatible)
    tmp_file_path = None
    file_handle = None
    
    try:
        # Step 1: Create temporary file and write bytes
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=Path(file.filename).suffix
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            tmp_file_path = tmp_file.name
        
        # Step 2: Open file separately (outside with block to avoid Windows file locking)
        file_handle = open(tmp_file_path, "rb")
        
        # Step 3: Call OpenAI API
        translation = client.audio.translations.create(
            file=file_handle,
            model=model,
            response_format=response_format,
            prompt=prompt,
            temperature=temperature,
        )
        
        # Step 4: Extract text from response
        if response_format == "text":
            translated_text = translation
        else:
            translated_text = translation.text if hasattr(translation, "text") else str(translation)
        
        return TranslationResponse(
            success=True,
            text=translated_text,
            message="Translation completed successfully"
        )
        
    except Exception as e:
        # Handle OpenAI API errors
        error_msg = str(e)
        if "openai" in error_msg.lower() or "api" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail=f"OpenAI API error: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Translation failed: {error_msg}"
            )
    
    finally:
        # Step 5: Cleanup - close file handle FIRST, then delete
        if file_handle:
            file_handle.close()
        
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                # Log but don't fail the request if cleanup fails
                print(f"Warning: Failed to delete temporary file {tmp_file_path}: {e}")

