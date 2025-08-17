import json
import sys
import os

# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fetchers.utils import auth_token
from fetchers.population.household import household_data
from fetchers.population.housings import housing_data
from fetchers.population.population import population_data
from fetchers.traffic_data import get_traffic_data
from fetchers.healthcare_system import get_healthcare_data
from fetchers.complementary_businesses import get_other_businesses_data
from fetchers.population.household import load_housing_features
# from fetchers.population.housings import load_housing_features
from fetchers.utils import getting_data_category
import time
from fetchers.data_loader import preload_categories

def fetch_data(conf, user_id, token , household_features , 
                housings_features, hospitals , dentists ,
                pharmacies,  grocery_store_data , supermarket_data,
                 restaurant_data, bank_data,
                  atm_data , place_url ):
    # Fetch all datasets
    traffic = get_traffic_data(conf)
    households = household_data( conf.targeted_lat, conf.targeted_lng , features=household_features )
    housings = housing_data(conf.targeted_lat, conf.targeted_lng, features=housings_features)
    population = population_data(conf.targeted_lat, conf.targeted_lng, token=token, user_id=user_id)
    health_care_data = get_healthcare_data(conf , 
                                           hospital_data=hospitals , 
                                           dentist_data=dentists ,
                                           pharmacies_data=pharmacies)
    other_data = get_other_businesses_data(conf, grocery_store_data , supermarket_data,
                                           restaurant_data , bank_data,
                                           atm_data)

    total_population = population.get("total_population") if population else None
    num_pharmacies = (
            health_care_data.get("healthcare", {})
                            .get("pharmacy", {})
                            .get("num_of_pharmacies")
            if health_care_data else None
        )

    # Calculate pharmacies per 10k population
    pharmacies_per_10k = (num_pharmacies / total_population * 10000) if total_population and total_population > 0 else 0

    # Add the new key right under num_of_pharmacies
    health_care_data["healthcare"]["pharmacy"]["pharmacies_per_10k_population"] = round(pharmacies_per_10k, 2)

    data = {
        "place name" : place_url ,
        "lat": conf.targeted_lat,
        "lng": conf.targeted_lng,
        "location_data": {
            "traffic": traffic,
            "pop_data" : {
                **households,
                **housings,
                **population
            },
        **health_care_data,
        **other_data
        }
    }

    # Save to JSON
    with open(conf.data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
# inside your module where fetch_full_data is defined (replace the block that calls getting_data_category per-category)

def fetch_full_data(conf , user_id , token):
    with open(conf.shops_for_rent , "r" , encoding="utf-8") as f :
        data = json.load(f)
    household_features = load_housing_features(conf.household_data_path)
    housing_features = load_housing_features(conf.housing_data_path)

    # categories to preload
    categories = [
        "hospital", "dentist", "pharmacy",
        "grocery_store", "supermarket", "restaurant",
        "atm", "bank"
    ]

    # Preload everything once (parallel=True is default)
    cached = preload_categories(conf, user_id, token, categories, parallel=True)
    
    # assign variables to keep the rest of your code unchanged
    hospitals_data = cached.get("hospital", {})
    dentists = cached.get("dentist", {})
    pharmacies = cached.get("pharmacy", {})
    grocery_store = cached.get("grocery_store", {})
    supermarket = cached.get("supermarket", {})
    restaurant = cached.get("restaurant", {})
    atm = cached.get("atm", {})
    bank = cached.get("bank", {})

    features = data['data']['features']
    i = 0
           
    for feature in features:
        geometry = feature['geometry']
        coordinates = geometry['coordinates']
        lng = coordinates[0]
        lat = coordinates[1]
        place_url = feature["properties"]["url"]
        last_segment = place_url.split('/')[-1]
        extracted_part = last_segment.rsplit('-', 1)[0]
        conf.get_conf(lat=lat , lng=lng)
        if os.path.exists(conf.data_file):
            continue
     
        fetch_data(conf , user_id=user_id , token=token ,
                    household_features=household_features,
                    housings_features=housing_features, 
                    hospitals=hospitals_data,
                    dentists=dentists,
                    pharmacies=pharmacies, supermarket_data=supermarket,
                    grocery_store_data=grocery_store , restaurant_data=restaurant,
                    atm_data=atm , bank_data=bank , place_url=extracted_part)
        i += 1
        if i % 10 == 0 :
            print(f"number of locations have been fetched {i}")
        time.sleep(0.5)
