from flask import Flask, jsonify
import json
import os
from collections import defaultdict, Counter
import geoip2.database

app = Flask(__name__)
EVE_LOG = "/var/log/suricata/eve.json"
GEO_DB = "/home/cgarriv/geoipdb/GeoLite2-City_20250325/GeoLite2-City.mmdb"


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

@app.route("/")
def index():
    return "NeuralNIDS API Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
