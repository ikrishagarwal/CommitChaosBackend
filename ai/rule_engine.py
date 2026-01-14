def apply_rules(anomaly, features):
    speed, distance, time_gap, zone_risk, deviation = features

    if not anomaly["is_anomaly"]:
        return None

    severity = "LOW"

    if zone_risk == 1 and time_gap > 1800:
        severity = "HIGH"
    elif time_gap > 1200:
        severity = "MEDIUM"

    return {
        "type": "BEHAVIORAL_ANOMALY",
        "severity": severity,
        "confidence": anomaly["confidence"],
        "reason": "Unusual tourist movement detected"
    }
