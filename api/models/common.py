"""Common Pydantic models shared across the API."""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=500, description="Items per page")
