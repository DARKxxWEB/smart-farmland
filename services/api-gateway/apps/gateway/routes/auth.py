import grpc
from fastapi import APIRouter, Request

from auth.v1 import auth_pb2
from grpc_clients import clients
from schema._input import ChangePasswordBody, LoginBody, LogoutBody, RefreshBody
from utils.deps import AuthLimit, UserDep
from utils.errors import client_ip, grpc_http_error
from utils import proto_json

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginBody, request: Request, _: None = AuthLimit):
    try:
        response = await clients.auth_stub.Login(
            auth_pb2.LoginRequest(username=body.username, password=body.password),
            metadata=clients.metadata(ip=client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.tokens(response)


@router.post("/refresh")
async def refresh(body: RefreshBody, request: Request, _: None = AuthLimit):
    try:
        response = await clients.auth_stub.RefreshToken(
            auth_pb2.RefreshTokenRequest(refresh_token=body.refresh_token),
            metadata=clients.metadata(ip=client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.tokens(response)


@router.post("/logout")
async def logout(body: LogoutBody, request: Request):
    try:
        await clients.auth_stub.Logout(
            auth_pb2.LogoutRequest(refresh_token=body.refresh_token),
            metadata=clients.metadata(ip=client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {"ok": True}


@router.get("/me")
async def me(request: Request, user=UserDep):
    try:
        response = await clients.auth_stub.GetMe(
            auth_pb2.GetMeRequest(),
            metadata=clients.metadata(request.state.access_token, client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return proto_json.user(response)


@router.post("/change-password")
async def change_password(body: ChangePasswordBody, request: Request, user=UserDep):
    try:
        response = await clients.auth_stub.ChangePassword(
            auth_pb2.ChangePasswordRequest(
                old_password=body.old_password,
                new_password=body.new_password,
            ),
            metadata=clients.metadata(request.state.access_token, client_ip(request)),
        )
    except grpc.aio.AioRpcError as e:
        raise grpc_http_error(e) from e
    return {"message": response.message}
