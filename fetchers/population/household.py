import json
from shapely.geometry import shape, box
import sys
import os 
from fetchers.utils import generate_bbox, bbox_to_polygon


def load_housing_features(path):
    try :
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["features"]
    except Exception as e :
        print(f"Error during loading the data {str(e)}")


def collect_housing_stats(features, bbox_polygon):
    matched = []
    Household_Average_Size = []
    Household_Median_Size = []
   
    for feature in features:
        polygon = shape(feature["geometry"])
        
        if polygon.intersects(bbox_polygon):
            matched.append(feature["id"])
            props = feature["properties"]
            Household_Average_Size.append(props.get("HHAVG"))
            Household_Median_Size.append(props.get("HHMED"))

    # Clean the lists by removing any None values before performing calculations
    Household_Average_Size = [x for x in Household_Average_Size if x is not None]
    Household_Median_Size = [x for x in Household_Median_Size if x is not None]
    try:
        avg_median_size = sum(Household_Median_Size) / len(Household_Median_Size)
        avg_average_size = sum(Household_Average_Size) / len(Household_Average_Size)
    except ZeroDivisionError:
        avg_median_size = 0
        avg_average_size = 0

    return matched, {
        "Household_Median_Size": round(avg_median_size , 2),
        "Household_Average_Size": round(avg_average_size , 2)
    }


#main function that for the household data bringing
def household_data( lat , lng , features  ):
    # features = load_housing_features(household_data_path)
    bbox = generate_bbox(lat, lng, radius_km=3)
    bbox_poly = bbox_to_polygon(bbox)
    _ , stats = collect_housing_stats(features, bbox_poly)
    return stats
