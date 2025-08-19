import json
from shapely.geometry import shape, box
from fetchers.utils import generate_bbox,bbox_to_polygon

def load_housing_features(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["features"]

def collect_housing_stats(features, bbox_polygon):
    matched = []
    total = {
        "Total_housings": 0,
        "Residential_housings": 0,
        "Non_Residential_housings": 0,
        "Owned_housings": 0,
        "Rented_housings": 0,
        "Provided_housings": 0,
        "Other_Residential_housings": 0,
        "Public_Housing": 0,
        "Work_Camps": 0,
        "Commercial_housings": 0,
        "Other_housings": 0
    }
    poylgons_objects = []
    for feature in features:
        polygon = shape(feature["geometry"])
        
        if polygon.intersects(bbox_polygon):
            poylgons_objects.append(polygon.intersection(bbox_polygon))
            matched.append(feature["id"])
            props = feature["properties"]
            total["Total_housings"] += props.get("H_DWLG_CNT", 0)
            total["Residential_housings"] += props.get("H_DWLG_T_RID", 0)
            total["Non_Residential_housings"] += props.get("H_DWLG_T_COM", 0)
            total["Owned_housings"] += props.get("H_OWNED_RID_H_CNT", 0)
            total["Rented_housings"] += props.get("H_RENTED_RID_H_CNT", 0)
            total["Provided_housings"] += props.get("H_PROV_RID_H_CNT", 0)
            total["Other_Residential_housings"] += props.get("H_OTH_RID_H_CNT", 0)
            total["Public_Housing"] += props.get("H_DWLG_T_COM_PUB", 0)
            total["Work_Camps"] += props.get("H_DWLG_T_COM_WRK", 0)
            total["Commercial_housings"] += props.get("H_DWLG_T_COM_COMM", 0)
            total["Other_housings"] += props.get("H_DWLG_OTH", 0)
    return matched, total

def housing_data(lat , lng , features):
    # features = load_housing_features(housing_data_path)
    bbox = generate_bbox(lat , lng)
    bbox_poly = bbox_to_polygon(bbox)
    _ ,stats = collect_housing_stats(features , bbox_poly)
    return stats
