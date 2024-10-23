import requests

BASE_URL = "https://coinos.io/api"

class Coinos:

    def __init__(self, token=None):
        self.token = token

    def register(self, username, password):
        url = f"{BASE_URL}/register"
        payload = {
            "user": {
                "username": username,
                "password": password,
            }
        }
        return self.make_request("POST", url, payload)

    def login(self, username, password):
        url = f"{BASE_URL}/login"
        payload = {
            "username": username,
            "password": password
        }
        result = self.make_request("POST", url, payload)
        if result:
            self.token = result.get("token")
        return self.token

    def create_invoice(self, amount: float, invoice_type: str, webhook=None, secret=None, currency="USD"):
        url = f"{BASE_URL}/invoice"
        payload = {
            "invoice": {
                "amount": amount,
                "type": invoice_type,
                "webhook": webhook,
                "secret": secret,
                "currency": currency
            }
        }
        return self.make_request("POST", url, payload)

    def get_invoice(self, hash):
        url = f"{BASE_URL}/invoice/{hash}"
        return self.make_request("GET", url)

    def send_lightning_payment(self, payreq):
        url = f"{BASE_URL}/payments"
        payload = {
            "payreq": payreq
        }
        return self.make_request("POST", url, payload)

    def send_internal_payment(self, username, amount):
        url = f"{BASE_URL}/send"
        payload = {
            "amount": amount,
            "username": username
        }
        return self.make_request("POST", url, payload)

    def send_bitcoin_payment(self, address, amount):
        url = f"{BASE_URL}/bitcoin/send"
        payload = {
            "amount": amount,
            "address": address
        }
        return self.make_request("POST", url, payload)

    def get_payments(self, start=None, end=None, limit=None, offset=None):
        url = f"{BASE_URL}/payments"
        params = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return self.make_request("GET", url, params=params)

    def make_request(self, method, url, payload=None, params=None):
        headers = {
            "Content-Type": "application/json"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, json=payload)

        response.raise_for_status()
        if response.text:
            return response.json()
        return None
