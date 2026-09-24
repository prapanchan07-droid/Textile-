from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class StandardResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

class HealthResponseData(BaseModel):
    status: str
    project_name: str
    company: str
    version: str
    environment: str
    database: Dict[str, Any]
    active_module: str
