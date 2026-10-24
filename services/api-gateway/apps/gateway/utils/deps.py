from fastapi import Depends, Header, HTTPException, Request

from auth.v1 import auth_pb2
from grpc_clients import clients
from settings import (
    AI_CHAT_RATE_LIMIT,
    AUTH_RATE_LIMIT,
    DEVICE_INGEST_TOKEN,
    INGEST_RATE_LIMIT,
    READ_RATE_LIMIT,
)
from utils.errors import client_ip, grpc_http_error
from utils.rate_limiter import limiter, parse_limits
import grpc

READ_LIMITS = parse_limits(READ_RATE_LIMIT)
AI_CHAT_LIMITS = parse_limits(AI_CHAT_RATE_LIMIT)
INGEST_LIMITS = parse_limits(INGEST_RATE_LIMIT)
AUTH_LIMITS = parse_limits(AUTH_RATE_LIMIT)


async def limit_auth(request: Request) -> None:
    await limiter.check("auth", client_ip(request), AUTH_LIMITS)


async def limit_read(request: Request) -> None:
    await limiter.check("read", client_ip(request), READ_LIMITS)


async def limit_ai_chat(request: Request) -> None:
    await limiter.check("ai_chat", client_ip(request), AI_CHAT_LIMITS)


async def limit_ingest(request: Request) -> None:
    await limiter.check("ingest", client_ip(request), INGEST_LIMITS)


def _bearer(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


async def current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> auth_pb2.VerifyTokenResponse:
    token = _bearer(authorization)
    try:
        result = await clients.auth_stub.VerifyToken(
            auth_pb2.VerifyTokenRequest(access_token=token),
            metadata=clients.metadata(ip=client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    if not result.valid:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    request.state.access_token = token
    request.state.user = result
    return result


async def ingest_principal(
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict:
    if DEVICE_INGEST_TOKEN and authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "device" and token == DEVICE_INGEST_TOKEN:
            return {"type": "device", "username": "device"}
    user = await current_user(request, authorization)
    return {"type": "user", "username": user.username, "role": user.role}


UserDep = Depends(current_user)
IngestDep = Depends(ingest_principal)
AuthLimit = Depends(limit_auth)
ReadLimit = Depends(limit_read)
AiChatLimit = Depends(limit_ai_chat)
IngestLimit = Depends(limit_ingest)
