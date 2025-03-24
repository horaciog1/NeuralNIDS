import os
import dpkt
import socket
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
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

def preprocess_data(df):
    # encoding labels and scaling numerical features.
    # Non-numeric columns like session_id are dropped, but relevant categorical features are encoded.
    # Drop columns that are irrelevant
    if 'session_id' in df.columns:
        df = df.drop(columns=['session_id'])

    # If dataset has 'attack_detected" and 'label' column
    if 'attack_detected' in df.columns:
        target_column = 'attack_detected'
    else:
        target_column = 'label'

    # Identify categorical columns that need to be encoded
    categorical_columns = []
    for col in df.columns:
        if df[col].dtype == object and col != target_column:  # Exclude the target label if already encoded later
            categorical_columns.append(col)

    # Encode categorical features using one-hot encoding
    df = pd.get_dummies(df, columns=categorical_columns)

    # Encode if necessary
    if df[target_column].dtype == object:
        encoder = LabelEncoder()
        df[target_column] = encoder.fit_transform(df[target_column])

    # Separate features and target variable
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Scale numerical features
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y


def train_model(X, y):
    # Split the dataset
    # train a Random Forest classifier
    # evaluate its performance.

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Apply SMOTE to the training data
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print("After SMOTE, counts of label '0' and '1':",
            dict(pd.Series(y_train_res).value_counts()))

    # Train the model using resampled data
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_res, y_train_res)

    # Evaluate the model on the test set
    y_pred = model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("Classification Report:\n", classification_report(y_test, y_pred))

    # Display the confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix")
    plt.show()

    return model


def main():
    # Specify your data file path. This can be either a PCAP or CSV file.
    file_path = '/Users/christian/PycharmProjects/NeuralNIDS/Datasets/cybersecurity_intrusion_data.csv'  # e.g., 'data/network_traffic.pcap' or 'data/dataset.csv'
    label = "normal"  # or "attack" if applicable

    model_path = 'data/trained_model.joblib'
    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    if os.path.exists(model_path):
        print("Loading existing model...")
        model = load(model_path)
        print("Model loaded successfully.")
    else:
        print("No saved model found. Training a new model...")
        df = load_data(file_path, label)
        print("Extracted Data:")
        print(df.head())
        X, y = preprocess_data(df)
        model = train_model(X, y)
        dump(model, model_path)
        print(f"Model saved to '{model_path}'")

if __name__ == "__main__":
    main()
