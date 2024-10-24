import requests

class LightningAddress:

    @staticmethod
    def get_lnurlp_info(address: str):
        username, domain = address.split("@")
        url = f"https://{domain}/.well-known/lnurlp/{username}"
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception("Failed to fetch Lightning Address information")

        return response.json()

    @staticmethod
    def fetch_invoice(address: str, amount: int, comment: str = "") -> dict:
        lnurlp_info = LightningAddress.get_lnurlp_info(address)
        if len(comment) > lnurlp_info.get("commentAllowed", 0):
            raise ValueError("The comment size is larger than allowed.")
        
        if lnurlp_info.get("minSendable", 0) > amount:
            raise ValueError("Minimum value is greater than amount.")

        if amount > lnurlp_info.get("maxSendable", 0):
            raise ValueError("The amount value is greater than the maximum value.")

        callback_url = lnurlp_info['callback'] + f"?amount={amount}&comment={comment}"
        invoice_response = requests.get(callback_url)
        if invoice_response.status_code != 200:
            raise Exception("Failed to generate invoice")

        return invoice_response.json()