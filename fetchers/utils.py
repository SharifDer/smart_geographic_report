import requests
import json
import os
from shapely.geometry import box
from geopy.distance import geodesic

def auth_token(email , password):
    """  
    parameters : email , password
    returns : user_id , token
    """
    login_endpoint = "http://37.27.195.216:8000/fastapi/login"
    login_data = {
        "message": "string",
        "request_info": {
            "additionalProp1": {}
        },
        "request_body": {
            "email": email,
            "password": password
        }
        }
    login_response = requests.post(url=login_endpoint , json=login_data)
    data = login_response.json()
    user_id = data["data"]["localId"]
    token = data["data"]["idToken"]
    return user_id , token


def generate_bbox(center_lat , center_lng , radius_km=1):
    delta = radius_km / 111
    return {
        "min_lng": center_lng - delta,
        "max_lng": center_lng + delta,
        "min_lat" : center_lat - delta,
        "max_lat" : center_lat + delta
    }

def bbox_to_polygon(bbox):
    return box(bbox["min_lng"], bbox["min_lat"], bbox["max_lng"], bbox["max_lat"])


def getting_data_category(user_id : str , token : str , data_dir : str , category : str = "hospital" , city : str = "Riyadh" , country : str = "Saudi Arabia") -> dict :
    """
    Return the data fetched for a specific category
    For example it returns all pharmacies in Riyadh if category pharmacy
    """
        # Send request (you must define headers and payload yourself)
    fname = f"{data_dir}/{category}.json"
    if os.path.exists(fname):
        with open(fname ,"r" , encoding="utf-8" ) as f:
            print(f"Loading file {category} from cache")
            data = json.load(f)
            return data
    url = "http://37.27.195.216:8000/fastapi/fetch_dataset"
    headers = {
        "Authorization": f"Bearer {token}"
        ,"Content-Type": "application/json"
    }

    # Payload
    payload = {
        "message": "string",
        "request_info": {
            "additionalProp1": {}
        },
        "request_body": {
            "lat": 0,
            "lng": 0,
            "user_id": f"{user_id}",
            "prdcer_lyr_id": "",
            "city_name": f"{city}",
            "country_name": f"{country}",
            "boolean_query": f"{category}",
            "action": "full data",
            "page_token": "",
            "search_type": "category_search",
            "text_search": "",
            "zoom_level": 0,
            "radius": 30000,
            "bounding_box": [],
            "included_types": [],
            "excluded_types": [],
            "ids_and_location_only": False,
            "include_rating_info": False,
            "include_only_sub_properties": True,
            "full_load": True
        }
    }
    print(f"Downloading file {category} from ep")
    response = requests.post(url, json=payload, headers=headers)
    with open(fname , "w" , encoding="utf-8") as f:
        json.dump(response.json() , f , indent=2 , ensure_ascii=False)
    return response.json()


def calculate_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict:
    origin = (origin_lat, origin_lng)  # Latitude, Longitude of the origin
    destination = (dest_lat, dest_lng)
    distance = geodesic(origin , destination).meters
    return {
        "est_driving_distance_meters" : int(distance)
    }