# fetchers/complementary_businesses.py
from fetchers.utils import generate_bbox, bbox_to_polygon, calculate_distance
from shapely.geometry import Point

def process_category_data(conf, typ, data, distance_key='est_distance_meters', radius_km=1):
    """
    Process category 'data' (already loaded). Returns {'nearby_{typ}': [...]}
    distance_key controls output field name so we don't change existing saved structures.
    """
    category_data = data or {}
    bbox = generate_bbox(conf.targeted_lat, conf.targeted_lng, radius_km=radius_km)
    area_polygon = bbox_to_polygon(bbox)

    results = {f"nearby_{typ}": []}
    features = category_data.get("data", {}).get("features", [])
    for feature in features:
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2:
            continue
        lng, lat = coords[0], coords[1]
        point = Point(lng, lat)
        if area_polygon.contains(point):
            dist_data = calculate_distance(conf.targeted_lat, conf.targeted_lng, lat, lng)
            results[f"nearby_{typ}"].append({
                "name": feature.get("properties", {}).get("name", ""),
                "coordinates": [lng, lat],
                distance_key: dist_data["est_driving_distance_meters"]
            })
    return results

def get_other_businesses_data(conf, grocery_store_data, supermarket_data,
                              restaurant_data, bank_data, atm_data):
    def top_n_closest(category_results, key, n=5):
        items = category_results.get(key, [])
        items_sorted = sorted(items, key=lambda x: x["est_distance_meters"])
        return items_sorted[:n]

    categories = [
        "grocery_store",
        "supermarket",
        "restaurant",
        "atm",
        "bank"
    ]

    input_map = {
        "grocery_store": grocery_store_data,
        "supermarket": supermarket_data,
        "restaurant": restaurant_data,
        "atm": atm_data,
        "bank": bank_data
    }

    amenities = {}
    num_of_businesses_around = 0
    for category in categories:
        data = input_map.get(category, {})
        key = f"nearby_{category}"
        # Keep the same key name used previously for amenities: 'est_distance_meters'
        results = process_category_data(conf, category, data, distance_key='est_distance_meters')
        num_of_businesses_around += len(results[key])
        results[key] = top_n_closest(results, key, 5)
        amenities[category] = {**results}

    return {
        "num of business around" : num_of_businesses_around,
        "nearest_businessess": amenities
   
    }
