# from flask import Flask, request, abort

# from linebot import (
#     LineBotApi, WebhookHandler
# )
# from linebot.exceptions import (
#     InvalidSignatureError
# )
# from linebot.models import *
# import tempfile, os
# import datetime
# import time
# import traceback

# app = Flask(__name__)

# # Channel Access Token
# line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
# # Channel Secret
# handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# # 監聽所有來自 /callback 的 Post Request
# @app.route("/callback", methods=['POST'])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers['X-Line-Signature']
#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)
#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)
#     return 'OK'

# # 處理訊息
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     message = TextSendMessage(text=event.message.text)
#     line_bot_api.reply_message(event.reply_token, message)

# import os
# if __name__ == "__main__":
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host='0.0.0.0', port=port)

import os
import requests
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數（需在 Render 設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Maps Geocoding API 查詢函式
def get_location_map_url(location):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location,
        "key": GOOGLE_MAPS_API_KEY,
        "language": "zh-TW"
    }
    response = requests.get(url, params=params).json()
    
    if "results" in response and len(response["results"]) > 0:
        # 取得經緯度
        lat = response["results"][0]["geometry"]["location"]["lat"]
        lng = response["results"][0]["geometry"]["location"]["lng"]
        # 生成 Google 地圖連結
        maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        return maps_url
    return None

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    maps_url = get_location_map_url(user_input)
    
    if maps_url:
        reply_text = f"地點的地圖連結：\n{maps_url}"
    else:
        reply_text = "找不到該地點，請重新輸入。"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
