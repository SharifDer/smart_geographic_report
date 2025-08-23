import requests
from datetime import datetime, timezone, timedelta
import json
import os
import sys

def get_last_monday_6pm_utc():
    today = datetime.now(timezone.utc)
    last_monday = today - timedelta(days=today.weekday() + 7)
    local_time = last_monday.replace(hour=18, minute=0, second=0, tzinfo=timezone(timedelta(hours=3)))
    return local_time, local_time.astimezone(timezone.utc)


def fetch_traffic_data(conf, target_time_utc):
    lat = conf.targeted_lat
    lng = conf.targeted_lng
    url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    params = {
        "key": conf.tomtom_api,
        "point": f"{lat},{lng}",
        "unit": "KMPH",
        "openLr": "false",
        "time": target_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def extract_metrics(data):
    segment = data.get("flowSegmentData")
    if not segment:
        raise ValueError("No 'flowSegmentData' in API response")

    # travel_time_min = segment['currentTravelTime'] / 60
    # free_flow_time_min = segment['freeFlowTravelTime'] / 60
    # confidence = segment['confidence'] * 100
    current_speed = segment['currentSpeed']
    frc = segment['frc']
    return {
        "Average Vehicle Speed in km": current_speed,
        # "Travel Time minutes": round(travel_time_min, 1),
        # "Free-flow Travel Time": round(free_flow_time_min, 1),
        # "Data Confidence": round(confidence, 0),
        "Functional Road Class": frc
    }


def print_report(lat, lng, target_time_local, metrics):
    print("\n" + "=" * 60)
    print(f"Historical Traffic Data for Olaya Street, Riyadh")
    print(f"Coordinates: ({lat}, {lng})")
    print(f"Day: Monday | Time: 6:00 PM local time")
    print(f"Data from: {target_time_local.strftime('%Y-%m-%d')}")
    print("=" * 60)
    for k, v in metrics.items():
        unit = "km/h" if "Speed" in k else "%"
        print(f"{k}: {v} {unit if k == 'Data Confidence' else ''}".strip())
    print("=" * 60)
def get_traffic_data(conf):
    try : 
        _, target_utc = get_last_monday_6pm_utc()
        data = fetch_traffic_data(conf, target_utc)
        metrics = extract_metrics(data)
        return metrics
    except Exception as e :
        print(f"Error: {str(e)}")