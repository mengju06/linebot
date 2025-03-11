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
from linebot.models import (
    MessageEvent, TextMessage, ImageSendMessage, TemplateSendMessage,
    ButtonsTemplate, URIAction
)

app = Flask(__name__)

# 環境變數（需在 Render 設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Places API 查詢函式
def get_location_info(location):
    # 查詢地點的 place_id
    find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": location,
        "inputtype": "textquery",
        "fields": "photos,geometry",
        "key": GOOGLE_MAPS_API_KEY
    }
    response = requests.get(find_place_url, params=params).json()
    
    if "candidates" in response and len(response["candidates"]) > 0:
        place = response["candidates"][0]
        # 取得經緯度
        lat = place["geometry"]["location"]["lat"]
        lng = place["geometry"]["location"]["lng"]
        # 取得第一張圖片的 photo_reference
        if "photos" in place and len(place["photos"]) > 0:
            photo_reference = place["photos"][0]["photo_reference"]
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
        else:
            photo_url = None
        # 生成 Google 地圖連結
        maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        return photo_url, maps_url
    return None, None

# 建立 Button Template
def create_button_template(maps_url, location_name):
    button_template = TemplateSendMessage(
        alt_text="地點地圖",
        template=ButtonsTemplate(
            title="地點地圖",
            text=f"點擊按鈕查看 {location_name} 的地圖",
            actions=[
                URIAction(
                    label="查看地圖",
                    uri=maps_url  # 按鈕連結
                )
            ]
        )
    )
    return button_template

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
    photo_url, maps_url = get_location_info(user_input)
    
    if photo_url and maps_url:
        # 回傳圖片
        image_message = ImageSendMessage(
            original_content_url=photo_url,
            preview_image_url=photo_url
        )
        # 回傳按鈕
        button_template = create_button_template(maps_url, user_input)
        line_bot_api.reply_message(event.reply_token, [image_message, button_template])
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該地點，請重新輸入。"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
