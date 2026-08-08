import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production Rate Limiting Middleware.
    Restricts IP addresses to a maximum number of requests per minute.
    """
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.ip_requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean timestamps older than 60 seconds
        window_start = now - 60
        self.ip_requests[client_ip] = [t for t in self.ip_requests[client_ip] if t > window_start]
        
        if len(self.ip_requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Maximum 120 requests per minute allowed."}
            )

        self.ip_requests[client_ip].append(now)

        start_time = time.time()
        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Process-Time-MS"] = str(process_time_ms)
        
        return response
