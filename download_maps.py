import folium
import requests
import os
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to get latitude and longitude
def get_coordinates(location):
    session = requests.Session()
    session.verify = False  # Disable SSL verification

    url = f"http://nominatim.openstreetmap.org/search?q={location}&format=json"
    headers = {
        "User-Agent": "DriveSmart/1.0 (contact@drivesmart.com)"
    }

    try:
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            else:
                return None, None
        else:
            print(f"Error: Received status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    return None, None

# Function to generate an offline map
def generate_offline_map(location, zoom=12):
    lat, lon = get_coordinates(location)

    if lat is None or lon is None:
        return {"success": False, "error": "Geolocation failed. Try again with a different location."}

    # Create a map with Folium
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles="OpenStreetMap")

    # Add a marker for the location
    folium.Marker([lat, lon], popup=location, tooltip=location).add_to(m)

    # Save the map as an HTML file
    map_path = f"static/maps/{location.replace(' ', '_')}.html"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    m.save(map_path)

    return {"success": True, "map_path": map_path}