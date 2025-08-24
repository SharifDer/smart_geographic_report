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
        place_price = data.get("price")
        if lat is None or lng is None:
            print(f"Missing lat/lng in {filepath}, skipping")
            continue

        # Compose key
        loc_key = f"{lat},{lng}"
        location_data = data.get("location_data", {})
        num_of_businesses_around = location_data["num of business around"]
        traffic_data = location_data.get("traffic", {})
        healthcare_data = location_data.get("healthcare", {})
        amenities_data = location_data.get("nearest_businessess", {})
        pop_data = location_data.get("pop_data", {})
        frc_weights = Weights.frc_weights
        traffic_score_weight = Weights.traffic_score
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
            "price" : place_price,
            "scores": {
                "overall_score" : (traffic_score["overall_score"] + demographics_score["overall_score"] + 
                                   healthcare_score["overall_score"] + competitive_score["overall_score"] + complementary_score["overall_score"]),
                "traffic": traffic_score,
                "demographics": demographics_score,
                "competitive": competitive_score,
                "healthcare": healthcare_score,
                "complementary": complementary_score,
            },
            "data" : {
                'nearby Businesses within 500 meters' : num_of_businesses_around,
               **(traffic_data or {}),
                **(pop_data or {}),
                'competing_pharmacies' : healthcare_data.get("pharmacy" , 0).get("num_of_pharmacies" , 0),
                "pharmacies_per_10k_population" : healthcare_data.get("pharmacy").get("pharmacies_per_10k_population" ),
                "number of hospitals around" : healthcare_data.get("num_of_hospitals"),
                "number of dentists around" : healthcare_data.get("num_of_dentists") 
            }
        }

    with open(targeted_scoring_file, "w" , encoding="utf-8") as f:
        json.dump(results ,f , ensure_ascii=False , indent=2)

