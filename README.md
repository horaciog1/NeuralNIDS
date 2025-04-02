# 🧠 NeuralNIDS – Intelligent Network Intrusion Detection System

**NeuralNIDS** is an AI-enhanced, machine learning-driven Network Intrusion Detection System (NIDS) developed by three students from New Mexico State University. Built for real-world cybersecurity challenges, NeuralNIDS intelligently detects, classifies, and responds to malicious network activity while providing real-time visibility and alerting through a sleek web-based dashboard.

By integrating adaptive ML techniques with traditional IDS logs (e.g., Suricata), NeuralNIDS overcomes the limitations of signature-based detection, such as high false positives and inability to detect zero-day threats.

---

## 👨‍💻 Team Members

- **Horacio Gonzalez** – Offensive Security, Feature Engineering, Network Simulations 
- **Christian Garcia Rivero** – Machine Learning, Pipeline Architecture, Data Handling 
- **Jacob Yanez** – Backend Integration, Dashboard Development, System Design

---

## 🚀 Project Vision

NeuralNIDS was created to provide a scalable, intelligent alternative to conventional IDS solutions. With machine learning at its core, NeuralNIDS evolves continuously by learning from real-world attack patterns and traffic behavior, adapting to emerging threats without relying on static rule updates.

---

## 🔍 Key Features

- ✅ **ML-Based Threat Detection** – Trained ensemble models (Random Forest, XGBoost) with SMOTE balancing.
- 🌐 **Interactive Dashboard** – View alerts, threat statistics, protocol distribution, and live GeoIP heatmaps.
- 🔔 **Real-Time Alerting** – Audio, visual, and email notifications for critical events.
- 🧩 **Modular Integration** – Compatible with Snort, Suricata, and ELK Stack for plug-and-play deployment.
- 📊 **Alert Management** – Exportable CSV logs and role-based access.
- 🌍 **GeoIP Mapping** – Maps attacker IPs with coordinates and hit frequency.

---

## 🧠 Machine Learning Pipeline

- **Dataset**: Trained on UNSW-NB15 – includes fuzzers, DoS, exploits, shellcode, and more.
- **Preprocessing**: Uses XGBoost feature importance, SMOTE (only on training) to handle class imbalance.
- **Architecture**: Modular pipeline with separate stages for training, testing, tuning, and deployment.
- **Performance**: Post-leakage fix baseline at ~51% accuracy — realistic for imbalanced datasets; future tuning ongoing.

---

## 🏗️ System Architecture

1. **Traffic Capture** – Suricata collects logs (`eve.json`)
2. **Log Parsing & Processing** – Flask API parses alerts and maps locations
3. **ML Classification** – Trained models classify malicious patterns from structured traffic
4. **Dashboard Visualization** – JS frontend shows active alerts, protocol stats, and IP maps
5. **Alerting** – Triggered via sound, visual cues, and email through Flask-Mail
6. **Data Storage** – Alerts saved in memory and exported upon request (CSV)

---

## 🛠️ Tech Stack

| Component         | Technology Used                                   |
|------------------|---------------------------------------------------|
| **ML Engine**     | Python, scikit-learn, XGBoost, SMOTE              |
| **Log Parser**    | Suricata, dpkt, Pandas                            |
| **Backend API**   | Flask, Flask-Mail, dotenv                         |
| **Frontend UI**   | HTML, CSS, Chart.js, Leaflet.js, JS               |
| **Deployment**    | Proxmox, Ubuntu, Docker-ready                     |
| **GeoIP Mapping** | MaxMind GeoLite2 City DB, geoip2                  |

---

## 📦 File Structure (Simplified)
NeuralNIDS/ ├── app.py # Flask backend + API ├── main.py # ML training pipeline ├── static/ │ ├── index.html # Dashboard UI │ ├── all_alerts.html # Full alert log viewer │ ├── styles.css # Dashboard styling │ ├── index.js # Main JS logic │ ├── all_alerts.js # Alert viewer JS │ ├── notification.js # Audio/visual alert trigger │ └── alert.mp3 # Notification sound └── .env # Email credentials (not committed)



---

## 📊 Metrics for Success

- **Detection Accuracy**: ≥ 95% on known attack datasets
- **False Positive Rate**: < 5%
- **Response Time**: < 1 second for alert delivery
- **Usability**: Confirmed via feedback from target user interviews

---

## 🎯 Goals & Milestones

| Weeks     | Goal                                             |
|-----------|--------------------------------------------------|
| 1–3       | Proposal Finalization, Dataset Research          |
| 4–6       | Requirements Specification, Environment Setup    |
| 7–10      | IDS Integration, Model Training & Evaluation     |
| 11–12     | Simulated Traffic Testing, Alert Pipeline        |
| 13–14     | Dashboard UI & Full Stack Integration            |
| 15        | Final Testing, Evaluation, and Documentation     |

---

## 🔒 Security & Compliance

- GDPR, SOC 2, and NIST-aligned design principles
- Logs stored encrypted, role-based access control implemented
- Email alerts only sent to verified addresses from `.env`

---

## 🧪 Known Challenges

- Imbalanced data can inflate metrics (false positives/negatives)
- GeoIP limitations on local/internal networks
- Performance tuning for real-world traffic load is ongoing

---

## 💡 Use Cases

- 📡 SOC Teams (enterprise/government)
- 🏫 Educational Labs & Blue Team Simulations
- 🧪 Penetration Testers monitoring live labs
- 🏠 Home users interested in learning NIDS & ML

---

## 📬 Getting Started

### 🔧 Requirements

- Python 3.8+
- Suricata (with EVE JSON enabled)
- GeoLite2-City.mmdb (placed in correct path)
- Valid SMTP credentials for email alerts

### 🛠️ Setup

```bash
git clone https://github.com/yourusername/neuralnids.git
cd neuralnids
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Add your .env:
```ini
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_password
EMAIL_RECIPIENTS=someone@example.com
```

Start the backend:
```bash
python app.py
```

Visit http://localhost:5000

To train a new model from PCAP/CSV:
```bash
python main.py
```

## 🙏 Acknowledgments

Special thanks to:
- **Dr. Gaurav Panwar** – Cybersecurity Professor, NMSU
- **Dr. Bill Hamilton** – Professor, NMSU
- **Eugene Hanway** – Mentor, Knack Works Inc.

---

## 📎 License

MIT License – see [LICENSE](LICENSE) for details.

---

## 📬 Contact

For questions or contributions, feel free to reach out:
- Horacio Gonzalez – @horaciog1
- Christian Garcia Rivero – @chrisgarcia
- Jacob Yanez – @jacobyanez
