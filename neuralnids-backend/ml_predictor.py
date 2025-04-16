import json
import pandas as pd
from joblib import load
from utils import preprocess_data, engineer_features
import os

# --- CONFIG ---
MODEL_PATH = "models/ensemble_stacking_model.joblib"
FEATURES_PATH = "models/top25_features.txt"
THRESHOLD_PATH = "logs/optimal_threshold_stacking.txt"

def load_sample_event(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return pd.DataFrame([data])

def load_threshold():
    if os.path.exists(THRESHOLD_PATH):
        with open(THRESHOLD_PATH, "r") as f:
            return float(f.read().strip())
    return 0.5

def drop_unhashable_columns(df):
    unhashable_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, dict)).any()]
    if unhashable_cols:
        print(f"[X] Dropping nested columns: {unhashable_cols}")
        df = df.drop(columns=unhashable_cols)
    return df

def predict_event(input_data):
    try:
        # Ensure input is a DataFrame
        if isinstance(input_data, dict):
            df = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            df = input_data.copy()
        else:
            raise ValueError("Input must be a dictionary or DataFrame")

        # Drop unhashable/nested columns
        unhashable_cols = [col for col in df.columns if df[col].apply(lambda x: isinstance(x, dict)).any()]
        if unhashable_cols:
            print(f"[!] Dropping nested columns: {unhashable_cols}")
            df = df.drop(columns=unhashable_cols)

        print("[+] Engineering new features...")
        df = engineer_features(df)

        print("[+] Preprocessing features...")
        X, _, _ = preprocess_data(df, selected_features_file=FEATURES_PATH)

        # Keep only numeric columns (this avoids JSON/IP/etc errors)
        X = X.select_dtypes(include=["number"])

        if X.shape[1] == 0:
            raise ValueError("No usable features found after preprocessing. Ensure the input matches the expected top25 features.")

        print("[+] Loading model and threshold...")
        model = load(MODEL_PATH)
        threshold = load_threshold()

        print("[+] Making prediction...")
        prob = model.predict_proba(X)[0][1]
        prediction = int(prob >= threshold)

        return {
            "Probability": round(prob, 4),
            "Threshold": threshold,
            "Prediction": prediction,
            "Label": "ATTACK" if prediction == 1 else "NORMAL"
        }

    except Exception as e:
        print(f"[X] ML Prediction error: {e}")
        return {
            "Prediction": -1,
            "Confidence": 0.0,
            "Label": "Error",
            "Error": str(e)
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python ml_predictor.py <json_file>")
        exit(1)

    json_file = sys.argv[1]
    df = load_sample_event(json_file)
    result = predict_event(df)
    print("\n[+] Prediction Result:")
    for k, v in result.items():
        print(f"{k.capitalize()}: {v}")
