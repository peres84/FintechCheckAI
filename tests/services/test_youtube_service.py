from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
from requests.exceptions import ConnectionError, Timeout, HTTPError
from pytube import YouTube, exceptions
import subprocess
import os
import sys
import runpod
from datetime import datetime
import asyncio
import json
import tempfile
import shutil
import base64
import requests
from dotenv import load_dotenv

# Load environment variables from root .env file
# Get the root directory (2 levels up from tests/services/)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

# ================= Configuration =================
IMAGEKIT_UPLOAD_URL = "https://upload.imagekit.io/api/v1/files/upload"
IMAGEKIT_DELETE_URL = "https://api.imagekit.io/v1/files"

# Environment variables
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")

# Validate required environment variables
required_vars = {
    "RUNPOD_API_KEY": RUNPOD_API_KEY,
    "RUNPOD_ENDPOINT_ID": RUNPOD_ENDPOINT_ID,
    "IMAGEKIT_PRIVATE_KEY": IMAGEKIT_PRIVATE_KEY,
    "IMAGEKIT_URL_ENDPOINT": IMAGEKIT_URL_ENDPOINT
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"Missing required environment variables: {', '.join(missing_vars)}")
    print(f"Looking for .env file at: {env_path}")
    sys.exit(1)

# ================= Helper Function for image kit =================
def upload_wav_to_imagekit(local_wav_path: str) -> tuple[str, str]:
    if not os.path.exists(local_wav_path):
        raise FileNotFoundError(local_wav_path)

    auth = base64.b64encode(
        f"{IMAGEKIT_PRIVATE_KEY}:".encode()
    ).decode()

    with open(local_wav_path, "rb") as f:
        response = requests.post(
            IMAGEKIT_UPLOAD_URL,
            headers={
                "Authorization": f"Basic {auth}"
            },
            files={
                "file": f
            },
            data={
                "fileName": os.path.basename(local_wav_path),
                "useUniqueFileName": "true"
            }
        )

    if response.status_code != 200:
        raise RuntimeError(f"ImageKit upload failed: {response.text}")

    data = response.json()
    return data["url"], data["fileId"]

def delete_from_imagekit(file_id: str):
    auth = base64.b64encode(
        f"{IMAGEKIT_PRIVATE_KEY}:".encode()
    ).decode()

    response = requests.delete(
        f"{IMAGEKIT_DELETE_URL}/{file_id}",
        headers={
            "Authorization": f"Basic {auth}"
        }
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(f"ImageKit delete failed: {response.text}")

# ================= Helper Functions =================
def get_y_video_id(vid_url: str) -> str:
    """
    Extract the video ID from a YouTube URL.
    
    Raises:
        TypeError: If the input is not a string.
        ValueError: If the URL is not a valid YouTube link.
    """
    #Check input type of given parameter
    if not isinstance(vid_url, str):
        raise TypeError(f"Expected a string for URL, got {type(vid_url).__name__} instead.")

    #Extract video ID
    try:
        if "v=" in vid_url:
            return vid_url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in vid_url:
            return vid_url.split("/")[-1]
        else:
            raise ValueError("URL does not appear to be a valid YouTube link.")
    except ValueError as e:
        raise ValueError(f"ERROR, invalid YouTube URL: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error getting youtube video ID: {e}")

def extract_full_transcript(video_id: str) -> str:
    """
    Retrieve the full transcript from YouTube captions, if available.

    Raises:
        TypeError: If the input is not a string.
        TranscriptsDisabled: If captions are disabled.
        NoTranscriptFound: If no transcript is available.
        VideoUnavailable: If the video ID is invalid, removed, or private.
    """
    #Check input type of given parameter
    if not isinstance(video_id, str):
        raise TypeError(f"Expected a string for video id, got {type(video_id).__name__} instead.")

    #Try extracting the transcript
    try:
        #Create an API instance
        ytt_api = YouTubeTranscriptApi()

        #Fetch transcript for English
        fetched = ytt_api.fetch(video_id)

        #Convert to plain text
        full_text = " ".join([segment["text"] for segment in fetched.to_raw_data()])
        return full_text

    except VideoUnavailable as e:
        raise VideoUnavailable(f"Video {video_id} is unavailable: {e}")
    except TranscriptsDisabled as e:
        raise TranscriptsDisabled(f"The provided video {video_id} has its transcript disabled: {e}")
    except NoTranscriptFound as e:
        raise NoTranscriptFound(f"No transcript found for the provided video ID {video_id}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error getting youtube transcript {video_id}: {e}")

async def download_full_audio(vid_url: str) -> str:
    """
    Download the full audio track from a YouTube video that must be processed
    to extract the data subsequently.

    Raises:
        TypeError: If vid_url is not a string.
        ValueError: If the URL is invalid or video ID extraction fails.
        pytube.exceptions.VideoUnavailable: If the video is private, removed, or blocked.
        pytube.exceptions.AgeRestrictedError: If the video is age restricted.
        RuntimeError: For any other unexpected error during download.
    """
    #Check input type of given parameter
    if not isinstance(vid_url, str):
        raise TypeError(f"Expected a string for video URL, got {type(vid_url).__name__} instead.")

    #Extract id for naming the file
    filename = get_y_video_id(vid_url)
    #Get current date and time in YYYYMMDD_HHMMSS format
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    #Download the audio
    try:
        youtube_vid = YouTube(vid_url)
        stream = youtube_vid.streams.filter(only_audio=True).first()

        full_audio_name = f"video_{filename}_{current_time}.mp4"
        audio_file = await asyncio.to_thread(stream.download, filename=full_audio_name)
        return audio_file
    
    except exceptions.VideoUnavailable as e:
        raise exceptions.VideoUnavailable(f"Video unavailable: {vid_url}: {e}")
    except exceptions.AgeRestrictedError as e:
        raise exceptions.AgeRestrictedError(f"Video is age restricted: {vid_url}: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error downloading audio from YouTube: {e}")

async def convert_to_wav(input_file_path: str) -> str:
    """
    Convert audio to WAV format suitable for transcription.

    Raises:
        TypeError: If input_file_path are not strings.
        FileNotFoundError: If input_file_path does not exist.
        RuntimeError: If FFmpeg fails or is not installed.
    """
    #Type checks
    if not isinstance(input_file_path, str):
        raise TypeError("input_file_path must be strings.")

    #File existence check
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file does not exist: {input_file_path}")

    #Determine output path with same base name but .wav extension
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    dir_name = os.path.dirname(input_file_path)
    output_file_path = os.path.join(dir_name, f"{base_name}.wav")

    #intra_Function to run FFmpeg synchronously
    def ffmpeg_convert():
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file_path,
            "-ar", "16000", "-ac", "1", output_file_path
        ], check=True)
        return output_file_path

    #Convert wav using FFmpeg
    try:
        wav_file = await asyncio.to_thread(ffmpeg_convert)
        return wav_file

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error converting to WAV: {e}")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
    except Exception as e:
        raise RuntimeError(f"Unexpected error converting audio to wav format: {e}")

async def transcribe_with_runpod(audio_url: str) -> dict:
    """
    Send audio file to RunPod Whisper endpoint for transcription.

    Raises:
        TypeError: If audio_url is not a string.
        RuntimeError: If transcription fails.
    """
    if not isinstance(audio_url, str):
        raise TypeError("audio_url must be a string.")

    try:
        job = runpod.run_sync(
            RUNPOD_ENDPOINT_ID,
            input={"audio_file": audio_url},
            api_key=RUNPOD_API_KEY
        )
        return job

    except (ConnectionError, Timeout, HTTPError) as e:
        raise RuntimeError(f"Network or API error when calling RunPod: {e}")
    except Exception as e:
        raise RuntimeError(f"Error transcribing with RunPod service: {e}")

# ================= Main Function =================
async def main_async(youtube_url: str):
    """
    Main function to orchestrate the YouTube ETL process.

    TODO: REMEMBER change all prints with proper logging
    """

    video_id = get_y_video_id(youtube_url)

    temp_dir = tempfile.mkdtemp(prefix=f"yt_etl_{video_id}_")
    try:
        print(f"Temporary working directory created at {temp_dir}")
        print("Skipping transcript check - testing audio transcription flow...")
        
        # DISABLED FOR TESTING: Skip transcript check to test full audio flow
        # try:
        #     transcript = extract_full_transcript(video_id)
        #     if transcript:
        #         print("Transcript successfully extracted from YouTube captions!")
        #         with open(f"{video_id}_transcript.txt", "w", encoding="utf-8") as f:
        #             f.write(transcript)
        #         print(f"Full transcript saved as '{video_id}_transcript.txt'.")
        #         return transcript
        # except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, RuntimeError) as e:
        #     print(f"No transcript available via YouTube captions: {e}")
        #     transcript = None

        # ========== Download audio ==========
        print("Downloading full audio for transcription...")
        filename = get_y_video_id(youtube_url)
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"video_{filename}_{current_time}.mp4"
        audio_mp4 = await asyncio.to_thread(
            lambda: YouTube(youtube_url)
                .streams.filter(only_audio=True)
                .first()
                .download(output_path=temp_dir, filename=audio_filename)
        )
        print(f"Audio downloaded: {audio_mp4}")

        # ========== Convert to WAV & upload ==========
        print("Converting audio to WAV...")
        audio_wav = await convert_to_wav(audio_mp4)
        print(f"Audio converted to WAV: {audio_wav}")

        # ========== Upload WAV to ImageKit ==========
        print("Uploading WAV to ImageKit...")
        audio_url, imagekit_file_id = upload_wav_to_imagekit(audio_wav)
        print(f"Uploaded to ImageKit: {audio_url}")

        # ========== RunPod transcription ==========
        try:
            print("Sending audio URL to RunPod...")
            runpod_result = await transcribe_with_runpod(audio_url)
            print("Transcription complete!")
        finally:
            print("Deleting audio from ImageKit...")
            delete_from_imagekit(imagekit_file_id)

        # ========== Save results ==========
        with open(f"{video_id}_transcript.json", "w", encoding="utf-8") as f:
            json.dump(runpod_result, f, indent=2)
        with open(f"{video_id}_transcript.txt", "w", encoding="utf-8") as f:
            f.write(runpod_result.get("transcript", ""))

        print(f"Full transcript saved as '{video_id}_transcript.txt' and JSON as '{video_id}_transcript.json'.")
        return runpod_result

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Temporary files in {temp_dir} deleted")

# ================= Entry Point =================
# if __name__ == "__main__":
#     youtube_url = input("Enter YouTube URL: ").strip()
#     asyncio.run(main_async(youtube_url))

# ================= Test / Entry Point =================
if __name__ == "__main__":
    # Print environment info for debugging
    print("=== Environment Check ===")
    print(f"Root directory: {root_dir}")
    print(f".env file path: {env_path}")
    print(f".env file exists: {os.path.exists(env_path)}")
    print(f"RUNPOD_API_KEY loaded: {'Yes' if RUNPOD_API_KEY else 'No'}")
    print(f"RUNPOD_ENDPOINT_ID loaded: {'Yes' if RUNPOD_ENDPOINT_ID else 'No'}")
    print(f"IMAGEKIT_PRIVATE_KEY loaded: {'Yes' if IMAGEKIT_PRIVATE_KEY else 'No'}")
    print("========================\n")
    
    # Test with any video since we're skipping transcript check
    TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video

    print("Starting YouTube ETL test...")
    print(f"Testing URL: {TEST_YOUTUBE_URL}")
    print(f"Video ID: {get_y_video_id(TEST_YOUTUBE_URL)}")
    try:
        result = asyncio.run(main_async(TEST_YOUTUBE_URL))
        print("\nTest finished successfully!")
        if isinstance(result, dict):
            print("RunPod transcription keys:", list(result.keys()))
        else:
            print("Transcript (YouTube captions):")
            print(result[:300], "...")  # print first 300 chars
    except Exception as e:
        print("Test failed with exception:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        import traceback
        traceback.print_exc()