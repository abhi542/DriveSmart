import sys
import os
import logging
import requests
from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, flash
from openrouteservice import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure Python finds local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import feature modules
from drowsiness import generate_frames
from sos import send_sos
from carservice import set_first_service_date, log_service, load_service_data
from route_optimiser import get_optimized_route
from download_maps import generate_offline_map

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

# Weather API Keys
ORS_API_KEY = "5b3ce3597851110001cf62484ee8b8904df24d65b8eb10cfd475d87a"
WEATHERAPI_KEY = "845006fdce204c8380d161636250705"  # Replace with your actual key
client = Client(key=ORS_API_KEY)

# ========== Routes ==========

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/drowsiness')
def drowsiness():
    return render_template('drowsiness.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sos')
def sos():
    return render_template('sos.html')

@app.route('/send_sos')
def sos_alert():
    return send_sos()


@app.route('/service_reminder', methods=['GET', 'POST'])
def service_reminder():
    user_id = "default_user"
    data = load_service_data()

    if request.method == 'POST':
        if 'first_service_date' in request.form:
            service_date = request.form['first_service_date']
            set_first_service_date(user_id, service_date)
            flash("First service date set successfully.")
            return redirect(url_for('service_reminder'))

        elif 'log_service' in request.form:
            success, message = log_service()
            flash(message)
            return redirect(url_for('service_reminder'))

    user_data = data.get(user_id)
    return render_template('service_reminder.html', user_data=user_data)

# Route Optimization API
# Route Optimization API (Only POST Allowed)
@app.route('/route-optimization', methods=['POST'])
def route_optimization():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    origin = data.get("origin")
    destination = data.get("destination")

    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required"}), 400

    logging.info(f"Route request: {origin} -> {destination}")

    route_map = get_optimized_route(origin, destination)

    if not route_map:
        return jsonify({"error": "Failed to retrieve optimized route"}), 500

    return jsonify({"success": True, "map_path": route_map})

# Route Optimization Page
@app.route('/route')
def route_page():
    return render_template('route.html')


@app.route('/offline_maps', methods=['GET', 'POST'])
def offline_maps():
    if request.method == 'POST':
        location = request.form.get("location")
        result = generate_offline_map(location)

        if result["success"]:
            return render_template('offlinemaps.html', map_path=result["map_path"])
        else:
            return render_template('offlinemaps.html', error=result["error"])

    return render_template('offlinemaps.html')

# ===== Live Location Tracker =====
@app.route('/location-tracker')
def location_tracker():
    return render_template('location.html')

@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.get_json()
    latitude = data['latitude']
    longitude = data['longitude']

    print(f"[LIVE LOCATION] Latitude: {latitude}, Longitude: {longitude}")

    return jsonify({'latitude': latitude, 'longitude': longitude})

# ===== Weather Page =====
@app.route('/weather')
def weather_page():
    return render_template('weather.html')

@app.route('/route-weather')
def get_route_weather():
    start = request.args.get('start')
    end = request.args.get('end')

    def geocode(place):
        url = f'https://api.openrouteservice.org/geocode/search?api_key={ORS_API_KEY}&text={place}'
        res = requests.get(url).json()
        coords = res['features'][0]['geometry']['coordinates']
        return coords  # [lon, lat]

    try:
        start_coords = geocode(start)
        end_coords = geocode(end)
    except Exception as e:
        return jsonify({'error': f'Geocoding failed: {str(e)}'})

    try:
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',
            format='geojson'
        )
        geometry = route['features'][0]['geometry']['coordinates']
        route_points = [(lat, lon) for lon, lat in geometry]
        sampled = route_points[::max(1, len(route_points)//15)]
    except Exception as e:
        return jsonify({'error': f'Route fetch failed: {str(e)}'})

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
                'alert': "None"  # Free tier of WeatherAPI
            })
        except Exception as e:
            print(f"Weather fetch failed for ({lat},{lon}): {e}")
            continue

    return jsonify({
        'route': route_points,
        'weather': weather_data,
        'distance': round(route['features'][0]['properties']['summary']['distance'] / 1000, 2),
        'duration': f"{int(route['features'][0]['properties']['summary']['duration'] // 3600)}h {int((route['features'][0]['properties']['summary']['duration'] % 3600) // 60)}m"
    })

# Run App
if __name__ == '__main__':
    app.run(debug=True)
