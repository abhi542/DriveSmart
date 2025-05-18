import json
from datetime import datetime, timedelta
from google_calendar_sync import add_event_to_google_calendar
import os

DATA_FILE = 'service_log.json'

# Load data
def load_service_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data
def save_service_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Get next service date
def calculate_next_service_date(last_date_str, interval_months=6):
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
    next_date = last_date + timedelta(days=interval_months*30)
    return next_date.strftime("%Y-%m-%d")

# Log new service
def log_service():
    data = load_service_data()

    if not data:
        return False, "No service data found. Please enter the first service date."

    # Add new service entry (this can be done without specifying user_id)
    new_date = datetime.today().strftime("%Y-%m-%d")
    
    for user_id in data:
        data[user_id]['history'].append(new_date)
        data[user_id]['last_service_date'] = new_date
        data[user_id]['next_service_date'] = calculate_next_service_date(new_date)

    save_service_data(data)
    
    # Add all service dates to Google Calendar
    for user_id in data:
        add_event_to_google_calendar(data[user_id]['next_service_date'], "Next Car Service")
    
    return True, "Service logged successfully."

# First time setup or re-setting service date after clearing history
def set_first_service_date(service_date):
    data = load_service_data()

    # Reset everything and start fresh
    data = {}

    # Set first service date and calculate next service date
    data['user_1'] = {
        'last_service_date': service_date,
        'next_service_date': calculate_next_service_date(service_date),
        'history': [service_date]
    }

    save_service_data(data)

    # Add first service to Google Calendar
    add_event_to_google_calendar(data['user_1']['next_service_date'], "Next Car Service")
    return True