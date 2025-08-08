import os
import json
import requests
from typing import List, Dict
import sys
import time
from geopy.distance import geodesic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from run_files import conf

def cache_exists(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def fetch_nearby_pharmacies(conf , radius: int = 3000, max_results: int = 10) -> List[Dict]:
    """Fetch and cache top N nearby pharmacies"""
    lat = conf.targeted_lat
    lng = conf.targeted_lng
    cache_file =  conf.pharmacies_data_file
    if cache_exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            print(f"Data loaded from cache {cache_file}")
            return json.load(f)

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "type": "pharmacy",
        "key": conf.google_maps_api
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data:
        raise ValueError(f"Places API error: {data}")

    top_pharmacies = data["results"][:max_results]

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(top_pharmacies, f, indent=2, ensure_ascii=False)

    return top_pharmacies

#get approximate distance 
def calculate_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict:
    origin = (origin_lat, origin_lng)  # Latitude, Longitude of the origin
    destination = (dest_lat, dest_lng)
    distance = geodesic(origin , destination).meters
    return {
        "est_driving_distance_meters" : distance
    }
def find_top_10_pharmacies_with_routes(conf) -> Dict:
    pharmacies = fetch_nearby_pharmacies(conf)
    results = {
        "origin": {"lat": conf.targeted_lat, "lng": conf.targeted_lng},
        "places": []
    }

    for p in pharmacies:
        dest = p["geometry"]["location"]
        route = calculate_distance(conf.targeted_lat, conf.targeted_lng, dest["lat"], dest["lng"])
        if not isinstance(route, dict) or "est_driving_distance_meters"  not in route:
            continue

        results["places"].append({
            "name": p.get("name"),
            "address": p.get("vicinity"),
            "location": dest,
            "est_driving_distance_meters": int(route["est_driving_distance_meters"] , )
        })
    cache_file = conf.pharmacies_routes_file
    with open(cache_file , "w" , encoding="utf-8") as f :
        json.dump(results , f , indent=2 , ensure_ascii=False)
    results["places"] = sorted(results["places"], key=lambda x: x["est_driving_distance_meters"])[:10]
    return results


if __name__ == "__main__":

    try:
        top10 = find_top_10_pharmacies_with_routes(conf)
    except Exception as e:
        print(f"[FATAL ERROR] {e}")
