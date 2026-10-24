import os

from dotenv import load_dotenv

load_dotenv()

HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("HTTP_PORT", "8000"))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

AUTH_GRPC_TARGET = os.getenv("AUTH_GRPC_TARGET", "localhost:50051")
TELEMETRY_GRPC_TARGET = os.getenv("TELEMETRY_GRPC_TARGET", "localhost:50052")
BI_GRPC_TARGET = os.getenv("BI_GRPC_TARGET", "localhost:50053")
NOTIFICATION_GRPC_TARGET = os.getenv("NOTIFICATION_GRPC_TARGET", "localhost:50054")

REDIS_URL = os.getenv("REDIS_URL") or None
INGEST_RATE_LIMIT = os.getenv("INGEST_RATE_LIMIT", "60/minute;1000/hour")
AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "10/minute;100/hour")
READ_RATE_LIMIT = os.getenv("READ_RATE_LIMIT", "120/minute")
AI_CHAT_RATE_LIMIT = os.getenv("AI_CHAT_RATE_LIMIT", "10/hour")

DEVICE_INGEST_TOKEN = os.getenv("DEVICE_INGEST_TOKEN", "")
WS_QUEUE_SIZE = int(os.getenv("WS_QUEUE_SIZE", "100"))
