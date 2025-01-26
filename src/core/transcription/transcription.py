import os
from dotenv import load_dotenv
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechRecognizer
from azure.cognitiveservices.speech.audio import PullAudioInputStreamCallback
import requests
from pytube import YouTube
from pydub import AudioSegment
import tempfile

# Load environment variables from .env
load_dotenv()

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

if not AZURE_SPEECH_KEY or not AZURE_REGION:
    raise ValueError("Azure Speech key or region is not set in the .env file.")

# Helper function to download audio from YouTube
def download_audio_from_url(url: str) -> str:
    """Downloads audio from a YouTube URL and converts it to WAV format."""
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        print(f"Downloading audio: {yt.title}")
        audio_file = stream.download()
        
        # Convert to WAV format using pydub
        print("Converting audio to WAV format...")
        audio = AudioSegment.from_file(audio_file)
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        audio.export(temp_wav.name, format="wav")
        
        return temp_wav.name
    except Exception as e:
        raise RuntimeError(f"Failed to download or convert audio: {str(e)}")

# Transcription function
def transcribe_audio(audio_path: str) -> str:
    """Transcribes audio to text using Azure Speech Service."""
    speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = AudioConfig(filename=audio_path)
    speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Starting transcription...")
    result = speech_recognizer.recognize_once()

    if result.reason == result.Reason.RecognizedSpeech:
        print("Transcription successful!")
        return result.text
    elif result.reason == result.Reason.NoMatch:
        print("No speech could be recognized.")
        return ""
    else:
        print(f"Speech recognition failed. Reason: {result.reason}")
        return ""

# Main function
def process_audio_from_url(url: str) -> str:
    """Processes audio from a URL and returns the transcription."""
    try:
        # Download and prepare audio
        audio_path = download_audio_from_url(url)
        
        # Transcribe the audio
        transcription = transcribe_audio(audio_path)
        
        # Clean up temporary audio file
        os.remove(audio_path)
        
        return transcription
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return ""

# Example Usage
if __name__ == "__main__":
    # Replace this with the actual URL of a YouTube video or other audio source
    youtube_url = "https://www.youtube.com/watch?v=your_video_id"
    transcription = process_audio_from_url(youtube_url)
    
    if transcription:
        print("\nTranscription:")
        print(transcription)
    else:
        print("No transcription available.")
