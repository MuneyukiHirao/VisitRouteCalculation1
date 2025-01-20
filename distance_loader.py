import math
import random
import requests

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2)**2 
         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

def get_travel_time(lat1, lon1, lat2, lon2, use_google_api=False, google_api_key=None):
    if use_google_api and google_api_key:
        # 実際にはGoogle Maps Directions APIコール
        # 例： https://maps.googleapis.com/maps/api/directions/json?origin=lat1,lon1&destination=lat2,lon2&mode=driving&key=google_api_key
        # ここではモック例
        try:
            url = f"https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": f"{lat1},{lon1}",
                "destination": f"{lat2},{lon2}",
                "mode": "driving",
                "key": google_api_key
            }
            response = requests.get(url, params=params)
            data = response.json()
            if data["status"] == "OK":
                # 複数ルートある場合最初のルート
                duration_sec = data["routes"][0]["legs"][0]["duration"]["value"]
                # 分に変換
                return duration_sec / 60.0
            else:
                print("Google API error:", data["status"], "Falling back to haversine.")
        except Exception as e:
            print("Exception calling Google API:", e, "Falling back to haversine.")

    # フォールバック：ハバサイン+固定速度
    speed_kmh = 30.0
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    base_time = (dist / speed_kmh) * 60.0
    factor = random.uniform(1.2, 1.5)
    return base_time * factor
