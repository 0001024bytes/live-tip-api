from fastapi.middleware.cors import CORSMiddleware
from src.services.bitpreco import bitpreco
from src.services.bitfinex import bitfinex
from src.services.liquid import liquid
from src.services.coinos import coinos
from src.services.redis import redis
from src.services.depix import depix
from src.utils.helpers import calculate_percentage, sats_to_msats
from src.api.schemas import CoinosWebhookSchema
from src.configs import (
    API_ALLOW_ORIGINS,
    API_HOST,
    API_PORT,
    LIQUID_WEBHOOK_KEY,
    LIQUID_WEBHOOK_URL,
    MAX_VALUE,
    MIN_VALUE,
    PRODUCTION,
    COINOS_WEBHOOK_KEY,
    COINOS_WEBHOOK_URL,
)
from src.lib.lnurl import LightningAddress
from fastapi import FastAPI, HTTPException, Query, Request
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

api.add_middleware(
    CORSMiddleware,
    allow_origins=API_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/api/v1/getinfo")
def get_info(lightning_address: str = Query("")):
    lnurlp_info = LightningAddress.get_lnurlp_info(lightning_address)
    return {
        "comment_allowed": int(lnurlp_info.get("commentAllowed", 0)), 
        "min_value": MIN_VALUE, 
        "max_value": MAX_VALUE
    }

@api.post("/api/v1/address/{id}")
async def create_address(
    id: str,
    amount: float = Query(0, ge=0, description="Amount to be donated in fiat."),
    lightning_address: str = Query(""),
    payment_type: str = Query("lightning", description="Payment type. E.g., lightning or liquid."),
    message: str = Query("", description="Optional message.")
):
    if payment_type not in ["lightning", "liquid", "pix"]:
        raise HTTPException(status_code=400, detail="Payment type is invalid.")

    lnurlp_info = LightningAddress.get_lnurlp_info(lightning_address)
    message = message[:int(lnurlp_info.get("commentAllowed", 0))]
    price_data = bitfinex.get_price(ticket="btcusd")
    price = float(price_data["SELL"])
    amount_btc = amount / price
    amount_sat = round(amount_btc * pow(10, 8))
    if lnurlp_info.get("minSendable", 0) > amount_sat * 1000:
        raise ValueError("Minimum value is greater than amount.")

    if amount_sat * 1000 > lnurlp_info.get("maxSendable", 0):
        raise ValueError("The amount value is greater than the maximum value.")

    txid = uuid4()
    address = None
    if payment_type in ["lightning", "liquid"]:
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
        elif payment_type == "lightning":
            invoice["text"] = f"lightning:{invoice['text']}"
        
        address = invoice["text"]
    elif payment_type == "pix":
        amount_brl = round(amount * bitpreco.get_price("usdt-brl")["BUY"])
        liquid_address_assets = liquid.get_new_address(
            str(txid), 
            label=lightning_address, 
            webhook_url=f"{LIQUID_WEBHOOK_URL}/{txid}/{id}/{payment_type}?message={message}&lightning_address={lightning_address}",
            webhook_key=LIQUID_WEBHOOK_KEY
        )["address"]

        address = depix.create_qrcode(
            amount=amount_brl, 
            address=liquid_address_assets
        ).get("qrcode")
    else:
        raise NotImplemented

    return {"txid": txid, "address": address}

@api.get("/api/v1/payment/{txid}/paid")
def get_payment_paid(txid: str):
    tx = redis.redis_get(f"tx.{txid}")
    return {"paid": tx.get("paid", False)}

@api.post("/api/v1/liquid/webhook/{txid}/{id}/{payment_type}")
def liquid_webhook_payment(
        txid: str, 
        id: str, 
        payment_type: str, 
        data: dict,
        request: Request,
        lightning_address: str = Query("", description="Optional lightning address."),
        message: str = Query("", description="Optional message.")
    ):
    if (LIQUID_WEBHOOK_KEY != \
            request.headers.get("X-WEBHOOK-KEY", "")):
        raise HTTPException(401)

    if data["data"]["asset_id"] != "02f22f8d9c76ab41661a2729e4752e2c5d1a263012141b86ea98af5472df5189":
        raise HTTPException(400)

    tx_status = redis.redis_get(f"tx.{txid}")
    if tx_status and tx_status.get("paid", False):
        raise HTTPException(400)

    data["id"] = id
    data["txid"] = txid
    data["payment_type"] = payment_type
    data["message"] = message
    data["paid"] = data.get("confirmed", False)
    data["lightning_address"] = lightning_address
    redis.redis_set(f"tx.{txid}", data)

    amount_depix = data["data"]["asset_value"] / pow(10, 8)
    amount_btc = amount_depix / bitpreco.get_price("btc-brl")["SELL"]
    amount_sats = round(amount_btc * pow(10, 8))
    amount_sats_discount = amount_sats 
    amount_sats_discount-= round(calculate_percentage(amount_sats_discount, 5))
    amount_sats_discount = abs(amount_sats_discount)
    maxfee = abs(amount_sats - amount_sats_discount)
    if maxfee < 1:
        maxfee = 1

    payreq = LightningAddress.fetch_invoice(
        lightning_address, 
        amount=sats_to_msats(amount_sats_discount), 
        comment=message
    ).get("pr")
    if not payreq:
        raise HTTPException(500, "Unable to generate an Invoice from Lightning Address.")

    coinos.send_lightning_payment(
        payreq=payreq, 
        amount=amount_sats_discount, 
        maxfee=maxfee
    )

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

    tx_status = redis.redis_get(f"tx.{txid}")
    if tx_status and tx_status.get("paid", False):
        raise HTTPException(400)

    data["id"] = id
    data["txid"] = txid
    data["payment_type"] = payment_type
    data["message"] = message
    data["paid"] = data.get("confirmed", False)
    data["lightning_address"] = lightning_address
    redis.redis_set(f"tx.{txid}", data)

    if data.get("confirmed"):
        amount_sats = data["amount"]
        amount_sats_discount = amount_sats 
        amount_sats_discount-= round(calculate_percentage(amount_sats_discount, 1))
        amount_sats_discount = abs(amount_sats_discount)
        maxfee = abs(amount_sats - amount_sats_discount)
        if maxfee < 1:
            maxfee = 1

        payreq = LightningAddress.fetch_invoice(
            lightning_address, 
            amount=sats_to_msats(amount_sats_discount), 
            comment=message
        ).get("pr")
        if not payreq:
            raise HTTPException(500, "Unable to generate an Invoice from Lightning Address.")

        coinos.send_lightning_payment(
            payreq=payreq, 
            amount=amount_sats_discount, 
            maxfee=maxfee
        )

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
