import grpc
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from utils.rate_limiter import RateLimitExceeded

GRPC_TO_HTTP = {
    grpc.StatusCode.UNAUTHENTICATED: 401,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.INVALID_ARGUMENT: 422,
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.RESOURCE_EXHAUSTED: 429,
    grpc.StatusCode.FAILED_PRECONDITION: 400,
    grpc.StatusCode.UNAVAILABLE: 503,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.INTERNAL: 500,
}


def grpc_http_error(exc: grpc.aio.AioRpcError) -> HTTPException:
    status = GRPC_TO_HTTP.get(exc.code(), 502)
    message = exc.details() or "Upstream service error"
    return HTTPException(status_code=status, detail=message)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": str(exc)})
