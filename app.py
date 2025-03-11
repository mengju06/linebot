import os
import requests
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, URITemplateAction, TextSendMessage

app = Flask(__name__)

# 環境變數（需在 Render 設定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Geocoding API 查詢函式
def get_lat_lng(location):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": location,
        "key": GOOGLE_MAPS_API_KEY,
        "language": "zh-TW"
    }
    response = requests.get(url, params=params).json()
    
    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None, None

# Google Places API (New) 查詢函式
def search_nearby_restaurants(lat, lng):
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.rating,places.id,places.formattedAddress,places.photos"
    }
    data = {
        "includedTypes": ["restaurant"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": 500.0
            }
        }
    }
    response = requests.post(url, headers=headers, json=data).json()
    
    if "places" in response:
        return response["places"]
    return None

# 建立 Carousel Template 訊息
def create_carousel_message(restaurants):
    columns = []
    
    for restaurant in restaurants:
        name = restaurant["displayName"]["text"]
        rating = restaurant.get("rating", "無評分")
        address = restaurant.get("formattedAddress", "地址未知")
        place_id = restaurant["id"]
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
        
        # 取得照片網址
        if "photos" in restaurant:
            photo_reference = restaurant["photos"][0]["name"]
            photo_url = f"https://places.googleapis.com/v1/{photo_reference}/media?key={GOOGLE_MAPS_API_KEY}&maxWidthPx=400"
        else:
            photo_url = "https://via.placeholder.com/400x300?text=No+Image"

        column = CarouselColumn(
            thumbnail_image_url=photo_url,
            title=name[:40],  # 限制長度
            text=f"⭐ 評分: {rating}\n📍 {address[:40]}",  # 避免過長
            actions=[
                URITemplateAction(label="查看地圖", uri=maps_url)
            ]
        )
        columns.append(column)
    
    return TemplateSendMessage(alt_text="附近餐廳推薦", template=CarouselTemplate(columns=columns))

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
    lat, lng = get_lat_lng(user_input)
    
    if lat and lng:
        restaurants = search_nearby_restaurants(lat, lng)
        if restaurants:
            carousel_message = create_carousel_message(restaurants)
            line_bot_api.reply_message(event.reply_token, carousel_message)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="附近找不到餐廳。"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="找不到該地點，請重新輸入。"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# import os
# import requests
# from flask import Flask, request, jsonify
# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError
# from linebot.models import MessageEvent, TextMessage, TextSendMessage

# app = Flask(__name__)

# # 環境變數（需在 Render 設定）
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
# GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
# handler = WebhookHandler(LINE_CHANNEL_SECRET)

# # Google Geocoding API 查詢函式
# def get_lat_lng(location):
#     url = "https://maps.googleapis.com/maps/api/geocode/json"
#     params = {
#         "address": location,
#         "key": GOOGLE_MAPS_API_KEY,
#         "language": "zh-TW"
#     }
#     response = requests.get(url, params=params).json()
    
#     if response["status"] == "OK":
#         # 取得第一個結果的經緯度
#         location = response["results"][0]["geometry"]["location"]
#         lat = location["lat"]
#         lng = location["lng"]
#         return lat, lng
#     return None, None

# # Google Places API (New) 查詢函式
# def search_nearby_restaurants(lat, lng):
#     url = "https://places.googleapis.com/v1/places:searchNearby"
#     headers = {
#         "Content-Type": "application/json",
#         "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
#         "X-Goog-FieldMask": "places.displayName,places.rating,places.id"
#     }
#     data = {
#         "includedTypes": ["restaurant"],
#         "maxResultCount": 10,
#         "locationRestriction": {
#             "circle": {
#                 "center": {
#                     "latitude": lat,
#                     "longitude": lng
#                 },
#                 "radius": 500.0  # 搜尋半徑（單位：米）
#             }
#         }
#     }
#     response = requests.post(url, headers=headers, json=data).json()
    
#     if "places" in response:
#         return response["places"]
#     return None

# # 建立回傳訊息
# def create_reply_message(lat, lng, restaurants):
#     # 地點的經緯度
#     location_info = f"📍 地點經緯度：\n緯度: {lat}\n經度: {lng}\n\n"
    
#     # 餐廳資訊
#     restaurants_info = "🍽️ 附近餐廳：\n"
#     for i, restaurant in enumerate(restaurants, 1):
#         name = restaurant["displayName"]["text"]
#         rating = restaurant.get("rating", "無評分")
#         place_id = restaurant["id"]
#         maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
#         restaurants_info += f"{i}. {name} ⭐{rating}\n{maps_url}\n\n"
    
#     return location_info + restaurants_info

# @app.route("/callback", methods=["POST"])
# def callback():
#     signature = request.headers.get("X-Line-Signature")
#     body = request.get_data(as_text=True)
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         return "Invalid signature", 400
#     return "OK"

# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     user_input = event.message.text
#     lat, lng = get_lat_lng(user_input)
    
#     if lat and lng:
#         restaurants = search_nearby_restaurants(lat, lng)
#         if restaurants:
#             reply_text = create_reply_message(lat, lng, restaurants)
#         else:
#             reply_text = "附近找不到餐廳。"
#     else:
#         reply_text = "找不到該地點，請重新輸入。"
    
#     line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

