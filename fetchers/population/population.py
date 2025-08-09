import requests
import datetime
import geopandas as gpd
from shapely.geometry import Polygon, shape
# import matplotlib.pyplot as plt
import sys
import os
import json

def generate_bbox(center_lat , center_lng , radius_km=3):
    delta = radius_km / 111
    return {
        "min_lng": center_lng - delta,
        "max_lng": center_lng + delta,
        "min_lat" : center_lat - delta,
        "max_lat" : center_lat + delta
    }

def auth_token(email , password):
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

def fetch_demographics(bbox, token=None, user_id=None):
    url = "http://37.27.195.216:8000/fastapi/fetch_population_by_viewport"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "message": "Requesting demographic data for a specific area",
        "request_info": {
        },
        "request_body": {
            **bbox,
            "zoom_level": 12,
            "user_id": user_id,
            "population": True,
            "income": True
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def process_demographics(data):
    features = data["data"]["features"]
    if not features:
        return None
    
    total_population = 0
    total_male_count = 0
    total_female_count = 0
    pop_density_values = []
    age_values = []
    income_values = []
    geometries = []
    male_age_values = []
    female_age_values = []
    for f in features:
        props = f["properties"]
        total_population += props.get("Population_Count") or 0
        total_male_count += props.get("Male_Population") or 0
        total_female_count += props.get("Female_Population") or 0
        pop_density_values.append(props.get("Population_Density_KM2", 0))
        age_values.append(props.get("Median_Age_Total") or 0)
        male_age_values.append(props.get("Median_Age_Male") or 0)
        female_age_values.append(props.get("Median_Age_Female") or 0)
        income_values.append(props.get("income", 0))
        geometries.append(shape(f["geometry"]))
    return {
        "total_population": total_population,
        "total_male_count" : total_male_count,
        "total_female_count" : total_female_count,
        "avg_density": sum(pop_density_values) / len(pop_density_values),
        "avg_median_age": sum(age_values) / len(age_values),
        "avg_median_male_age" : sum(male_age_values) / len(male_age_values),
        "avg_median_female_age" : sum(female_age_values) / len(female_age_values),
        "avg_income": sum(income_values) / len(income_values),
        # "geometries": geometries
    }

def population_data(lat , lng , email , password):
    all_results = []
    site = {
        "lat" : lat,
        "lng" : lng
    }
    bbox = generate_bbox(lat, lng)
    user_id, token = auth_token(email=email, password=password)
    raw_data = fetch_demographics(bbox, token=token, user_id=user_id)
    processed = process_demographics(raw_data)
    all_results.append({
        "site": site,
        "data": processed  # store raw response for printing later
    })
    percentage_age_above_35 = (processed["avg_median_age"]- 35) + 50
    percentage_mage_above_35 = (processed["avg_median_male_age"]- 35) + 50
    percentage_fage_above_35 = (processed["avg_median_female_age"]- 35) + 50
    all_results[0]["data"].update(
        {
            "percentage_age_above_35" : percentage_age_above_35,
            "percentage_mage_above_35" : percentage_mage_above_35,
             " percentage_fage_above_35" :  percentage_fage_above_35
        }
    )
    return all_results