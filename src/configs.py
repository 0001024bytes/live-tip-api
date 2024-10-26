from secrets import token_hex
from os import getenv

# API configuration.
API_HOST = getenv("API_HOST", "0.0.0.0")
API_PORT = int(getenv("API_PORT", 3214))
API_ALLOW_ORIGINS = getenv("API_ALLOW_ORIGINS", "*").split(",")

# Production configuration
PRODUCTION = getenv("PRODUCTION", "false") == "true"

class RedisConfig:

    def __getattr__(self, name: str):
        value = getenv(name)
        if value:
            if name == "REDIS_PREFIX":
                value = f"L#{value}"
            if name == "REDIS_PORT":
                value = int(value)
            return value
        elif name == "REDIS_PREFIX":
            return "T#"
        elif name == "REDIS_HOST":
            return "127.0.0.1"
        elif name == "REDIS_PORT":
            return 6379

# Coinos configuration
COINOS_USERNAME = getenv("COINOS_USERNAME")
COINOS_PASSWORD = getenv("COINOS_PASSWORD")
COINOS_WEBHOOK_URL = getenv("COINOS_WEBHOOK_URL", f"http://localhost:{API_PORT}/api/v1/coinos/webhook")
COINOS_WEBHOOK_KEY = getenv("COINOS_WEBHOOK_KEY", token_hex(32))

# Donation configuration
MIN_VALUE = float(getenv("MIN_VALUE", 15))
MAX_VALUE = float(getenv("MAX_VALUE", 1))

# Liquid configuration
LIQUID_URL = getenv("LIQUID_URL", "http://localhost:4023")
LIQUID_KEY = getenv("LIQUID_KEY", "")
LIQUID_WEBHOOK_URL = getenv("LIQUID_WEBHOOK_URL", f"http://localhost:{API_PORT}/api/v1/liquid/webhook")
LIQUID_WEBHOOK_KEY = getenv("LIQUID_WEBHOOK_KEY", token_hex(32))