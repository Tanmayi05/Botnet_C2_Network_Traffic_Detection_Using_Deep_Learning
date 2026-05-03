import pandas as pd
import numpy as np
import random
import os
from datetime import datetime
from tensorflow.keras.models import load_model

class TrafficSimulator:
    def __init__(self, model_path, data_path, benign_mix=0.6):
        print(f"Loading model from: {model_path}")
        self.model = load_model(model_path)

        self.data = pd.read_csv(data_path)
        self.index = 0
        self.benign_mix = benign_mix

        self.attack_logs = []
        self.blacklist = set()

        os.makedirs("logs", exist_ok=True)
        self.log_file = "logs/attack_logs.csv"

        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("time,ip,risk,status\n")   # 🔥 FIXED HEADER

    # 🔥 Generate dynamic IP
    def generate_ip(self):
        return ".".join(str(random.randint(1, 255)) for _ in range(4))

    # 🔥 Prepare model input (150x12)
    def preprocess(self, row):
        values = row.values
        features = np.resize(values, (150, 12))
        return features.reshape(1, 150, 12)

    def get_next_flow(self):
        row = self.data.iloc[self.index]
        self.index = (self.index + 1) % len(self.data)

        # ✅ Dynamic IP
        ip = self.generate_ip()

        # ✅ Mixed traffic: keep some flows benign so the dashboard is not all high-risk.
        if random.random() < self.benign_mix:
            risk_val = np.round(random.uniform(0.05, 0.45), 2)
            risk = f"{risk_val:.2f}"
            status = "BENIGN"
        else:
            # ✅ Model prediction + add variety to malicious traffic
            features = self.preprocess(row)
            prediction = self.model.predict(features, verbose=0)
            pred_val = float(prediction[0][0])
            
            # Create variety: malicious traffic gets range 0.65-0.99
            if pred_val >= 0.65:
                risk_val = np.round(random.uniform(0.65, 0.99), 2)
                risk = f"{risk_val:.2f}"
                status = "BENIGN"

                # 🔥 Auto detect + block for truly suspicious traffic
                if risk_val >= 0.7:
                    status = "BLOCKED"
                    self.blacklist.add(ip)
                    self._log_attack(ip, risk)
            else:
                risk_val = np.round(pred_val, 2)
                risk = f"{risk_val:.2f}"
                status = "BENIGN"

        log = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "ip": ip,   # 🔥 FIXED (IMPORTANT)
            "risk": risk,
            "status": status,
            "blocked": ip in self.blacklist
        }

        self.attack_logs.insert(0, log)
        self.attack_logs = self.attack_logs[:50]

        return log

    def _log_attack(self, ip, risk_str):
        log = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip,   # 🔥 FIXED
            "risk": risk_str,
            "status": "BLOCKED"
        }

        with open(self.log_file, "a") as f:
            f.write(f"{log['time']},{ip},{risk_str},BLOCKED\n")

    def get_logs(self):
        return self.attack_logs

    def get_blocked_ips(self):
        return list(self.blacklist)