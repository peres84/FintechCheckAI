from fastapi import APIRouter

from ...models.schemas import VerificationRequest, VerificationResponse

router = APIRouter()


@router.post("/verify", response_model=VerificationResponse)
def verify_claims(payload: VerificationRequest) -> VerificationResponse:
    return VerificationResponse(results=[])
