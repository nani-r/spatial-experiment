import requests
import json
from geopy.distance import geodesic
from itertools import combinations
import math

# --- CONFIG ---
OUTPUT_FILE = "australia_spatial_corpus.jsonl"
CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Hobart", "Canberra", "Darwin", "Alice Springs", "Fraser Island", "Albury-Wodonga"]
TOPONYM_ALIASES = {
    "Fraser Island": "K’gari",
    "Sydney, NSW": "Warrane",
        "Melbourne, VIC": "Naarm",
        "Newcastle, NSW": "Mulubinba",
        "Perth, WA": "Boorlo",
        "Alice Springs, NT": "Mparntwe",
        "Bunbury, WA": "Goomburrup",
        "Mount Gambier, SA": "Berrin",
        "Adelaide, SA": "Tarntanya",
        "Brisbane, QLD": "Meanjin",
        "Albany, WA": "Kinjarling",
        "Canberra, ACT": "Ngambri",
        "Darwin, NT": "Gulumoerrgin",
        "Hobart, TAS": "Nipaluna"
}
CENTROID_CITY = "Albury-Wodonga"

# --- HELPERS ---

def get_city_coords(city):
    query = f"""
    [out:json];
    area["name"="Australia"]->.a;
    node["name"="{city}"](area.a);
    out center;
    """
    response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
    try:
        coords = response.json()['elements'][0]
        return (coords['lat'], coords['lon'])
    except Exception:
        print(f"Failed to get coordinates for {city}")
        return None

def direction_from_to(coord1, coord2):
    # Bearing calculation
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dlon)
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    dirs = ["North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"]
    idx = round(bearing / 45) % 8
    return dirs[idx]

def is_clockwise(p1, p2, center):
    angle1 = math.atan2(p1[1] - center[1], p1[0] - center[0])
    angle2 = math.atan2(p2[1] - center[1], p2[0] - center[0])
    return (angle2 - angle1) % (2 * math.pi) < math.pi

def fetch_rivers():
    query = """
    [out:json][timeout:20];
    rel["admin_level"="2"]["name"="Australia"];
    out body;
    map_to_area -> .a;
    way["waterway"="river"](area.a);
    out body qt 20;
    """
    response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
    return response.json()['elements']

def fetch_states():
    query = """
        [out:json][timeout:60];

    // Get Australia relation and convert to area
    rel["admin_level"="2"]["name"="Australia"];
    out body;
    map_to_area -> .a;

    // Fetch all admin_level=4 boundaries inside Australia (states/territories)
    rel(area.a)["admin_level"="4"]["boundary"="administrative"];
    out body;
    """
    response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
    return response.json()['elements']

# --- MAIN ---

def build_document():
    print("Collecting city coordinates...")
    city_coords = {city: get_city_coords(city) for city in CITIES if get_city_coords(city)}

    docs = []

    print("Building directional relations...")
    for c1, c2 in combinations(city_coords.keys(), 2):
        coord1, coord2 = city_coords[c1], city_coords[c2]
        dir1 = direction_from_to(coord1, coord2)
        dir2 = direction_from_to(coord2, coord1)
        docs.append({"type": "directional", "text": f"{c1} is {dir1} of {c2}."})
        docs.append({"type": "directional", "text": f"{c2} is {dir2} of {c1}."})

    print("Adding topological (river-region) intersections...")
    rivers = fetch_rivers()
    states = fetch_states()
    for river in rivers:
        r_name = river.get("tags", {}).get("name", "Unnamed River")
        for state in states:
            s_name = state.get("tags", {}).get("name", "Unnamed State")
            docs.append({"type": "topological", "text": f"The {r_name} intersects the region {s_name}."})

    print("Adding toponym info...")
    for city, alias in TOPONYM_ALIASES.items():
        docs.append({"type": "toponym", "text": f"{city} is also known as {alias}."})

    print("Building cyclic paths from centroid...")
    center = city_coords.get(CENTROID_CITY)
    if center:
        for c1, c2 in combinations([c for c in city_coords if c != CENTROID_CITY], 2):
            coord1, coord2 = city_coords[c1], city_coords[c2]
            direction = "clockwise" if is_clockwise(coord1, coord2, center[::-1]) else "counterclockwise"
            docs.append({"type": "cyclic", "text": f"With respect to a centroid in {CENTROID_CITY}, moving from {c1} to {c2} is {direction}."})

    print(f"Writing {len(docs)} documents to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")

    print("Done.")

if __name__ == "__main__":
    #states = fetch_states()
    #print(f"Fetched {len(states)} states.")
    build_document()
