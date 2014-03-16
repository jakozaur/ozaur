# coding=utf-8

import requests
import time
import hmac
import hashlib
import json

import config
from main import app

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

  def verify_order_validity(self, coinbase_order_id, value_satoshi, custom_field):
    url = "https://coinbase.com/api/v1/orders/%s" % (coinbase_order_id)

    nounce = str(int(time.time() * 1e6))
    message = nounce + url
    signed = hmac.new(config.COINBASE_SECRET_KEY, message, hashlib.sha256).hexdigest()

    r = requests.get(
      url,
      headers = {"ACCESS_KEY": self.api_key,
        "ACCESS_SIGNATURE": signed,
        "ACCESS_NONCE": nounce,
        "Content-Type": "application/json"})

    if not r.ok:
      app.logger.error("Error while veryfing the transaction %s" % (r.text))
      return False

    json = r.json()

    if "order" not in json:
      app.logger.error("Can't find order with given id, someone might be evil! Expected id: %s, got '%s'" % (coinbase_order_id, r.text))
      return False

    order = json["order"]

    if order["id"] != coinbase_order_id:
      app.logger.error("Value of id mismatches, someone might be evil! Expected: %d, got '%s'" % (coinbase_order_id, r.text))
      return False

    if order["total_btc"]["cents"] != value_satoshi:
      app.logger.error("Value of transaction mismatches, someone might be evil! Expected: %d, got '%s'" % (value_satoshi, r.text))
      return False

    if order["custom"] != custom_field:
      app.logger.error("Custom field mismatches, someone miht be evil! Expected: %s, got '%s'", custom_field, r.text)
      return False

    app.logger.info("Verified '%s' transaction successfully. Verify: '%s'" % (custom_field, r.text))
    return True







