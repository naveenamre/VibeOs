from flask import Flask, request, jsonify
from solver import solve_schedule  # <-- Ye line zaroori hai

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"mode": "God Mode", "status": "VibeOS Brain is Active"})

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    try:
        # Asli Logic Call
        result = solve_schedule(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)