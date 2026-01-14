import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def extract_features(prev, curr, zone_risk, deviation):
    distance = haversine(
        prev["lat"], prev["lon"],
        curr["lat"], curr["lon"]
    )

    time_gap = (curr["timestamp"] - prev["timestamp"]).seconds

    speed = (distance / time_gap) * 3.6 if time_gap > 0 else 0

    return [
        speed,
        distance,
        time_gap,
        zone_risk,
        deviation
    ]
