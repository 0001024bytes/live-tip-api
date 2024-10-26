import requests

class Liquid:

    def __init__(
            self, 
            url: str = "http://localhost:4023",
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
        return response.json()

    def get_new_address(self, id: str, label="", webhook_url=None, webhook_key=None) -> dict:
        return self.call("POST", f"/api/v1/liquid/new-address", {"id": id, "label": label, "webhook_url": webhook_url, "webhook_key": webhook_key}) 

    def get_address(self, id: str):
        return self.call("GET", f"/api/v1/liquid/address/{id}")

    def get_balance(self):
        return self.call("GET", "/api/v1/liquid/balance")