from enum import Enum
from typing import Dict, Any, Optional
from fastapi import HTTPException

class ErrorType(str, Enum):
    """Enumeration of error types"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    GRAPH_ERROR = "GRAPH_ERROR"
    ARGUMENT_ERROR = "ARGUMENT_ERROR"
    CITATION_ERROR = "CITATION_ERROR"

class BaseError(Exception):
    """Base error class for custom exceptions"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(BaseError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str):
        super().__init__(message, {"field": field})
        self.field = field

class ArgumentError(BaseError):
    """Raised when argument structure is invalid"""
    pass

class DatabaseError(BaseError):
    """Raised when database operations fail"""
    pass

class GraphError(BaseError):
    """Raised when graph operations or validations fail"""
    pass

class CitationError(BaseError):
    """Raised when citation verification fails"""
    pass

class BaseAPIError(HTTPException):
    """Base class for API errors"""
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_type = error_type
        detail = {
            "error_type": error_type.value,
            "message": message,
            "details": details or {}
        }
        super().__init__(status_code=status_code, detail=detail) 