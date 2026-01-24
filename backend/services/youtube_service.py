import yt_dlp
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
from requests.exceptions import ConnectionError, Timeout, HTTPError
import subprocess
import os
import runpod
from datetime import datetime
import asyncio
import json
import tempfile
import shutil
import base64
import requests
from dotenv import load_dotenv
from typing import Any, Dict, Tuple

# Load environment variables
load_dotenv()

# ================= Configuration =================
IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"
IMAGEKIT_DELETE_URL = "https://api.imagekit.io/v1/files"

# Environment variables
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")

# ================= Helper Functions =================


def _validate_environment() -> None:
    """Validate that all required environment variables are set."""
    required_vars = {
        "RUNPOD_API_KEY": RUNPOD_API_KEY,
        "RUNPOD_ENDPOINT_ID": RUNPOD_ENDPOINT_ID,
        "IMAGEKIT_PRIVATE_KEY": IMAGEKIT_PRIVATE_KEY,
        "IMAGEKIT_URL_ENDPOINT": IMAGEKIT_URL_ENDPOINT
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")


def _get_video_id(video_url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    if not isinstance(video_url, str):
        raise TypeError(f"Expected a string for URL, got {type(video_url).__name__} instead.")

    try:
        if "v=" in video_url:
            return video_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in video_url:
            return video_url.split("/")[-1]
        else:
            raise ValueError("URL does not appear to be a valid YouTube link.")
    except ValueError as e:
        raise ValueError(f"Invalid YouTube URL: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error extracting video ID: {e}")


def _extract_youtube_transcript(video_id: str) -> str:
    """Retrieve the full transcript from YouTube captions, if available."""
    if not isinstance(video_id, str):
        raise TypeError(f"Expected a string for video id, got {type(video_id).__name__} instead.")

    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        full_text = " ".join([segment["text"] for segment in fetched.to_raw_data()])
        return full_text

    except VideoUnavailable as e:
        raise VideoUnavailable(f"Video {video_id} is unavailable: {e}")
    except TranscriptsDisabled as e:
        raise TranscriptsDisabled(f"Video {video_id} has transcript disabled: {e}")
    except NoTranscriptFound as e:
        raise NoTranscriptFound(f"No transcript found for video {video_id}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error getting transcript for {video_id}: {e}")


# ================= Audio Processing Functions =================
async def _download_audio_ytdlp(video_url: str, output_dir: str) -> str:
    """Download audio from YouTube using yt-dlp."""
    if not isinstance(video_url, str):
        raise TypeError(f"Expected a string for video URL, got {type(video_url).__name__} instead.")

    filename = _get_video_id(video_url)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, f'video_{filename}_{current_time}.%(ext)s'),
        'extractaudio': True,
        'audioformat': 'mp4',
        'quiet': True,
    }

    try:
        def download_sync():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                
                # Find the downloaded file
                for file in os.listdir(output_dir):
                    if file.startswith(f'video_{filename}_{current_time}'):
                        return os.path.join(output_dir, file)
                
                raise RuntimeError("Downloaded file not found")
        
        audio_file = await asyncio.to_thread(download_sync)
        return audio_file
        
    except Exception as e:
        raise RuntimeError(f"Error downloading audio with yt-dlp: {e}")


async def _convert_to_wav(input_file_path: str) -> str:
    """Convert audio to WAV format suitable for transcription."""
    if not isinstance(input_file_path, str):
        raise TypeError("input_file_path must be a string.")

    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file does not exist: {input_file_path}")

    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    dir_name = os.path.dirname(input_file_path)
    output_file_path = os.path.join(dir_name, f"{base_name}.wav")

    def ffmpeg_convert():
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file_path,
            "-ar", "16000", "-ac", "1", output_file_path
        ], check=True, capture_output=True)
        return output_file_path

    try:
        wav_file = await asyncio.to_thread(ffmpeg_convert)
        return wav_file

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error converting to WAV: {e}")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
    except Exception as e:
        raise RuntimeError(f"Unexpected error converting audio to WAV: {e}")


# ================= ImageKit Functions =================
def _upload_wav_to_imagekit(local_wav_path: str) -> Tuple[str, str]:
    """Upload WAV file to ImageKit and return URL and file ID."""
    if not os.path.exists(local_wav_path):
        raise FileNotFoundError(local_wav_path)

    auth = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()

    with open(local_wav_path, "rb") as f:
        response = requests.post(
            IMAGEKIT_UPLOAD_URL,
            headers={"Authorization": f"Basic {auth}"},
            files={"file": f},
            data={
                "fileName": os.path.basename(local_wav_path),
                "useUniqueFileName": "true"
            }
        )

    if response.status_code != 200:
        raise RuntimeError(f"ImageKit upload failed: {response.text}")

    data = response.json()
    return data["url"], data["fileId"]


def _delete_from_imagekit(file_id: str) -> None:
    """Delete file from ImageKit."""
    auth = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()

    response = requests.delete(
        f"{IMAGEKIT_DELETE_URL}/{file_id}",
        headers={"Authorization": f"Basic {auth}"}
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(f"ImageKit delete failed: {response.text}")


# ================= RunPod Transcription =================
async def _transcribe_with_runpod(audio_url: str) -> Dict[str, Any]:
    """Send audio file to RunPod Whisper endpoint for transcription."""
    if not isinstance(audio_url, str):
        raise TypeError("audio_url must be a string.")

    try:
        runpod.api_key = RUNPOD_API_KEY
        
        # Create endpoint object
        endpoint = runpod.Endpoint(RUNPOD_ENDPOINT_ID)
        
        # Health check to warm up serverless endpoint
        try:
            health = endpoint.health()
        except Exception:
            pass  # Health check failure is not critical
        
        # Use the correct input format for Faster Whisper endpoint
        runpod_input = {
            "input": {
                "audio": audio_url,     # Required: audio file URL
                "model": "turbo"        # Optional: model selection
            }
        }
        
        # Synchronous call with timeout
        result = endpoint.run_sync(runpod_input, timeout=180)
        
        if result is None:
            return {"transcript": "", "status": "failed", "error": "RunPod returned None"}
        
        return result

    except (ConnectionError, Timeout, HTTPError) as e:
        raise RuntimeError(f"Network or API error when calling RunPod: {e}")
    except Exception as e:
        raise RuntimeError(f"Error transcribing with RunPod service: {e}")


# ================= Main Function =================
async def fetch_transcript(video_url: str) -> Dict[str, Any]:
    """
    Main function to fetch transcript from YouTube video.
    
    First tries to get transcript from YouTube captions.
    If not available, downloads audio and transcribes using RunPod.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        Dictionary containing transcript and metadata
        
    Raises:
        ValueError: If video URL is invalid
        RuntimeError: If transcription fails
    """
    _validate_environment()
    
    video_id = _get_video_id(video_url)
    
    # Try YouTube transcript first
    try:
        transcript = _extract_youtube_transcript(video_id)
        if transcript:
            return {
                "transcript": transcript,
                "source": "youtube_captions",
                "video_id": video_id,
                "status": "completed"
            }
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, RuntimeError):
        # Continue to audio transcription if captions not available
        pass

    # Fallback to audio transcription
    temp_dir = tempfile.mkdtemp(prefix=f"yt_etl_{video_id}_")
    try:
        # Download and convert audio
        audio_file = await _download_audio_ytdlp(video_url, temp_dir)
        wav_file = await _convert_to_wav(audio_file)
        
        # Upload to ImageKit
        audio_url, file_id = _upload_wav_to_imagekit(wav_file)
        
        try:
            # Transcribe with RunPod
            result = await _transcribe_with_runpod(audio_url)
            
            # Add metadata
            result.update({
                "source": "audio_transcription",
                "video_id": video_id
            })
            
            # Extract clean transcript text if available
            if "transcription" in result:
                result["transcript"] = result["transcription"]
            
            return result
            
        finally:
            # Clean up ImageKit file
            _delete_from_imagekit(file_id)
            
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
