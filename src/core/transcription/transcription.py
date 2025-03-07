import os
from dotenv import load_dotenv
from azure.cognitiveservices.speech import SpeechConfig, AudioConfig, SpeechRecognizer
from azure.cognitiveservices.speech.audio import PullAudioInputStreamCallback
import yt_dlp
import tempfile
import json
import datetime
from moviepy import AudioFileClip

# Load environment variables from .env
load_dotenv()

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_REGION = os.getenv("AZURE_REGION")

if not AZURE_SPEECH_KEY or not AZURE_REGION:
    raise ValueError("Azure Speech key or region is not set in the .env file.")

def download_audio_from_url(url: str) -> str:
    """Downloads audio from a YouTube URL and converts it to WAV format using yt-dlp."""
    try:
        # Define yt-dlp options
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define yt-dlp options with a proper outtmpl template
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),  # Template for output filename
                'quiet': True,  # Suppress yt-dlp output
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
        audio_clip.write_audiofile(wav_path, codec='pcm_s16le')
        audio_clip.close()

        # Clean up the intermediate .webm file
        os.remove(downloaded_file)
        
        return wav_path
    except Exception as e:
        raise RuntimeError(f"Failed to download or convert audio: {str(e)}")

def transcribe_audio(audio_path: str) -> str:
    """Transcribes audio to text using Azure Speech Service."""
    # speech_config = SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    # audio_config = AudioConfig(filename=audio_path)
    # speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    # audio_file_name = os.path.basename(audio_path)
    # print(f"Starting transcription of file {audio_file_name}")
    # # TODO: replace by .start_continuous_recognition_async for audio files > 30s
    # result = speech_recognizer.recognize_once()

    # if result.reason == result.Reason.RecognizedSpeech:
    #     print("Transcription successful!")
    #     return result.text
    # elif result.reason == result.Reason.NoMatch:
    #     print("No speech could be recognized.")
    #     return ""
    # else:
    #     print(f"Speech recognition failed. Reason: {result.reason}")
    #     return ""
    return "This is a test ABCBCAIBCITSENRDI"

def save_transcription_to_json(transcription: str) -> str:
    transcription_data = {
            "source_url": youtube_url,
            "transcription_text": transcription,
            # "audio_filename": os.path.basename(audio_path) if audio_path else None,
            "audio_filename": "test.wav", # TODO: pass meta info
            "transcription_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "audio_source_date": "07-03-2025", # TODO: read from info_dict?
            "duration_seconds": "1min 30s" # TODO: read from info_dict?
    }

    transcription_dir = "data/transcriptions"
    json_filename = f"transcription_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
    json_filepath = os.path.join(transcription_dir, json_filename)
    with open(json_filepath, "w", encoding="utf-8") as json_file:
        json.dump(transcription_data, json_file, ensure_ascii=False, indent=4)
    print(f"Transcription saved to {json_filepath}")
    return json_filepath

def process_audio_from_url(url: str) -> str:
    """Processes audio from a URL and returns the transcription file path"""
    try:
        audio_path = download_audio_from_url(url)
        transcription = transcribe_audio(audio_path)
        if transcription:
            return save_transcription_to_json(transcription)

        # Clean up temporary audio file
        os.remove(audio_path)
        
        return transcription
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return ""

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/watch?v=B9vR1MDuEGk"
    transcription = process_audio_from_url(youtube_url)
    
    if transcription:
        print("\nTranscription:")
        print(transcription)
    else:
        print("No transcription available.")
