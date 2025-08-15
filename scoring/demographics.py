def score_demographics(pop_data: dict, weight_score: float) -> dict:
    """
    Scores demographics by combining:
    - Residential density (avg_density)
    - Age 35+ (%)
    - Income (avg_income)
    - Household size (median or average size)
    
    Returns dict with weighted overall score and detailed scores.
    """

    MAX_DENSITY = 6000    # people per sq km (adjust as max observed)
    MAX_INCOME = 11000     # SAR monthly (approximate upper bound)
    MAX_HOUSEHOLD_SIZE = 4 # large families in area
 
    density_score = min(pop_data.get("avg_density", 0) / MAX_DENSITY, 1.0)
    age_score = min(pop_data.get("percentage_age_above_35", 0) / 60, 1.0)
    income_score = min(pop_data.get("avg_income", 0) / MAX_INCOME, 1.0)
    
    household_size = pop_data.get("Household_Median_Size", pop_data.get("Household_Average_Size", 1))
    household_score = min(household_size / MAX_HOUSEHOLD_SIZE, 1.0)

    average_score = (density_score + age_score + income_score + household_score) / 4

    return {
        "overall_score": (average_score * weight_score) * 100,
        "details": {
            " Residential density within 3km driving radius": (density_score * 100),
            "Age distribution above 35": age_score * 100,
            "Income levels": income_score * 100,
            "Household composition": household_score * 100
        }
    }
