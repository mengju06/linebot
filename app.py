import os
import requests
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數（需在 Render 設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("")
LINE_CHANNEL_SECRET = os.getenv("")
GOOGLE_MAPS_API_KEY = os.getenv("")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Places API 查詢函式
def search_hotels(location):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{location} 高評價飯店",
        "key": GOOGLE_MAPS_API_KEY,
        "type": "lodging",
        "language": "zh-TW"
    }
    response = requests.get(url, params=params).json()
    
    if "results" in response:
        hotels = response["results"][:10]  # 取前 10 筆
        hotel_info = []
        for hotel in hotels:
            name = hotel.get("name", "未知名稱")
            rating = hotel.get("rating", "無評分")
            place_id = hotel.get("place_id")
            maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            hotel_info.append(f"{name} ⭐{rating}\n{maps_url}")
        return "\n\n".join(hotel_info)
    return "找不到相關飯店資訊。"

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
    reply_text = search_hotels(user_input)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
