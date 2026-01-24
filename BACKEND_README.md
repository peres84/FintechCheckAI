# FinTech Check AI Backend

A FastAPI-based backend service for AI-powered financial document verification and YouTube transcript extraction.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# RunPod Configuration (for audio transcription)
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=your_runpod_endpoint_id

# ImageKit Configuration (for temporary file storage)
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_URL_ENDPOINT=your_imagekit_url_endpoint

# Optional: Server Configuration
PORT=8000
```

### 3. Start the Server

#### Option 1: Using the startup script (Recommended)
```bash
python run_server.py
```

#### Option 2: Using the main module directly
```bash
python -m backend.main
```

#### Option 3: Using uvicorn directly
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access the API

- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **YouTube Health**: http://127.0.0.1:8000/api/youtube/health

## API Endpoints

### Health Check
```
GET /health
```
Returns the overall service health status.

### YouTube Transcript Extraction
```
POST /api/youtube/transcript
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "transcript": "Full transcript text...",
  "source": "youtube_captions",
  "status": "completed",
  "error": null
}
```

**Features:**
- Attempts to extract transcript from YouTube captions first
- Falls back to audio download and AI transcription if captions unavailable
- Supports various YouTube URL formats
- Comprehensive error handling and logging

### YouTube Service Health
```
GET /api/youtube/health
```
Returns the YouTube service health status and available endpoints.

## Testing

Run the endpoint tests to verify everything is working:

```bash
python test_endpoints.py
```

## Configuration

The backend configuration is stored in `backend/core/config.json`:

- **Network settings**: Host, port, reload options
- **Logging configuration**: Log levels, file locations
- **Endpoint settings**: Rate limits, prefixes, routes

## Logging

Logs are written to both console and files in the `logs/` directory:
- **File location**: `logs/fintech_check_ai_YYYY-MM-DDTHH-MM-SS.log`
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Structured logging**: Timestamps, log levels, and detailed messages

## Architecture

```
backend/
├── main.py                 # FastAPI application and startup
├── core/
│   ├── config.py          # Configuration loader
│   ├── config.json        # Configuration settings
│   └── logging.py         # Logging setup
├── api/
│   └── routes/
│       ├── youtube.py     # YouTube transcript endpoints
│       ├── documents.py   # Document processing endpoints
│       └── verification.py # Verification endpoints
├── services/
│   └── youtube_service.py # YouTube transcript service logic
└── models/
    └── schemas.py         # Pydantic models for requests/responses
```

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid YouTube URLs or malformed requests
- **500 Internal Server Error**: Service failures, missing environment variables
- **Detailed error messages**: Logged for debugging and returned to clients

## Development

### Adding New Endpoints

1. Create route file in `backend/api/routes/`
2. Add endpoint configuration to `backend/core/config.json`
3. Import and include router in `backend/main.py`
4. Add request/response models to `backend/models/schemas.py`

### Environment Variables

Required for full functionality:
- `RUNPOD_API_KEY`: For AI audio transcription
- `RUNPOD_ENDPOINT_ID`: RunPod endpoint identifier
- `IMAGEKIT_PRIVATE_KEY`: For temporary file storage
- `IMAGEKIT_URL_ENDPOINT`: ImageKit endpoint URL

Optional:
- `PORT`: Server port (default: 8000)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root directory
2. **Missing Dependencies**: Run `pip install -r backend/requirements.txt`
3. **Environment Variables**: Check `.env` file exists and contains required variables
4. **Port Conflicts**: Change port in config.json or set PORT environment variable

### Logs

Check the logs directory for detailed error information:
```bash
tail -f logs/fintech_check_ai_*.log
```