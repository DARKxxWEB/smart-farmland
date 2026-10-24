import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "bi")

GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50053"))
GRPC_REFLECTION = os.getenv("GRPC_REFLECTION", "false").lower() == "true"

TELEMETRY_GRPC_TARGET = os.getenv("TELEMETRY_GRPC_TARGET", "localhost:50052")

DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "50"))
MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
SILENCE_MINUTES = int(os.getenv("SILENCE_MINUTES", "30"))
DEFAULT_INTERVAL = os.getenv("DEFAULT_INTERVAL", "hour")

AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
AVALAI_MODEL = os.getenv("AVALAI_MODEL", "gpt-4o-mini")
AI_ASSISTANT_ENABLED = os.getenv("AI_ASSISTANT_ENABLED", "true").lower() == "true"

MOISTURE_LOW = float(os.getenv("MOISTURE_LOW", "20"))
MOISTURE_HIGH = float(os.getenv("MOISTURE_HIGH", "80"))
NITROGEN_LOW = float(os.getenv("NITROGEN_LOW", "20"))
NITROGEN_HIGH = float(os.getenv("NITROGEN_HIGH", "80"))
PHOSPHORUS_LOW = float(os.getenv("PHOSPHORUS_LOW", "10"))
PHOSPHORUS_HIGH = float(os.getenv("PHOSPHORUS_HIGH", "50"))
POTASSIUM_LOW = float(os.getenv("POTASSIUM_LOW", "80"))
POTASSIUM_HIGH = float(os.getenv("POTASSIUM_HIGH", "300"))
TEMPERATURE_LOW = float(os.getenv("TEMPERATURE_LOW", "5"))
TEMPERATURE_HIGH = float(os.getenv("TEMPERATURE_HIGH", "40"))
