import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "telemetry")

GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50052"))
GRPC_REFLECTION = os.getenv("GRPC_REFLECTION", "false").lower() == "true"

MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "500"))
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "200"))
FUTURE_SKEW_SECONDS = int(os.getenv("FUTURE_SKEW_SECONDS", "300"))
SEED_DEFAULT_SENSORS = os.getenv("SEED_DEFAULT_SENSORS", "true").lower() == "true"
