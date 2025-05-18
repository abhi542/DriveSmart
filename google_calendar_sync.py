import datetime
import os
import pickle
import datetime as dt


from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request


# Scopes give permission to access the calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def add_event_to_google_calendar(service_date_str, summary="Car Service Reminder"):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8888)

        # Save credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Convert date
    service_date = dt.datetime.strptime(service_date_str, "%Y-%m-%d")
    event = {
        'summary': summary,
        'start': {'date': service_date_str},
        'end': {'date': (service_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")},
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print(f"✅ Event created: {event.get('htmlLink')}")