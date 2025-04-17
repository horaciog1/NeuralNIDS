import os
import struct
import dpkt
import socket
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, roc_curve, auc

from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from xgboost import plot_importance
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from joblib import dump, load
from imblearn.over_sampling import SMOTE

def parse_pcap(file_path, label):
    # Parse a PCAP file and extract basic features for each packet.

    records = []
    with open(file_path, 'rb') as f:
        pcap = dpkt.pcap.Reader(f)
        for ts, buf in pcap:
            try:
                eth = dpkt.ethernet.Ethernet(buf)
                # Process only IP packets
                if not isinstance(eth.data, dpkt.ip.IP):
                    continue
                ip = eth.data

                # Extract source and destination IPs
                src_ip = socket.inet_ntoa(ip.src)
                dst_ip = socket.inet_ntoa(ip.dst)

                # Basic features: timestamp, protocol, packet length
                protocol = ip.p
                pkt_len = ip.len

                # More features (TCP flags, ports, etc.)
                records.append({
                    'timestamp': ts,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'protocol': protocol,
                    'pkt_len': pkt_len,
                    'label': label
                })
            except Exception as e:
                # Skip malformed packets
                continue
    return pd.DataFrame(records)


def load_data(file_path, label=None):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
        # Only add the forced label if no target column exists.
        # Need to research if dynamic label detection is possible
        # for various attack types rather than hard coding column labels
        if 'attack_detected' not in df.columns and 'label' not in df.columns and label is not None:
            df['label'] = label
    elif ext in ['.pcap', '.pcapng']:
        if label is None:
            raise ValueError("For PCAP files, please provide a label.")
        df = parse_pcap(file_path, label)
    else:
        raise ValueError("Unsupported file type: " + ext)
    return df


def encode_categorical_features(df, categorical_columns):
    # Encodes specific categroical columns using one-hot encoding

    return pd.get_dummies(df, columns=categorical_columns)


def preprocess_data(df, selected_features_file=None, for_training=True):
    import struct
    import socket
    from sklearn.preprocessing import LabelEncoder, StandardScaler

    def ip_to_int(ip_str):
        try:
            return struct.unpack("!I", socket.inet_aton(ip_str))[0]
        except:
            return 0

    # Identify target column
    target_column = 'attack_detected' if 'attack_detected' in df.columns else 'label'

    # Drop irrelevant columns
    drop_cols = ['session_id', 'timestamp', 'Unnamed: 47', 'attack_cat']
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Convert IP columns to ints
    ip_cols = ['src_ip', 'dst_ip']
    for col in ip_cols:
        if col in df.columns:
            df[col] = df[col].apply(ip_to_int)

    # Force one-hot encoding for important categorical features
    force_encode = ['proto']
    for col in df.columns:
        if col in force_encode and col in df.columns:
            print(f"[+] One-hot encoding important feature: {col}")
            df = pd.get_dummies(df, columns=[col])

    # Encode all other safe categorical features
    for col in df.columns:
        if df[col].dtype == object and col not in force_encode:
            if for_training and col == target_column:
                continue
            if df[col].nunique() > 20:
                print(f"[!] Dropping high-cardinality column: {col}")
                df = df.drop(columns=[col])
            else:
                print(f"[+] One-hot encoding safe column: {col}")
                df = pd.get_dummies(df, columns=[col])

    # Encode label (only during training)
    if for_training and target_column in df.columns and df[target_column].dtype == object:
        encoder = LabelEncoder()
        df[target_column] = encoder.fit_transform(df[target_column])

    # Separate X and y
    if for_training and target_column in df.columns:
        y = df[target_column]
        X = df.drop(columns=[target_column])
    else:
        X = df
        y = None

    # Ensure numeric only
    X = X.select_dtypes(include=['int64', 'float64'])

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)

    # Optional: Select only top features
    if selected_features_file:
        with open(selected_features_file, 'r') as f:
            top_features = [line.strip() for line in f.readlines()]
        missing = [feat for feat in top_features if feat not in X_scaled_df.columns]
        if missing:
            print(f"[!] Warning: Missing features from selection: {missing}")
        X_scaled_df = X_scaled_df[[f for f in top_features if f in X_scaled_df.columns]]
        print(f"[+] Using top {len(X_scaled_df.columns)} features.")

    print(f"[+] Preprocessing complete. Features shape: {X_scaled_df.shape}")
    return X_scaled_df, y, list(X_scaled_df.columns)




def train_model(X, y, X_val=None, y_val=None):

    # Apply SMOTE to the training data
    print("Applying SMOTE to rebalance classes...")
    smote = SMOTE(random_state=42)
    X, y = smote.fit_resample(X, y)

    print("Label distribution after SMOTE:")
    print(pd.Series(y).value_counts())

    # Train the model using resampled data
    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        #booster='gbtree',
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )

    # model = RandomForestClassifier(n_estimators=100, random_state=42)
    # model.fit(X_train_res, y_train_res)

    if X_val is not None and y_val is not None:
        model.fit(
            X, y,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=10,
            verbose=True
        )
    else:
        model.fit(X, y)

        return model

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.show()

    # ROC Curve
    if hasattr(model, "predict_proba"):
        y_probs = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_probs)
        roc_auc = auc(fpr, tpr)
        plt.figure(figsize=(6, 4))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC Curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate (Recall)")
        plt.title("Receiver Operating Characteristic (ROC) Curve")
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.show()

    # Feature Importance (Random Forest or others)
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:15]
        plt.figure(figsize=(8, 5))
        feature_labels = [X_test.columns[i] for i in indices]
        plt.bar(range(len(indices)), importances[indices])
        plt.title("Top 15 Feature Importances")
        plt.xlabel("Feature Index")
        plt.ylabel("Importance")
        plt.tight_layout()
        plt.show()

def check_feature_alignment(X_test, test_features, train_features):
    print("\n[+] Checking feature alignment...")

    if list(test_features) != list(train_features):
        print("Feature misalignment detected!")
        train_only = set(train_features) - set(test_features)
        test_only = set(test_features) - set(train_features)

        if train_only:
            print(f"→ Features in training but missing in test: {sorted(train_only)}")
        if test_only:
            print(f"→ Features in test but missing in training: {sorted(test_only)}")

            # Auto-align to only the common features
            common = sorted(set(train_features) & set(test_features))
            return X_test[common], common

    print("Features are aligned correctly.")
    return X_test, test_features


def engineer_features(df):
    print("[+] Engineering new features...")

    # Convert IP addresses if present
    ip_cols = ['src_ip', 'dst_ip']
    for col in ip_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: struct.unpack("!I", socket.inet_aton(x))[0] if isinstance(x, str) else 0)

    # Add protocol_category if 'proto' exists
    if 'proto' in df.columns:
        df['protocol_category'] = df['proto'].map({
            'tcp': 1,
            'udp': 2,
            'icmp': 3
        }).fillna(0)

    # Add byte_ratio if 'sbytes' and 'dbytes' exist
    if 'sbytes' in df.columns and 'dbytes' in df.columns:
        df['byte_ratio'] = df.apply(
            lambda row: row['sbytes'] / (row['dbytes'] + 1e-5), axis=1
        )

    # Add packet_ratio if 'spkts' and 'dpkts' exist
    if 'spkts' in df.columns and 'dpkts' in df.columns:
        df['packet_ratio'] = df.apply(
            lambda row: row['spkts'] / (row['dpkts'] + 1e-5), axis=1
        )

    # Add total_pkts
    if 'spkts' in df.columns and 'dpkts' in df.columns:
        df['total_pkts'] = df['spkts'] + df['dpkts']

    # Add flags_combined if 'state' exists
    if 'state' in df.columns:
        df['flags_combined'] = df['state'].astype(str).apply(lambda x: sum([ord(c) for c in x]))

    return df

