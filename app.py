from flask import Flask, jsonify
import json
import os
from collections import defaultdict, Counter
import geoip2.database

app = Flask(__name__)
EVE_LOG = "/var/log/suricata/eve.json"
GEO_DB = "/home/cgarriv/geoipdb/GeoLite2-City_20250325/GeoLite2-City.mmdb"

def load_alerts(limit=200):
    alerts = []
    if not os.path.exists(EVE_LOG):
        return alerts
    with open(EVE_LOG, "r") as f:
        lines = f.readlines()[-limit:]
        for line in lines:
            try:
                data = json.loads(line)
                if data.get("event_type") == "alert":
                    alerts.append({
                        "timestamp": data.get("timestamp"),
                        "src_ip": data.get("src_ip"),
                        "dest_ip": data.get("dest_ip"),
                        "protocol": data.get("proto"),
                        "signature": data.get("alert", {}).get("signature"),
                        "severity": data.get("alert", {}).get("severity")
                    })
            except json.JSONDecodeError:
                continue
    return alerts

@app.route("/api/alerts")
def get_alerts():
    return jsonify(load_alerts())

@app.route("/api/locations")
def get_locations():
    alerts = load_alerts()
    ip_counts = Counter(a["src_ip"] for a in alerts if a.get("src_ip"))
    geo_data = []
    try:
        reader = geoip2.database.Reader(GEO_DB)
        for ip, count in ip_counts.items():
            try:
                response = reader.city(ip)
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
    return jsonify(geo_data)

@app.route("/")
def index():
    return "NeuralNIDS API Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
