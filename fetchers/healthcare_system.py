import requests
import time
import json
import os 
import sys
from geopy.distance import geodesic
from typing import List,Dict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from run_files import conf

def get_places_with_routes(conf, place_type=None, keyword=None):
    """
    Retrieves nearby places via Google Places API and appends driving route info from Google Routes API.
    Saves consolidated data as JSON.
    """
    lat = conf.targeted_lat
    lng = conf.targeted_lng
    places = fetch_places_nearby(lat, lng, place_type=place_type, keyword=keyword)
    if not places:
        print("No places found")
        return None
    fname = f"{conf.healthcare_routes_folder}/{lat}_{lng}_{place_type or 'all'}.json"
    if os.path.exists(fname):
        print(f"Loading cached data from {fname}")
        with open(fname, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            return cached_data
    results = {
        "origin": {"lat": lat, "lng": lng},
        "search_params": {"type": place_type, "keyword": keyword},
        "places": []
    }

    for place in places:
        plat = place["geometry"]["location"]["lat"]
        plng = place["geometry"]["location"]["lng"]
        route = calculate_distance(lat, lng, plat, plng)
        results["places"].append({
            "name": place.get("name"),
            "types": place.get("types", []),
            "location": {"lat": plat, "lng": plng},
            "vicinity": place.get("vicinity"),
            "route": route
        })
    os.makedirs(conf.healthcare_routes_folder, exist_ok=True)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved route data to {fname}")
    return results

def calculate_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> Dict:
    origin = (origin_lat, origin_lng)  # Latitude, Longitude of the origin
    destination = (dest_lat, dest_lng)
    distance = geodesic(origin , destination).meters
    return {
        "est_driving_distance_meters" : int(distance)
    }

def get_route_info(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    Calls Google Routes API `computeRoutes` endpoint (POST JSON).
    Returns distance (meters), duration (seconds), and polyline string.
    """
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": conf.google_maps_api,
        "X-Goog-FieldMask": "routes/legs/distanceMeters"
    }
    body = {
        "origin": {
            "location": {"latLng": {"latitude": origin_lat, "longitude": origin_lng}}
        },
        "destination": {
            "location": {"latLng": {"latitude": dest_lat, "longitude": dest_lng}}
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE"
    }

    try:
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Route API request error: {e}")
        return None

    if "routes" in data and data["routes"]:
        leg = data["routes"][0].get("legs", [{}])[0]
        return {
            "driving_distance_meters": leg.get("distanceMeters"),
        }
    return None


def get_healthcare_count(conf):
    categories = [
        ("hospital", None),       # Official type
        ("dentist", None),        # Official type  
    ]

    total_counts = {
        "hospital": 0,
        "dentist": 0,
    }

    for place_type, keyword in categories:
        route_results = get_places_with_routes(conf, place_type=place_type, keyword=keyword)
        results = route_results["places"] if route_results else []
        key = place_type if place_type else keyword
        total_counts[key] = len(results)
    return total_counts


def fetch_places_nearby(lat, lng, place_type=None, keyword=None, radius=2000):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Create filename based on parameters
    filename = f"{conf.healthcare_nearby_data}/{lat}_{lng}_{place_type}.json"
    os.makedirs(conf.healthcare_nearby_data, exist_ok=True)  # Ensure directory exists
    
    # Check if cached data exists
    if os.path.exists(filename):
        print(f"Loading cached data from {filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            return cached_data.get("results", [])
    
    # Prepare API request
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "key": conf.google_maps_api,
    }
    if place_type:
        params["type"] = place_type
    if keyword:
        params["keyword"] = keyword
    
    # Make API call
    res = requests.get(url, params=params)
    data = res.json()
    
    # Save response to cache
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
    
    print(f"Saved new data to {filename}")
    return data.get("results", [])
x = get_healthcare_count(conf)
print(x)