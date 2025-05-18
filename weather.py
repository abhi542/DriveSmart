import requests
from openrouteservice import Client
from flask import Blueprint, jsonify, request

# Hardcoded API keys
ORS_API_KEY = "5b3ce3597851110001cf62484ee8b8904df24d65b8eb10cfd475d87a"  # Your OpenRouteService API key
WEATHERAPI_KEY = "845006fdce204c8380d161636250705"  # Your WeatherAPI key

client = Client(key=ORS_API_KEY)

# Create a Blueprint for the weather routes
weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/route')
def route():
    start = request.args.get('start')
    end = request.args.get('end')
    result = get_weather_and_route_data(start, end)
    return jsonify(result)

def geocode(place):
    url = f'https://api.openrouteservice.org/geocode/search?api_key={ORS_API_KEY}&text={place}'
    res = requests.get(url).json()
    coords = res['features'][0]['geometry']['coordinates']
    return coords  # [lon, lat]

def get_weather_and_route_data(start, end):
    try:
        start_coords = geocode(start)
        end_coords = geocode(end)
    except Exception as e:
        return {'error': f'Geocoding failed: {str(e)}'}

    try:
        # Get route geometry
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
        geometry = route['features'][0]['geometry']['coordinates']
        route_points = [(lat, lon) for lon, lat in geometry]

        # Sample points along the route
        sampled = route_points[::max(1, len(route_points)//15)]
    except Exception as e:
        return {'error': f'Route fetch failed: {str(e)}'}

    weather_data = []
    for lat, lon in sampled:
        try:
            url = f'https://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={lat},{lon}'
            res = requests.get(url)
            data = res.json()
            location_name = data.get('location', {}).get('name', 'Unknown')
            temp = data.get('current', {}).get('temp_c', 'N/A')
            description = data.get('current', {}).get('condition', {}).get('text', 'N/A')
            weather_data.append({
                'lat': lat,
                'lon': lon,
                'location': location_name,
                'temp': temp,
                'description': description,
                'alert': "None"
            })
        except Exception as e:
            print(f"Weather fetch failed for ({lat},{lon}): {e}")
            continue

    return {
        'route': route_points,
        'weather': weather_data,
        'distance': round(route['features'][0]['properties']['summary']['distance'] / 1000, 2),
        'duration': f"{int(route['features'][0]['properties']['summary']['duration'] // 3600)}h {int((route['features'][0]['properties']['summary']['duration'] % 3600) // 60)}m"
    }
