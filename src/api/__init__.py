from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query
from src.services.bitfinex import bitfinex
from src.services.coinos import coinos
from src.configs import (
    API_ALLOW_ORIGINS,
    API_HOST,
    API_PORT,
    PRODUCTION,
    COINOS_WEBHOOK_KEY,
    COINOS_WEBHOOK_URL,
)
import uvicorn
import re

api = FastAPI(
    title="API",
    docs_url=("/docs" if not PRODUCTION else None),
    redoc_url=("/redocs" if not PRODUCTION else None),
    swagger_ui_oauth2_redirect_url=None,
    openapi_url=("/openapi.json" if not PRODUCTION else None),
)

# CORS configuration
api.add_middleware(
    CORSMiddleware,
    allow_origins=API_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.post("/api/v1/address/{id}")
async def create_address(
    id: str,
    amount: int = Query(0, ge=0, description="Amount to be donated in fiat."),
    payment_type: str = Query("lightning", description="Payment type. E.g., lightning or liquid."),
    message: str = Query("", description="Optional message.")
):
    # Validate payment type
    valid_payment_types = ["lightning", "liquid"]
    if payment_type not in valid_payment_types:
        raise HTTPException(status_code=400, detail="Payment type is invalid.")

    # Get price and calculate the amount in satoshis
    price_data = bitfinex.get_price(ticket="btcusd")
    price = float(price_data["SELL"])
    amount_btc = amount / price
    amount_sat = round(amount_btc * 1e8)

    # Create the invoice in Coinos
    invoice = coinos.create_invoice(
        amount_sat,
        payment_type.lower(),
        f"{COINOS_WEBHOOK_URL}?id={id}&message={message}",
        COINOS_WEBHOOK_KEY
    )

    # Modify the invoice if the payment type is liquid
    if payment_type == "liquid":
        match = re.search(r'liquidnetwork:([^?]+)', invoice["text"])
        if match:
            address = match.group(1)
            invoice["text"] = f"liquidnetwork:{address}?amount={amount_btc:.8f}&assetid=6f0279e9ed041c3d710a9f57d0c02928416460c4b722ae3457a11eec381c526d"

    return {"address": invoice["text"]}

def start():
    """
    Starts the FastAPI application using Uvicorn.
    This function launches the application with the specified host, port, loop
    and logging configuration.
    """
    uvicorn.run(
        api,
        host=API_HOST,
        port=API_PORT,
        loop="asyncio",
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(asctime)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                },
            },
            "loggers": {
                "foo-logger": {"handlers": ["default"], "level": "DEBUG"},
            },
        },
    )
