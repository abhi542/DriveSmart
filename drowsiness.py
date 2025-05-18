import os
import threading
import cv2
import dlib
import numpy as np
from scipy.spatial import distance as dist
import imutils
from imutils import face_utils
from flask import Flask, render_template, Response, jsonify

app = Flask(__name__)

# Load Dlib face detector & landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Constants for drowsiness detection
EYE_AR_THRESH = 0.25
EYE_AR_CONSEC_FRAMES = 30  # Adjust for ~3 seconds
COUNTER = 0
ALARM_ON = False
ALARM_THREAD = None  # Thread for alarm sound

# Get eye landmark indices
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

# Eye aspect ratio function
def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

# Function to continuously play alarm until stopped
def play_alarm():
    global ALARM_ON
    while ALARM_ON:  # Keep playing while eyes are closed
        os.system("ffplay -nodisp -autoexit static/2.wav")  # Play alert sound on Mac

# Video stream generator
def generate_frames():
    global COUNTER, ALARM_ON, ALARM_THREAD

    cap = cv2.VideoCapture(0)  # Open webcam

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = imutils.resize(frame, width=600)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector(gray, 0)

        for rect in rects:
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0

            # Draw eye landmarks
            cv2.drawContours(frame, [cv2.convexHull(leftEye)], -1, (255, 255, 0), 1)
            cv2.drawContours(frame, [cv2.convexHull(rightEye)], -1, (255, 255, 0), 1)

            if ear < EYE_AR_THRESH:
                COUNTER += 1
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    if not ALARM_ON:
                        ALARM_ON = True
                        ALARM_THREAD = threading.Thread(target=play_alarm, daemon=True)
                        ALARM_THREAD.start()  # Start alarm loop
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                COUNTER = 0
                if ALARM_ON:
                    ALARM_ON = False  # Stop the alarm when eyes open

            cv2.putText(frame, f"EAR: {ear:.2f}", (400, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()