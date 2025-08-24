from dataclasses import dataclass
import os
import json
"""
Configuration settings for the pharmacy site selection report generator.
"""
from typing import Dict

# Scoring criteria and their weights
CRITERIA = ["traffic", "demographics", "competitive", "healthcare", "complementary"]

CRITERION_WEIGHTS: Dict[str, float] = {
    "traffic": 25.0,
    "demographics": 30.0,
    "competitive": 15.0,
    "healthcare": 20.0,
    "complementary": 10.0
}

# Maximum possible total score
MAX_TOTAL = sum(CRITERION_WEIGHTS.values())

# Chart and visualization settings
CHART_DPI = 200
CHART_FIGSIZE = (15, 8)
MAP_DPI = 150
MAP_FIGSIZE = (10, 7.5)

# File paths
DEFAULT_SCORES_PATH = "data/scores.json"
DEFAULT_OUTPUT_DIR = "report_output"
DEFAULT_OUTPUT_FILENAME = "report.md"
DEFAULT_TOP_N = 10

# Matplotlib settings for Arabic text support
FONT_FAMILY = 'Arial'
UNICODE_MINUS = False
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
        "FRC3": 0.6,
        "FRC4": 1,  
        "FRC5": 1,
        "FRC6": 0.9,
        "FRC7": 0.7,
        "FRC8" : 0.6
        }
        }