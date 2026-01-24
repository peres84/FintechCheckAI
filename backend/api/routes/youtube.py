from fastapi import APIRouter

router = APIRouter()


@router.get("/transcript")
def get_transcript(url: str) -> dict:
    return {"video_url": url, "transcript": [], "status": "not_implemented"}
