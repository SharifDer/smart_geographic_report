from dataclasses import dataclass
import os
import json

@dataclass
class Config():
    targeted_lat: float = 24
    targeted_lng: float = 46.7031
    tomtom_api: str = ""
    google_maps_api : str = ""
    email : str = ""
    password : str = ""
    data_dir: str = "data"
    images_dir : str = "images"
    loc_data : str = data_dir + "/loc_data"
    raw_data : str = data_dir + "/raw_data"
    data_file : str = ""
    household_data_path : str = data_dir +"/v12.8z/v12/all_features.json"
    housing_data_path : str = data_dir + "/v12/v12/all_features.json"

    # pharmacies_data_dir : str = f"{data_dir}/pharmacies"
    # pharmacies_data_file : str = f"{pharmacies_data_dir}/{targeted_lat}_{targeted_lng}_nearest_10_pharmacies.json"
    # pharmacies_routes_file : str = f"{pharmacies_data_dir}/{targeted_lat}_{targeted_lng}_pharmacies_routes.json"
    # healthcare_data_folder = f"{data_dir}/healthcare"
    # healthcare_routes_folder = f"{healthcare_data_folder}/healthcare_routes_data"
    # healthcare_nearby_data = f"{healthcare_data_folder}/healthcare_places_data"
    # other_business_data = f"{data_dir}/other_business_data"
    # other_business_routes = f"{data_dir}/other_business_routes"
    weights = {
            "traffic_score": 0.25,
            "population_score": 0.30,
            "competitive_score": 0.15,
            "healthcare_score": 0.20,
            "complementary_score": 0.10,
        }
     # Scoring Thresholds
    traffic_thresholds = {
        "non_highway": ["FRC0", "FRC1"],
        "other_shops_score": 5,
        "high_traffic_speed": 35,
        "medium_traffic_speed": 50,
        "non_highway_points": 10,
        "other_shops_points": 5,
        "high_traffic_points": 10,
        "medium_traffic_points": 5,
    }
    population_thresholds = {
        "high_density_housings": 150000,
        "medium_density_housings": 100000,
        "low_density_housings": 50000,
        "high_age_pct": 50,
        "medium_age_pct": 40,
        "high_income": 12000,
        "medium_income": 10000,
        "large_household_size": 2.7,
        "medium_household_size": 2.0,
        "high_density_points": 10,
        "medium_density_points": 7,
        "low_density_points": 4,
        "high_age_points": 10,
        "medium_age_points": 7,
        "high_income_points": 5,
        "medium_income_points": 3,
        "large_household_points": 5,
        "medium_household_points": 3,
    }
    competitive_thresholds = {
        "high_distance": 2000,
        "medium_distance": 1000,
        "low_distance": 500,
        "low_saturation_count": 50,
        "medium_saturation_count": 100,
        "high_distance_points": 7,
        "medium_distance_points": 4,
        "low_distance_points": 2,
        "low_saturation_points": 5,
        "medium_saturation_points": 3,
        "underserved_points": 3,
    }
    healthcare_thresholds = {
        "very_close_avg_dist": 1000,
        "moderately_close_avg_dist": 2000,
        "reasonably_close_avg_dist": 3000,
        "very_close_points": 15,
        "moderately_close_points": 10,
        "reasonably_close_points": 5,
    }
    complementary_thresholds = {
        "grocery_close": 500,
        "grocery_medium": 1000,
        "restaurant_close": 200,
        "restaurant_medium": 500,
        "bank_close": 300,
        "bank_medium": 700,
        "atm_close": 300,
        "atm_medium": 700,
        "close_points": 2.5,
        "medium_points": 1.5,
    }

    # File Paths and Directories
    images_dir = "report_images"
    data_file_path = "combined_report_data.json"
    output_file = "pharmacy_report.md"

    @classmethod
    def get_conf(cls, lat , lng ,path="secrets/secrets.json" ):
        cls.targeted_lat = lat
        cls.targeted_lng = lng
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls.tomtom_api = data.get("tomtom_api")
                cls.email = data.get("email")
                cls.password = data.get("password")
                cls.google_maps_api = data.get("google_maps_api")
            cls.data_file = os.path.join(cls.loc_data , f"{cls.targeted_lat}_{cls.targeted_lng}.json")
            cls.pharmacies_data_dir : str = f"{cls.data_dir}/pharmacies"
            # cls.pharmacies_data_file : str = f"{cls.pharmacies_data_dir}/{cls.targeted_lat}_{cls.targeted_lng}_nearest_10_pharmacies.json"
            # cls.pharmacies_routes_file : str = f"{cls.pharmacies_data_dir}/{cls.targeted_lat}_{cls.targeted_lng}_pharmacies_routes.json"
            # cls.healthcare_data_folder = f"{cls.data_dir}/healthcare"
            # cls.healthcare_routes_folder = f"{cls.healthcare_data_folder}/healthcare_routes_data"
            # cls.healthcare_nearby_data = f"{cls.healthcare_data_folder}/healthcare_places_data"
            # cls.other_business_data = f"{cls.data_dir}/other_business_data"
            # cls.other_business_routes = f"{cls.data_dir}/other_business_routes"
            return cls
        except Exception as e:
            print(f"[WARN] Error loading config: {e}")
        return cls()  # Fallback default