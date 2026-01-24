from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    meta: dict[str, Any] | None = None
