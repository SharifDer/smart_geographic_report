import requests
import datetime
import geopandas as gpd
from shapely.geometry import Polygon, shape
# import matplotlib.pyplot as plt
import sys
import os
import json
from fetchers.utils import generate_bbox


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
        # "total_population": total_population,
        # "total_male_count" : total_male_count,
        # "total_female_count" : total_female_count,
        "avg_density": round((sum(pop_density_values) / len(pop_density_values)) , 2),
        "avg_median_age": round((sum(age_values) / len(age_values)) , 2),
        # "avg_median_male_age" : round((sum(male_age_values) / len(male_age_values)) , 2),
        # "avg_median_female_age" : round((sum(female_age_values) / len(female_age_values)) , 2),
        "avg_income": round((sum(income_values) / len(income_values)) , 2),
        # "geometries": geometries
    }

def population_data(lat, lng, token, user_id):
    bbox = generate_bbox(lat, lng)
    raw_data = fetch_demographics(bbox, token=token, user_id=user_id)
    processed = process_demographics(raw_data)

    if processed is None:
        processed = {}

    percentage_age_above_35 = (processed.get("avg_median_age", 0) - 35 + 50) if processed else 0
    percentage_mage_above_35 = (processed.get("avg_median_male_age", 0) - 35 + 50) if processed else 0
    percentage_fage_above_35 = (processed.get("avg_median_female_age", 0) - 35 + 50) if processed else 0

    processed.update({
        "percentage_age_above_35": percentage_age_above_35,
        "percentage_mage_above_35": percentage_mage_above_35,
        "percentage_fage_above_35": percentage_fage_above_35
    })
    # Add new percentages directly into processed dict
    # processed.update({
    #     "percentage_age_above_35": percentage_age_above_35,
    #     "percentage_mage_above_35": percentage_mage_above_35,
    #     "percentage_fage_above_35": percentage_fage_above_35
    # })

    return processed
