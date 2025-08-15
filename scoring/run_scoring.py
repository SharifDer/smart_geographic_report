import os
import json

from scoring.traffic import score_traffic_for_retail
from scoring.healthcare import score_healthcare_ecosystem, score_competitive
from scoring.complementary_businesses import score_complementary_businesses
from scoring.demographics import score_demographics
# from Config import Weights, Config

def run_full_scoring(Weights , locations_dir , targeted_scoring_file ):

    results = {}

    directory_path = locations_dir  # should be a string directory path, e.g. "data/loc_data"

    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        
        if not os.path.isfile(filepath):
            print(f"Skipping non-file: {filepath}")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        lat = data.get("lat")
        lng = data.get("lng")
        place_name = data.get("place name")
        if lat is None or lng is None:
            print(f"Missing lat/lng in {filepath}, skipping")
            continue

        # Compose key
        loc_key = f"{lat},{lng}"
        location_data = data.get("location_data", {})

        traffic_data = location_data.get("traffic", {})
        healthcare_data = location_data.get("healthcare", {})
        amenities_data = location_data.get("nearest_businessess", {})
        pop_data = location_data.get("pop_data", {})
        frc_weights = Weights.frc_weights
        traffic_score_weight = Weights.traffic_score
        print("filename" , filepath)
        if traffic_data:
            traffic_score = score_traffic_for_retail(
                average_speed=traffic_data.get("Average Vehicle Speed in km", 0),
                frc=traffic_data.get("Functional Road Class", ""),
                frc_weights=frc_weights,
                traffic_score=traffic_score_weight
            )
        
        demographics_score = score_demographics(pop_data, Weights.population_score)
        healthcare_score = score_healthcare_ecosystem(healthcare_data, Weights.healthcare_score)
        competitive_score = score_competitive(healthcare_data, Weights.competitive_score)
        complementary_score = score_complementary_businesses(amenities_data, Weights.complementary_score)


        results[loc_key] = {
            "place name" : place_name,
            "lat": lat,
            "lng": lng,
            "scores": {
                "traffic": traffic_score,
                "demographics": demographics_score,
                "competitive": competitive_score,
                "healthcare": healthcare_score,
                "complementary": complementary_score,
            }
        }

    with open(targeted_scoring_file, "w" , encoding="utf-8") as f:
        json.dump(results ,f , ensure_ascii=False , indent=2)

