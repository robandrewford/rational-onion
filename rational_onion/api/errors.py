from enum import Enum
from typing import Dict, Any, Optional
from fastapi import HTTPException

class ErrorType(Enum):
    """Enumeration of possible error types"""
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    ARGUMENT_ERROR = "argument_error"
    GRAPH_ERROR = "graph_error"
    CITATION_ERROR = "citation_error"

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

class ArgumentError(BaseAPIError):
    """Error for argument-related issues"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type=ErrorType.ARGUMENT_ERROR,
            message=message,
            status_code=400,
            details=details
        )

class DatabaseError(BaseAPIError):
    """Error for database operations"""
    def __init__(self, operation: str, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["operation"] = operation
        super().__init__(
            error_type=ErrorType.DATABASE_ERROR,
            message=message,
            status_code=500,
            details=details
        )

class ValidationError(BaseAPIError):
    """Error for validation failures"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type=ErrorType.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details
        )

class GraphError(BaseAPIError):
    """Error for graph structure issues"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type=ErrorType.GRAPH_ERROR,
            message=message,
            status_code=400,
            details=details
        )

class CitationError(BaseAPIError):
    """Error for citation verification issues"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_type=ErrorType.CITATION_ERROR,
            message=message,
            status_code=400,
            details=details
        ) 