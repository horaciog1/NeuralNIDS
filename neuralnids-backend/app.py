import eventlet
eventlet.monkey_patch()

import logwatcher
from joblib import load
import numpy as np
from utils import preprocess_data, engineer_features
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
from dotenv import load_dotenv
from ml_predictor import predict_event
from flask_socketio import SocketIO
import json
import os
from collections import defaultdict, Counter
import geoip2.database
import pandas as pd

app = Flask(__name__, static_folder="static", static_url_path="/")
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for /api/*
load_dotenv()
EVE_LOG = "/var/log/suricata/eve.json"
GEO_DB = "/home/cgarriv/geoipdb/GeoLite2-City_20250325/GeoLite2-City.mmdb"

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")

mail = Mail(app)
socket = SocketIO(app, cors_allowed_origins="*")


# This function loads alerts from the Suricata EVE JSON log file
# and returns a list of dictionaries (JSON Objects) containing
# relevant information about each alert.
def load_alerts(limit=200):
    alerts = []
    if not os.path.exists(EVE_LOG):
        return alerts
    with open(EVE_LOG, "r") as f:
        lines = f.readlines()[-limit:]
        # read each entry in eve.json and parse it
        for line in lines:
            try:
                # parse the JSON entry and "convert" it to a dictionary
                data = json.loads(line)
                # if entry is an alert, extract relevant fields
                if data.get("event_type") == "alert":
                    alerts.append({
                        "timestamp": data.get("timestamp"),
                        "src_ip": data.get("src_ip"),
                        "dest_ip": data.get("dest_ip"),
                        "protocol": data.get("proto"),
                        "signature": data.get("alert", {}).get("signature"),
                        "severity": data.get("alert", {}).get("severity")
                    })
            # skip entry if it could not be parsed as JSON
            except json.JSONDecodeError:
                continue
    return alerts


# define /api/alerts endpoint to return alerts in JSON format
@app.route("/api/alerts")
def get_alerts():
    return jsonify(load_alerts())


# go to the view all alerts webpage
@app.route("/all-alerts")
def all_alerts():
    return send_from_directory("static", "all_alerts.html")


# define /api/locations endpoint to return IP location data in JSON format
@app.route("/api/locations")

# This function iterates through the alerts loaded from the Suricata EVE JSON log file
# and maps each source IP address to its geographical location using the GeoLite2 database.
def get_locations():
    alerts = load_alerts()
    # count occurrences of each source IP address in the alerts
    ip_counts = Counter(a["src_ip"] for a in alerts if a.get("src_ip"))
    # list to hold IP location data dictionaries
    geo_data = []
    try:
        reader = geoip2.database.Reader(GEO_DB)
        # for each IP, get its location and add to geo_data list
        for ip, count in ip_counts.items():
            try:
                response = reader.city(ip)
                # add IP location dictionary to geo_data list
                geo_data.append({
                    "ip": ip,
                    "lat": response.location.latitude,
                    "lng": response.location.longitude,
                    "count": count
                })
            except:
                continue
        reader.close()
    except Exception as e:
        print("GeoIP error:", e)
    # return the list of IP location data dictionaries as JSON object
    return jsonify(geo_data)


@app.route("/api/send-email", methods=["POST", "OPTIONS"])
def send_email():
    if request.method == "OPTIONS":
        # Preflight request handling
        response = app.make_default_options_response()
        headers = response.headers

        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Headers"] = "Content-Type"
        headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"

        return response

    data = request.get_json()
    if not data or "subject" not in data or "body" not in data:
        return jsonify({"error": "Invalid input"}), 400

    msg = Message(subject=data["subject"],
                  sender=app.config["MAIL_USERNAME"],
                  recipients=os.getenv("EMAIL_RECIPIENTS").split(","))
    msg.body = data["body"]

    try:
        mail.send(msg)
        return jsonify({"status": "Email sent successfully"}), 200
    except Exception as e:
        print("Mail send error:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/")
def index():
    return send_from_directory('static', 'index.html')


# --------------------------- ML PREDICTION API START --------------------------- #


def predict_event(input_data):
    # Load model and threshold
    model = load("models/ensemble_stacking_model.joblib")
    with open("logs/optimal_threshold_stacking.txt") as f:
        threshold = float(f.read().strip())

    # Convert input to DataFrame
    df = pd.DataFrame([input_data])

    # Engineer features
    df = engineer_features(df)

    # Preprocess using selected features
    X, _, _ = preprocess_data(df, selected_features_file="models/top25_features.txt")

    # Predict
    proba = model.predict_proba(X)[:, 1][0]
    prediction = int(proba >= threshold)

    return {
        "Prediction": prediction,
        "Confidence": round(proba, 4),
        "Label": "Attack" if prediction == 1 else "Normal"
    }

@app.route("/api/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return jsonify({"info": "Send a POST request with JSON data to get a prediction."})
    try:
        event = request.get_json()
        if not event:
            return jsonify({"Error": "No JSON data provided"}), 400

        result = predict_event(event)
        return jsonify(result), 200
    except Exception as e:
        print("Prediction error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/ml_alerts")
def get_ml_alerts():
    enriched_alerts = []
    try:
        with open("logs/ml_alerts.jsonl", "r") as f:
            for line in f.readlines()[-200:]:  # limit to recent alerts
                enriched_alerts.append(json.loads(line))
    except Exception as e:
        print("[!] Could not load ML alerts:", e)
    return jsonify(enriched_alerts)

@app.route("/api/live-alerts")
def live_alerts():
    try:
        with open("logs/ml_alerts.jsonl", "r") as f:
            lines = f.readlines()
            alerts = [json.loads(line.strip()) for line in lines if line.strip()]
        return jsonify(alerts[-5:])  # only return last 10
    except Exception as e:
        print(f"[X] Error loading ML alerts: {e}")
        return jsonify([]), 500
    

# --------------------------- ML PREDICTION API END --------------------------- #


    
# --------------------------- WEBSOCKET API START --------------------------- #


@socket.on("connect")
def handle_connect():
    print("Client connected")


# --------------------------- WEBSOCKET API END --------------------------- #

if __name__ == "__main__":
    #app.run(host="0.0.0.0", port=5000, debug=True)
    socket.start_background_task(logwatcher.watcher, socket)
    socket.run(app, host="0.0.0.0", port=5000, debug=True)
    
