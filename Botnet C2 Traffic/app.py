from flask import Flask, jsonify, render_template, request
from simulator import TrafficSimulator

app = Flask(__name__)

# 🔥 Initialize Simulator
simulator = TrafficSimulator(
    model_path="model/ensemble_c2_detector.h5",
    data_path="data/real_dataset.csv"
)

# -------------------------------
# Routes
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/detect")
def detect():
    return render_template("detect.html")

# -------------------------------
# API ROUTES
# -------------------------------

# 🔴 Live traffic
@app.route("/api/flows")
def flows():
    return jsonify(simulator.get_next_flow())

# 📜 Logs
@app.route("/api/logs")
def logs():
    return jsonify(simulator.get_logs())

# 🚫 Blocked IPs
@app.route("/api/blocked-ips")
def blocked_ips():
    return jsonify(simulator.get_blocked_ips())

# � Block IP (Manual)
@app.route("/api/block-ip", methods=["POST"])
def block_ip():
    try:
        data = request.get_json()
        ip = data.get("ip")
        reason = data.get("reason", "Manual block")
        
        if not ip:
            return jsonify({"status": "error", "message": "IP address is required"}), 400
        
        # Add IP to blacklist
        simulator.blacklist.add(ip)
        
        # Log the manual block
        simulator._log_attack(ip, "99.99")  # Manual block gets max risk score
        
        return jsonify({"status": "success", "message": f"IP {ip} blocked successfully", "ip": ip}), 200
    except Exception as e:
        print(f"Error blocking IP: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to block IP: {str(e)}"}), 500

# �📊 Dashboard Stats (FIXED)
@app.route("/api/stats")
def stats():
    logs = simulator.get_logs()

    if not logs:
        return jsonify({
            "total": 0,
            "malicious": 0,
            "benign": 0,
            "avg_risk": 0
        })

    total = len(logs)
    malicious = sum(1 for log in logs if log["status"] == "BLOCKED")
    benign = total - malicious
    avg_risk = round(sum(log["risk"] for log in logs) / total, 2)

    return jsonify({
        "total": total,
        "malicious": malicious,
        "benign": benign,
        "avg_risk": avg_risk
    })

# -------------------------------
# Run App
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)