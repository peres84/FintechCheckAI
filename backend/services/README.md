# Backend Services

This directory contains service modules that handle external integrations and core business logic for the application.

## Services Overview

### `youtube_service.py`

**Purpose**: Extracts transcripts from YouTube videos using multiple fallback methods.

**Main Function**: `fetch_transcript(video_url: str) -> Dict[str, Any]`

**Workflow**:
1. **YouTube Captions First**: Attempts to extract transcript directly from YouTube's built-in captions/subtitles
2. **Audio Transcription Fallback**: If captions aren't available, downloads the audio and transcribes it using AI

**Detailed Process**:

#### Method 1: YouTube Captions
- Uses `youtube-transcript-api` to fetch existing captions
- Fast and accurate when available
- Returns immediately if successful

#### Method 2: Audio Transcription Pipeline
When captions aren't available, the service:

1. **Download Audio**: Uses `yt-dlp` (more reliable than pytube) to download audio-only stream
2. **Convert Format**: Uses FFmpeg to convert to 16kHz mono WAV format optimized for speech recognition
3. **Upload to ImageKit**: Temporarily uploads WAV file to get a public URL
4. **Transcribe with RunPod**: Sends audio URL to RunPod Whisper endpoint for AI transcription
5. **Cleanup**: Deletes the temporary WAV file from ImageKit
6. **Return Results**: Returns transcript with metadata

**Dependencies**:
- `yt-dlp`: YouTube audio downloading
- `youtube-transcript-api`: Caption extraction
- `runpod`: AI transcription service
- `requests`: HTTP requests for ImageKit
- `ffmpeg`: Audio format conversion (system dependency)

**Environment Variables Required**:
- `RUNPOD_API_KEY`: API key for RunPod service
- `RUNPOD_ENDPOINT_ID`: Specific endpoint ID for Whisper transcription
- `IMAGEKIT_PRIVATE_KEY`: Private key for ImageKit file storage
- `IMAGEKIT_URL_ENDPOINT`: ImageKit URL endpoint

**Return Format**:
```python
{
    "transcript": "Full transcript text...",
    "source": "youtube_captions" | "audio_transcription",
    "video_id": "YouTube video ID",
    "status": "completed" | "failed",
    "duration": 123.45,  # Only for audio transcription
    "language": "en"     # Only for audio transcription
}
```

**Error Handling**:
- Validates environment variables on startup
- Handles YouTube API errors gracefully
- Provides detailed error messages for debugging
- Automatically cleans up temporary files even on failure

**Usage Example**:
```python
from backend.services.youtube_service import fetch_transcript

# Get transcript from any YouTube video
result = await fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(result["transcript"])
```

**Performance Notes**:
- YouTube captions: ~1-2 seconds
- Audio transcription: ~30-60 seconds depending on video length
- Temporary files are automatically cleaned up
- Uses async/await for non-blocking operations

---

## Adding New Services

When adding new service modules to this directory:

1. Follow the same pattern of having a main public function
2. Use private helper functions (prefixed with `_`) for internal logic
3. Include comprehensive error handling
4. Add environment variable validation
5. Update this README with documentation
6. Create corresponding test files in `tests/services/`

## Testing

Each service should have a corresponding test file in `tests/services/test_{service_name}.py` that covers:
- Happy path scenarios
- Error conditions
- Environment variable validation
- Integration with external services