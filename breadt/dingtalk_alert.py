# -*- coding: utf-8 -*-

import hmac
import hashlib
import base64
import urllib.parse
import time
from loguru import logger
import requests

# ACCESS_TOKEN = '2b122b4e786300fde8c3d447c44ae3ec73aedb6ab5f45d9373d7c0154ed31d17'
# SECRET = 'SEC57e5b83bdc088439ccc50d15ab604e29b6f813b8fc70e36b992d44ec8f5e2fae'

# 当前主要使用
# ACCESS_TOKEN = "b060a98409426bb860b190b00317ed4dda29f80d0b30ab7484889afb0803a2d3"
# SECRET = "SEC88015e806f1b6b2b6a744f1d4ee65289cd483e35e7510ae71d1d11fa66c45432"


class DingTalkAlert:
    def __init__(self, secret, access_token) -> None:
        self.secret = secret
        self.access_token = access_token

    def send_alert(self, message="股票Tick数据跑好了 @大大") -> None:
        timestamp = str(round(time.time() * 1000))

        secret_enc = self.secret.encode("utf-8")
        string_to_sign = "{}\n{}".format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        url = (
            "https://oapi.dingtalk.com/robot/send?access_token=%s&timestamp=%s&sign=%s"
            % (self.access_token, timestamp, sign)
        )

        headers = {"Content-Type": "application/json"}

        data = {"msgtype": "text", "text": {"content": message}}
        requests.post(url, headers=headers, json=data)
