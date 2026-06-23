'''backend/middleware.py'''
"""Centralized error handling and request logging middleware for FastAPI.
Provides a uniform JSON error format and logs each request with a unique ID.
"""
import uuid
import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("codesense")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as he:
            logger.error(f"[{request.state.request_id}] HTTPException: {he.detail}")
            return JSONResponse(
                status_code=he.status_code,
                content={"success": False, "error": {"code": "HTTP_ERROR", "message": he.detail}},
            )
        except Exception as exc:
            logger.exception(f"[{request.state.request_id}] Unexpected error")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": {"code": "SERVER_ERROR", "message": "Internal server error"}},
            )
