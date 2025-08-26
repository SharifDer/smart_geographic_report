def score_traffic_for_retail(average_speed, frc, frc_weights, traffic_score):
    """
    Scores traffic conditions for retail based on average vehicle speed and functional road class (FRC).
    
    Returns a dict with weighted overall score and details of sub-scores.
    """
    # Speed normalization: in retail, moderate speed (~40–60 km/h) is ideal
    if average_speed < 20:
        speed_score = 0.6
    elif 20 <= average_speed <= 30 :
        speed_score = 1.0
    elif 30 < average_speed <= 50:
        speed_score = 0.8
    elif 50 < average_speed <= 70:
        speed_score = 0.7
    else:
        speed_score = 0.3  # highway speeds

    frc_score = frc_weights.get("FRC").get(frc , 0.5)

    combined_score = 0.5 * speed_score + 0.5 * frc_score
    # overall_score = traffic_score * combined_score

    return {
        "overall_score": (combined_score * traffic_score) * 100,
        "details": {
            "Average Viechle Speed": speed_score * 100,
            "highway score": frc_score * 100,
        }
    }
