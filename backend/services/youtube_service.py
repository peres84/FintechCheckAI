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

# Import logging
from backend.core.logging import log_handler

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
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


def _get_video_id(video_url: str) -> str:
    """Extract the video ID from a YouTube URL."""
    if not isinstance(video_url, str):
        error_msg = f"Expected a string for URL, got {type(video_url).__name__} instead."
        log_handler.error(error_msg)
        raise TypeError(error_msg)

    try:
        if "v=" in video_url:
            video_id = video_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1]
        else:
            error_msg = "URL does not appear to be a valid YouTube link."
            log_handler.error(f"Invalid YouTube URL: {video_url}")
            raise ValueError(error_msg)
        
        log_handler.debug(f"Extracted video ID: {video_id} from URL: {video_url}")
        return video_id
        
    except ValueError as e:
        error_msg = f"Invalid YouTube URL: {e}"
        log_handler.error(error_msg)
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error extracting video ID: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


def _extract_youtube_transcript(video_id: str) -> str:
    """Retrieve the full transcript from YouTube captions, if available."""
    if not isinstance(video_id, str):
        error_msg = f"Expected a string for video id, got {type(video_id).__name__} instead."
        log_handler.error(error_msg)
        raise TypeError(error_msg)

    log_handler.info(f"Attempting to extract YouTube transcript for video ID: {video_id}")
    
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        full_text = " ".join([segment["text"] for segment in fetched.to_raw_data()])
        
        log_handler.info(f"Successfully extracted transcript from YouTube captions for video {video_id}")
        log_handler.debug(f"Transcript length: {len(full_text)} characters")
        return full_text

    except VideoUnavailable as e:
        error_msg = f"Video {video_id} is unavailable: {e}"
        log_handler.warning(error_msg)
        raise VideoUnavailable(error_msg)
    except TranscriptsDisabled as e:
        error_msg = f"Video {video_id} has transcript disabled: {e}"
        log_handler.warning(error_msg)
        raise TranscriptsDisabled(error_msg)
    except NoTranscriptFound as e:
        error_msg = f"No transcript found for video {video_id}: {e}"
        log_handler.warning(error_msg)
        raise NoTranscriptFound(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error getting transcript for {video_id}: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


# ================= Audio Processing Functions =================
async def _download_audio_ytdlp(video_url: str, output_dir: str) -> str:
    """Download audio from YouTube using yt-dlp."""
    if not isinstance(video_url, str):
        error_msg = f"Expected a string for video URL, got {type(video_url).__name__} instead."
        log_handler.error(error_msg)
        raise TypeError(error_msg)

    filename = _get_video_id(video_url)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    log_handler.info(f"Starting audio download for video {filename} using yt-dlp")
    
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
                        file_path = os.path.join(output_dir, file)
                        log_handler.info(f"Audio download completed: {file_path}")
                        return file_path
                
                error_msg = "Downloaded file not found"
                log_handler.error(error_msg)
                raise RuntimeError(error_msg)
        
        audio_file = await asyncio.to_thread(download_sync)
        return audio_file
        
    except Exception as e:
        error_msg = f"Error downloading audio with yt-dlp: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


async def _convert_to_wav(input_file_path: str) -> str:
    """Convert audio to WAV format suitable for transcription."""
    if not isinstance(input_file_path, str):
        error_msg = "input_file_path must be a string."
        log_handler.error(error_msg)
        raise TypeError(error_msg)

    if not os.path.exists(input_file_path):
        error_msg = f"Input file does not exist: {input_file_path}"
        log_handler.error(error_msg)
        raise FileNotFoundError(error_msg)

    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    dir_name = os.path.dirname(input_file_path)
    output_file_path = os.path.join(dir_name, f"{base_name}.wav")

    log_handler.info(f"Converting audio to WAV: {input_file_path} -> {output_file_path}")

    def ffmpeg_convert():
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file_path,
            "-ar", "16000", "-ac", "1", output_file_path
        ], check=True, capture_output=True)
        return output_file_path

    try:
        wav_file = await asyncio.to_thread(ffmpeg_convert)
        log_handler.info(f"Audio conversion completed: {wav_file}")
        return wav_file

    except subprocess.CalledProcessError as e:
        error_msg = f"Error converting to WAV: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)
    except FileNotFoundError:
        error_msg = "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error converting audio to WAV: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


# ================= ImageKit Functions =================
def _upload_wav_to_imagekit(local_wav_path: str) -> Tuple[str, str]:
    """Upload WAV file to ImageKit and return URL and file ID."""
    if not os.path.exists(local_wav_path):
        error_msg = f"File not found: {local_wav_path}"
        log_handler.error(error_msg)
        raise FileNotFoundError(error_msg)

    log_handler.info(f"Uploading WAV file to ImageKit: {local_wav_path}")

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
        error_msg = f"ImageKit upload failed: {response.text}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)

    data = response.json()
    log_handler.info(f"Successfully uploaded to ImageKit: {data['url']}")
    return data["url"], data["fileId"]


def _delete_from_imagekit(file_id: str) -> None:
    """Delete file from ImageKit."""
    log_handler.info(f"Deleting file from ImageKit: {file_id}")
    
    auth = base64.b64encode(f"{IMAGEKIT_PRIVATE_KEY}:".encode()).decode()

    response = requests.delete(
        f"{IMAGEKIT_DELETE_URL}/{file_id}",
        headers={"Authorization": f"Basic {auth}"}
    )

    if response.status_code not in (200, 204):
        error_msg = f"ImageKit delete failed: {response.text}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)
    
    log_handler.info(f"Successfully deleted file from ImageKit: {file_id}")


# ================= RunPod Transcription =================
async def _transcribe_with_runpod(audio_url: str) -> Dict[str, Any]:
    """Send audio file to RunPod Whisper endpoint for transcription."""
    if not isinstance(audio_url, str):
        error_msg = "audio_url must be a string."
        log_handler.error(error_msg)
        raise TypeError(error_msg)

    log_handler.info(f"Starting transcription with RunPod for audio URL: {audio_url}")

    try:
        runpod.api_key = RUNPOD_API_KEY
        
        # Create endpoint object
        endpoint = runpod.Endpoint(RUNPOD_ENDPOINT_ID)
        
        # Health check to warm up serverless endpoint
        try:
            health = endpoint.health()
            log_handler.debug(f"RunPod health check: {health}")
        except Exception as e:
            log_handler.warning(f"Health check failed (this might be normal): {e}")
        
        # Use the correct input format for Faster Whisper endpoint
        runpod_input = {
            "input": {
                "audio": audio_url,     # Required: audio file URL
                "model": "turbo"        # Optional: model selection
            }
        }
        
        log_handler.debug(f"Calling RunPod with input: {runpod_input}")
        
        # Synchronous call with timeout
        result = endpoint.run_sync(runpod_input, timeout=180)
        
        if result is None:
            error_msg = "RunPod returned None"
            log_handler.error(error_msg)
            return {"transcript": "", "status": "failed", "error": error_msg}
        
        log_handler.info("Transcription completed successfully")
        log_handler.debug(f"RunPod result: {result}")
        return result

    except (ConnectionError, Timeout, HTTPError) as e:
        error_msg = f"Network or API error when calling RunPod: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error transcribing with RunPod service: {e}"
        log_handler.error(error_msg)
        raise RuntimeError(error_msg)


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
    log_handler.info(f"Starting transcript fetch for video: {video_url}")
    
    _validate_environment()
    
    video_id = _get_video_id(video_url)
    
    # Try YouTube transcript first
    try:
        log_handler.info("Attempting to fetch transcript from YouTube captions")
        transcript = _extract_youtube_transcript(video_id)
        if transcript:
            log_handler.info("Successfully obtained transcript from YouTube captions")
            return {
                "transcript": transcript,
                "source": "youtube_captions",
                "video_id": video_id,
                "status": "completed"
            }
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, RuntimeError):
        # Continue to audio transcription if captions not available
        log_handler.info("YouTube captions not available, proceeding with audio transcription")

    # Fallback to audio transcription
    log_handler.info("Starting audio transcription workflow")
    temp_dir = tempfile.mkdtemp(prefix=f"yt_etl_{video_id}_")
    log_handler.debug(f"Created temporary directory: {temp_dir}")
    
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
            
            log_handler.info("Successfully completed audio transcription workflow")
            return result
            
        finally:
            # Clean up ImageKit file
            _delete_from_imagekit(file_id)
            
    finally:
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            log_handler.debug(f"Cleaned up temporary directory: {temp_dir}")
