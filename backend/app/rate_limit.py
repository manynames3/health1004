import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, requests_per_minute: int):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in {"/health"}:
            return await call_next(request)
        client_id = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = self.clients[client_id]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.requests_per_minute:
            return Response("Rate limit exceeded", status_code=429)
        window.append(now)
        return await call_next(request)
