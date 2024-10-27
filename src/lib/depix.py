import requests

class Depix:

    def __init__(
            self, 
            url: str = "http://localhost:8080",
            key: str = None
        ) -> None:
        self.url = url
        self.key = key

    def call(self, method: str, path: str, data=None) -> dict:
        response = requests.request(
            method=method, 
            url=self.url + path,
            json=data,
            headers={ "X-API-KEY": self.key }
        )
        response.raise_for_status()
        return response.json()

    def create_qrcode(self, amount: float, address: str) -> dict:
        return self.call("POST", "/api/v1/qrcode", data={"amount": amount, "address": address})
