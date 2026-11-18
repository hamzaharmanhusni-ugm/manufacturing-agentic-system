import math

from shared.config import SEA_ROUTE_FACTOR


def haversine_nm(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 3440.065 * math.asin(math.sqrt(h))


def sea_distance_nm(a, b):
    # ponytail: straight line x route factor; swap for a searoute library when real routes matter
    return haversine_nm(a, b) * SEA_ROUTE_FACTOR


def interpolate(a, b, f):
    return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
