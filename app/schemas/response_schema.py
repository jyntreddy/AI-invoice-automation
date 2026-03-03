from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar, List

T = TypeVar("T")


class Response(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error: str
    status_code: int
