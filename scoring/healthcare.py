def score_competitive(healthcare_data, weight_score):
    nearby_pharmacies = healthcare_data['pharmacy'].get('nearby_pharmacy', [])
    pharmacies_per_10k = healthcare_data['pharmacy'].get('pharmacies_per_10k_population', 0) / 100

    if nearby_pharmacies:
        nearest_distance = min(p['est_driving_distance_meters'] for p in nearby_pharmacies)
    else:
        nearest_distance = 3000  # large distance, underserved
    # Normalize distance score: farther is better, capped at 5 km
    distance_score = min(nearest_distance / 500, 1.0)

    # Normalize saturation: assume 0 to 20 pharmacies per 10k population
    saturation_score = max(0, (1 - pharmacies_per_10k))

    # Average of the two criteria (0..1)
    average_score = (distance_score + saturation_score) / 2

    return {
        "overall_score": (average_score * weight_score) * 100,
        "details": {
            "Distance to nearest pharmacy": distance_score * 100,
            "Market saturation": saturation_score * 100,
            "Underserved population pockets" : "N/A"
        }
    }


def score_healthcare_ecosystem(healthcare_data, weight_score):
    def score_proximity(places):
        if not places:
            return 0.0
        max_distance = 1500  # meters
        within_3km = [p for p in places if p['est_driving_distance_meters'] <= max_distance]
        if not within_3km:
            return 0.0

        avg_distance = sum(p['est_driving_distance_meters'] for p in within_3km) / len(within_3km)
        avg_distance_score = 1 - min(1, avg_distance / max_distance)
        count_score = min(len(within_3km), 5) / 5
        return avg_distance_score * count_score

    hospitals_score = score_proximity(healthcare_data.get('nearby_hospital', []))
    dentists_score = score_proximity(healthcare_data.get('nearby_dentist', []))

    average_score = (hospitals_score + dentists_score) / 2
    return {
        "overall_score": (average_score * weight_score) * 100,
        "details": {
            "Proximity to hospitals": hospitals_score * 100,
            " Proximity to dentists": dentists_score * 100
        }
    }
