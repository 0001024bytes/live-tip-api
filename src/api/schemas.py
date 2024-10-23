from pydantic import BaseModel

class CoinosWebhookSchema(BaseModel):
    amount: float
    confirmed: bool
    hash: str
    received: float 
    text: str
    secret: str