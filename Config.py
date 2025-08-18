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
    shops_for_rent : str = data_dir + "/shops_for_rent.json"
    scoring_file_dir : str = data_dir + "/scores.json"
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
            return cls
        except Exception as e:
            print(f"[WARN] Error loading config: {e}")
        return cls()  # Fallback default

class Weights():
    traffic_score = 0.25
    population_score = 0.30
    competitive_score = 0.15
    healthcare_score = 0.20
    complementary_score = 0.10 

    frc_weights = {
        "FRC" : {
        "FRC0": 0.0,  
        "FRC1": 0.0,
        "FRC2": 0.3,
        "FRC3": 1,
        "FRC4": 1,  
        "FRC5": 0.9,
        "FRC6": 0.9,
        "FRC7": 0.7,
        "FRC8" : 0.6
        }
        }