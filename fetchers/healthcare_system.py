
from fetchers.utils import generate_bbox, bbox_to_polygon, getting_data_category, calculate_distance
from shapely.geometry import Point


def process_category_data(conf, user_id, token, typ):
    category_data = getting_data_category(user_id, token, conf.raw_data, category=typ)

    # Make polygon for radius area
    bbox = generate_bbox(conf.targeted_lat, conf.targeted_lng)
    area_polygon = bbox_to_polygon(bbox)

    results = {f"nearby_{typ}": []}

    features = category_data.get("data", {}).get("features", [])
    for feature in features:
        coords = feature.get("geometry", {}).get("coordinates", [])
        if len(coords) != 2:
            continue

        lng, lat = coords[0], coords[1]  # GeoJSON = [lng, lat]

        # Check if point is inside polygon
        point = Point(lng, lat)
        if area_polygon.contains(point):
            # Calculate distance
            dist_data = calculate_distance(conf.targeted_lat, conf.targeted_lng, lat, lng)

            results[f"nearby_{typ}"].append({
                "name": feature.get("properties", {}).get("name", ""),
                "coordinates": [lng, lat],
                "est_driving_distance_meters": dist_data["est_driving_distance_meters"]
            })

    return results

def get_healthcare_data(conf, user_id, token):
    types = ["hospital", "dentist"]

    hospitals = process_category_data(conf, user_id, token, types[0])
    dentists = process_category_data(conf, user_id, token, types[1])
    pharmacies = process_category_data(conf, user_id, token, "pharmacy")
    num_pharmacies = len(pharmacies.get("nearby_pharmacy", []))
    def top_n_closest(category_results, key, n=5):
        items = category_results.get(key, [])
        items_sorted = sorted(items, key=lambda x: x["est_driving_distance_meters"])
        return items_sorted[:n]

    hospitals["nearby_hospital"] = top_n_closest(hospitals, "nearby_hospital", 5)
    dentists["nearby_dentist"] = top_n_closest(dentists, "nearby_dentist", 5)
    pharmacies["nearby_pharmacy"] = top_n_closest(pharmacies, "nearby_pharmacy", 5)


    return {
        "healthcare": {
             "pharmacy": {
                "num_of_pharmacies": num_pharmacies,
                **pharmacies
            },
            **hospitals,
            **dentists,
           
        }
    }
