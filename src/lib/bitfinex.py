import requests
import json

class Bitfinex:

    def __init__(
            self, 
            url="https://api.bitfinex.com/"
        ):
        self.__url = url

    def call(self, method: str, path: str, data=None, params=None):
        body = json.dumps(data).encode('utf-8')
        headers = { 'Content-Type': 'application/json' }
        response = requests.request(method.upper(), self.__url + path, headers=headers, params=params, data=body)
        response.raise_for_status()
        return response.json()
    
    def get_price(self, ticket="btcusd"):
        r = self.call("GET", f"v1/pubticker/{ticket}")
        return {"SELL": r["ask"], "BUY": r["bid"]}
