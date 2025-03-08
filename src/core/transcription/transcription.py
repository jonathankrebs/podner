import os
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechRecognizer
import yt_dlp
import tempfile
import json
from datetime import datetime, timezone
from moviepy import AudioFileClip
from typing import TypedDict, Optional
from ...utils.date_utils import to_iso_date
from ...models.types import TranscriptionData

# Load environment variables from .env
load_dotenv()

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

if not AZURE_SPEECH_KEY or not AZURE_REGION:
    raise ValueError("Azure Speech key or region is not set in the .env file.")

class AudioDLData(TypedDict):
    source_url: str
    audio_file_path: str
    audio_source_date: Optional[str]
    duration_string: Optional[str]
    language: Optional[str]
    title: Optional[str]

def download_audio_from_yt(url: str) -> AudioDLData:
    """Downloads audio from a YouTube URL and converts it to WAV format using yt-dlp."""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define yt-dlp options with a proper outtmpl template
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "quiet": True, 
            }

        print(f"Downloading audio from: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info_dict)

        # Create a temporary file for the WAV output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
            wav_path = temp_wav_file.name

        # Convert downloaded audio to WAV using moviepy
        print("Converting audio to WAV format...")
        audio_clip = AudioFileClip(downloaded_file)
        audio_clip.write_audiofile(wav_path, codec="pcm_s16le")
        audio_clip.close()

        # Retrieve meta information
        audio_dl_data: AudioDLData = {
            "source_url": info_dict["original_url"],
            "audio_file_path": wav_path,
            "audio_source_date": to_iso_date(info_dict["upload_date"]),
            "duration_string": info_dict["duration_string"],
            "language": info_dict["language"],
            "title": info_dict["title"]
        }

        # Clean up the intermediate .webm file
        os.remove(downloaded_file)
        
        return audio_dl_data
    except Exception as e:
        raise RuntimeError(f"Failed to download or convert audio: {str(e)}")

def transcribe_audio(audio_dl_data: AudioDLData) -> TranscriptionData:
    """Transcribes audio to text using Azure Speech Service."""
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_path = audio_dl_data["audio_file_path"]
    audio_config = AudioConfig(filename=audio_path)
    speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    audio_file_name = os.path.basename(audio_path)
    print(f"Starting transcription of file {audio_file_name}")
    # TODO: replace by .start_continuous_recognition_async for audio files > 30s
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Transcription successful!")
        transcription_data: TranscriptionData = {
            "source_url": audio_dl_data["source_url"],
            "transcription_text": result.text,
            "transcription_date": datetime.now(timezone.utc).isoformat(),
            "audio_source_date": audio_dl_data["audio_source_date"],
            "duration_string": audio_dl_data["duration_string"],
            "language": audio_dl_data["language"],
            "title": audio_dl_data["title"]
        }

        return transcription_data
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized.")
        return {}
    else:
        print(f"Speech recognition failed. Reason: {result.reason}")
        return {}

# TODO: instead of saving to a local json file, save to a document db (e.g. local mongodb or cloud cosmosdb)
def save_transcription_to_json(transcription_data: TranscriptionData) -> str:
    transcription_dir = "data/transcriptions"
    json_filename = f"transcription_{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")}.json"
    json_filepath = os.path.join(transcription_dir, json_filename)
    with open(json_filepath, "w", encoding="utf-8") as json_file:
        json.dump(transcription_data, json_file, ensure_ascii=False, indent=4)
    print(f"Transcription saved to {json_filepath}")
    return json_filepath

def process_audio_from_url(url: str) -> TranscriptionData:
    """Processes audio from a URL and returns the transcription file path"""
    try:
        audio_dl_data: AudioDLData = download_audio_from_yt(url)
        transcription_data = transcribe_audio(audio_dl_data)
        if transcription_data:
            save_transcription_to_json(transcription_data)

        # Clean up temporary audio file
        os.remove(audio_dl_data["audio_file_path"])
        
        return transcription_data
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return ""

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=B9vR1MDuEGk"
    transcription_data = process_audio_from_url(youtube_url)
    
    if transcription_data:
        print("\nTranscription:")
        print(transcription_data["transcription_text"])
    else:
        print("No transcription available.")
