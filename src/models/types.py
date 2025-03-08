from typing import TypedDict, Optional
from datetime import datetime

class TranscriptionData:
    source_url: str
    transcription_text: str
    transcription_date: str
    audio_source_date: Optional[str]
    duration_string: Optional[str]
    language: Optional[str]
    title: Optional[str]