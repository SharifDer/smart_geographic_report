import requests
import time
import json
import os
from geopy.distance import geodesic
import sys 


def get_places_with_routes(conf, place_type=None, keyword=None ):
    """
    Retrieves nearby places (from single cached dataset), filters by type/keyword,
    computes distances, saves results per type as before.
    """
    lat = conf.targeted_lat
    lng = conf.targeted_lng
    fname = f"{conf.other_business_routes}/{lat}_{lng}_{place_type or 'all'}.json"
    if os.path.exists(fname):
        print(f"Loading cached data from {fname}")
        with open(fname, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            return cached_data

    # Load once-fetched full dataset
    all_places = fetch_places_nearby(conf)

    results = {
        "origin": {"lat": lat, "lng": lng},
        "search_params": {"type": place_type, "keyword": keyword},
        "places": []
    }

    for place in all_places:
        place_types = place.get("types", [])
        name = place.get("name", "").lower()

        if place_type and place_type not in place_types:
            continue
        if keyword and keyword.lower() not in name:
            continue

        plat = place["geometry"]["location"]["lat"]
        plng = place["geometry"]["location"]["lng"]
        distance_meters = calculate_distance(lat, lng, plat, plng)
        results["places"].append({
            "name": place.get("name"),
            "types": place.get("types", []),
            "location": {"lat": plat, "lng": plng},
            "vicinity": place.get("vicinity"),
            "distance in meters": distance_meters
        })

    os.makedirs(conf.other_business_routes, exist_ok=True)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved route data to {fname}")
    return results


def calculate_distance(origin_lat, origin_lng, dest_lat, dest_lng):
    origin = (origin_lat, origin_lng)
    dest = (dest_lat, dest_lng)
    return int(geodesic(origin, dest).meters)


def get_other_business_count(conf):
    categories = [
        ("grocery_or_supermarket", None),
        ("restaurant", None),
        ("bank", None),
        ("atm", None),
    ]

    total_counts = {
        "grocery_or_supermarket": 0,
        "restaurant": 0,
        "bank": 0,
        "atm": 0
    }

    for place_type, keyword in categories:
        route_results = get_places_with_routes(conf, place_type=place_type, keyword=keyword)
        results = route_results["places"] if route_results else []
        key = place_type if place_type else keyword
        total_counts[key] = len(results)

    return total_counts


def fetch_places_nearby(conf , radius=500):
    lat = conf.targeted_lat
    lng = conf.targeted_lng
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    filename = f"{conf.other_business_data}/{lat}_{lng}_all.json"
    os.makedirs(conf.other_business_data, exist_ok=True)

    if os.path.exists(filename):
        print(f"Loading cached data from {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            return cached_data.get("results", [])

    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "key": conf.google_maps_api,
    }

    res = requests.get(url, params=params)
    time.sleep(2)
    data = res.json()

    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    print(f"Saved new data to {filename}")
    return data.get("results", [])


# x = get_other_business_count(conf)
# print(x)
