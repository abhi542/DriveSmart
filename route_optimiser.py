import folium
import requests
import os
import polyline

# OpenRouteService API Key
ORS_API_KEY = "5b3ce3597851110001cf624882ffcacadcee4bf4b53d5db47eb06a64"

# Function to get latitude and longitude from location name
def get_coordinates(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json"
    headers = {"User-Agent": "DriveSmart/1.0 (contact@drivesmart.com)"}

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coordinates: {e}")

    return None, None

# Function to get optimized road-based route
def get_optimized_route(origin, destination, zoom=6):
    lat1, lon1 = get_coordinates(origin)
    lat2, lon2 = get_coordinates(destination)

    if None in (lat1, lon1, lat2, lon2):
        print("Error: Could not fetch coordinates.")
        return None

    # OpenRouteService API request
    ors_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "coordinates": [[lon1, lat1], [lon2, lat2]],
        "radiuses": [1000, 1000],  # Increases the search radius (1000m)
        "format": "geojson"
    }

    try:
        response = requests.post(ors_url, json=payload, headers=headers, verify=False)
        route_data = response.json()

        if "routes" not in route_data:
            print("Error: API response does not contain 'routes'")
            print("Full response:", route_data)  # Debugging output
            return None

        # Extract and decode polyline
        encoded_polyline = route_data["routes"][0]["geometry"]  # Encoded geometry
        route_points = polyline.decode(encoded_polyline)  # Convert to (lat, lon)

    except Exception as e:
        print(f"Error fetching route: {e}")
        return None

    # Center map at midpoint
    center_lat, center_lon = (lat1 + lat2) / 2, (lon1 + lon2) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, tiles="OpenStreetMap")

    # Add start and end markers
    folium.Marker([lat1, lon1], popup="Origin", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker([lat2, lon2], popup="Destination", icon=folium.Icon(color="red")).add_to(m)

    # Draw route polyline
    folium.PolyLine(route_points, color="blue", weight=4, opacity=0.7).add_to(m)

    # Save the map
    map_path = f"static/maps/{origin.replace(' ', '_')}_to_{destination.replace(' ', '_')}.html"
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    m.save(map_path)

    print(f"Map saved at: {map_path}")  # Debugging output
    return map_path