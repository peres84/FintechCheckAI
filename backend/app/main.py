from fastapi import FastAPI

from .api import documents, verification, youtube

app = FastAPI(title="Fintech Check AI", version="0.1.0")

app.include_router(youtube.router, prefix="/api/youtube", tags=["youtube"])
app.include_router(verification.router, prefix="/api", tags=["verification"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
