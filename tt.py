import requests
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client

TWILIO_ACCOUNT_SID = "AC939c4611ad3508298375d7fd70cc793e"
TWILIO_AUTH_TOKEN = "23982e6fc67fdbbd3473fefcecbbe25d"

# Custom HTTP client to disable SSL verification
class NoSSLVerificationClient(TwilioHttpClient):
    def __init__(self):
        super().__init__()
        self.session.verify = False  # Disable SSL verification

# Use the custom HTTP client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, http_client=NoSSLVerificationClient())

try:
    message = client.messages.create(
        body="🚨 Test SOS Message",
        from_="+18286726678",  # Replace with your Twilio number
        to="+918277072243"  # Replace with the recipient's number
    )
    print("✅ Message sent successfully! SID:", message.sid)
except Exception as e:
    print("❌ Error sending message:", str(e))
