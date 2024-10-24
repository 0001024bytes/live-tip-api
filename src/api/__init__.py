from fastapi.middleware.cors import CORSMiddleware
from src.services.bitfinex import bitfinex
from src.services.coinos import coinos
from src.services.redis import redis
from src.api.schemas import CoinosWebhookSchema
from src.configs import (
    API_ALLOW_ORIGINS,
    API_HOST,
    API_PORT,
    PRODUCTION,
    COINOS_WEBHOOK_KEY,
    COINOS_WEBHOOK_URL,
)
from src.lib.lnurl import LightningAddress
from fastapi import FastAPI, HTTPException, Query
from uuid import uuid4

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
    lightning_address: str = Query(""),
    payment_type: str = Query("lightning", description="Payment type. E.g., lightning or liquid."),
    message: str = Query("", description="Optional message.")
):
    valid_payment_types = ["lightning", "liquid"]
    if payment_type not in valid_payment_types:
        raise HTTPException(status_code=400, detail="Payment type is invalid.")

    price_data = bitfinex.get_price(ticket="btcusd")
    price = float(price_data["SELL"])
    amount_btc = amount / price
    amount_sat = round(amount_btc * pow(10, 8))

    lnurlp_info = LightningAddress.get_lnurlp_info(address)
    if len(message) > lnurlp_info.get("commentAllowed", 0):
        raise ValueError("The comment size is larger than allowed.")
    
    if lnurlp_info.get("minSendable", 0) > amount_sat * 1000:
        raise ValueError("Minimum value is greater than amount.")

    if amount_sat * 1000 > lnurlp_info.get("maxSendable", 0):
        raise ValueError("The amount value is greater than the maximum value.")

    txid = uuid4()
    url = f"{COINOS_WEBHOOK_URL}/{txid}/{id}/{payment_type}?message={message}&lightning_address={lightning_address}"
    invoice = coinos.create_invoice(
        amount_sat,
        payment_type.lower(),
        url,
        COINOS_WEBHOOK_KEY
    )
    if payment_type == "liquid":
        match = re.search(r'liquidnetwork:([^?]+)', invoice["text"])
        if match:
            address = match.group(1)
            invoice["text"] = f"liquidnetwork:{address}?amount={amount_btc:.8f}&assetid=6f0279e9ed041c3d710a9f57d0c02928416460c4b722ae3457a11eec381c526d"

    return {"txid": txid, "address": invoice["text"]}

@api.get("/api/v1/payment/{txid}/paid")
def get_payment_paid(txid: str):
    tx = redis.redis_get(f"tx.{txid}")
    return {"paid": tx.get("paid", False)}

@api.post("/api/v1/coinos/webhook/{txid}/{id}/{payment_type}")
def coinos_webhook_payment(
        txid: str, 
        id: str, 
        payment_type: str, 
        data: CoinosWebhookSchema,
        lightning_address: str = Query("", description="Optional lightning address."),
        message: str = Query("", description="Optional message.")
    ):
    data = dict(data.dict())
    if data["secret"] != COINOS_WEBHOOK_KEY:
        raise HTTPException(400)

    data["id"] = id
    data["txid"] = txid
    data["payment_type"] = payment_type
    data["message"] = message
    data["paid"] = data.get("confirmed", False)
    data["lightning_address"] = lightning_address
    redis.redis_set(f"tx.{txid}", data)

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
