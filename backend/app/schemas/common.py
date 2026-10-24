"""
GlycoTwin Common API Schemas.
"""
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=1000, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total matching items count")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error description")
    error_type: str = Field("api_error", description="Machine-readable error category")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC error timestamp")
