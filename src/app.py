# pylint: disable=all
from dotenv import load_dotenv
from os import environ

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv(environ.get("ENV_PATH", ".env"))

import logging

# Configure logging level based on the environment variable LOG_LEVEL.
# Defaults to INFO if not specified.
logging.basicConfig(
    level={
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from src import api

def start():
    api.start()
