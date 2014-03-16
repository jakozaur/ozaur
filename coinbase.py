# coding=utf-8

import requests
import time
import hmac
import hashlib
import json

import config

class Coinbase(object):
  def __init__(self):
    self.api_key = config.COINBASE_API_KEY
    self.secret_key = config.COINBASE_SECRET_KEY

  def generate_payment_link(self, buyer, seller, value_satoshi, urls):
    string_bitcoin = str(value_satoshi)
    if len(string_bitcoin) < 9:
      string_bitcoin = "%09d" % (value_satoshi)
    price_string = string_bitcoin[:-8] + "." + string_bitcoin[-8:]
    value_micro = value_satoshi / config.SATOSHI_IN_MICRO

    print urls
    # TODO: add success/cancel url
    data = {
      "button": {
          "name": "Payment for the attention of '%s'" % (seller.display_name),
          "type": "buy_now",
          "price_string": price_string,
          "price_currency_iso": "BTC",
          "custom": "%d:%d" % (buyer.id, seller.id),
          "callback_url": urls["callback"],
          "cancel_url": urls["cancel"],
          "description": u"You need to pay %d μBTC to place a bid. After your bid will be accepted, you could send message to '%s'. '%s' promise to spent at least 5 minutes and reply to you." % (value_micro, seller.display_name, seller.display_name),
          "style": "none",
          "include_email": False
        }
    }

    # TODO: add logging

    body = json.dumps(data)
    url = "https://coinbase.com/api/v1/buttons"
    nounce = str(int(time.time() * 1e6))
    message = nounce + url + body
    signed = hmac.new(config.COINBASE_SECRET_KEY, message, hashlib.sha256).hexdigest()

    r = requests.post(
      url,
      headers = {"ACCESS_KEY": self.api_key,
        "ACCESS_SIGNATURE": signed,
        "ACCESS_NONCE": nounce,
        "Content-Type": "application/json"},
      data = body)

    if not r.ok:
      # TODO: Add logging
      return None

    response = r.json()
    if "button" not in response or "code" not in response["button"]:
      # TODO: Add logging
      return None

    return "https://coinbase.com/checkouts/%s" % (response["button"]["code"])
