import requests

class BitPreco:

    def __init__(self) -> None:
        self.url = "https://api.bitpreco.com"

    def call(self, method: str, path: str) -> dict:
        response = requests.request(method=method, url=self.url + path)
        return response.json()

    def get_price(self, ticket="btc-brl") -> dict:
        r = self.call("GET", f"/{ticket}/ticker")
        return {"SELL": r["sell"], "BUY": r["buy"], "RATIO": r["var"]}