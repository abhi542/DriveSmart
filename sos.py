import ssl
import certifi
from twilio.rest import Client
from flask import Flask, jsonify
import requests
from twilio.http.http_client import TwilioHttpClient
from twilio.rest import Client


app = Flask(__name__)

TWILIO_ACCOUNT_SID = "AC939c4611ad3508298375d7fd70cc793e"
TWILIO_AUTH_TOKEN = "23982e6fc67fdbbd3473fefcecbbe25d"
TWILIO_PHONE_NUMBER = "+18286726678"
EMERGENCY_CONTACT = "+8277072243"

class NoSSLVerificationClient(TwilioHttpClient):
    def __init__(self):
        super().__init__()
        self.session.verify = False  # Disable SSL verification

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, http_client=NoSSLVerificationClient())

@app.route('/send_sos')
def send_sos():

    try:
        message = client.messages.create(
            body="🚨 Emergency! This is an SOS alert from ABHINAV. Please respond immediately.",
            from_="+18286726678",  # Replace with your Twilio number
            to="+918277072243"  # Replace with the recipient's number
        )
        print("✅ Message sent successfully! SID:", message.sid)
        return jsonify({"message": "SOS alert sent successfully", "sid": message.sid})

    except Exception as e:
        print("❌ Error sending message:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
