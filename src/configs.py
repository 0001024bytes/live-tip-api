from secrets import token_hex
from os import getenv

# API configuration.
API_HOST = getenv("API_HOST", "0.0.0.0")
API_PORT = int(getenv("API_PORT", 3214))
API_ALLOW_ORIGINS = getenv("API_ALLOW_ORIGINS", "*").split(",")

# Production configuration
PRODUCTION = getenv("PRODUCTION", "false") == "true"

# Coinos configuration
COINOS_USERNAME = getenv("COINOS_USERNAME")
COINOS_PASSWORD = getenv("COINOS_PASSWORD")
COINOS_WEBHOOK_URL = getenv("WEBHOOK_URL")
COINOS_WEBHOOK_KEY = getenv("WEBHOOK_KEY", token_hex(32))