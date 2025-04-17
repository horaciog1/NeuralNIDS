import json
import pandas as pd
import time
import os
from ml_predictor import predict_event

EVE_LOG = "/var/log/suricata/eve.json"
ML_ALERT_LOG = "logs/ml_alerts.jsonl"
TOP25_FEATURES_PATH = "models/top25_features.txt"

def load_top_features(path):
    with open(path, "r") as f:
        return [line.strip() for line in f.readlines()]

def map_suricata_to_features(event, top_features):
    flat = {}
    for key, value in event.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                flat[subkey] = subvalue
        else:
            flat[key] = value

    features = {feat: 0 for feat in top_features}
    for feat in top_features:
        if feat in flat:
            features[feat] = flat[feat]

    return pd.DataFrame([features])

def trim_log_file(path, max_lines=10):
    with open(path, "r") as f:
        lines = f.readlines()[-max_lines:]
    with open(path, "w") as f:
        f.writelines(lines)

def tail_eve_and_predict():
    print("[+] Watching eve.json for new alerts with ML integration...")
    top_features = load_top_features(TOP25_FEATURES_PATH)
    seen_flows = set()

    with open(EVE_LOG, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            try:
                event = json.loads(line.strip())
                print(f"[DEBUG] New event received at {time.strftime('%X')}")
                print(f"[DEBUG] Event type: {event.get('event_type')}")

                if event.get("event_type") != "alert":
                    continue

                flow_id = event.get("flow_id")
                if flow_id in seen_flows:
                    continue
                seen_flows.add(flow_id)

                print(f"[ALERT] {event.get('src_ip')} → {event.get('dest_ip')} | {event.get('proto')} | {event.get('alert', {}).get('signature')}")

                print("[+] Mapping Suricata alert to feature vector...")
                df = map_suricata_to_features(event, top_features)
                print("[DEBUG] Feature Vector:", df.to_dict(orient="records")[0])

                print("[+] Sending to ML model for prediction...")
                result = predict_event(df)

                if "Probability" in result and "Label" in result:
                    print(f"[+] ML Prediction: {result['Label']} (Confidence: {result['Probability']})")

                    with open(ML_ALERT_LOG, "a") as log:
                        log.write(json.dumps({
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "label": result["Label"],
                            "confidence": result["Probability"]
                        }) + "\n")

                    trim_log_file(ML_ALERT_LOG, max_lines=10)

                else:
                    print(f"[X] ML Prediction failed: {result.get('Error', 'Unknown error')}")

            except Exception as e:
                print(f"[X] ML Prediction error: {e}")

if __name__ == "__main__":
    tail_eve_and_predict()