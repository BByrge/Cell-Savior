from flask import Flask, redirect, request, jsonify, render_template
import requests

app = Flask(__name__)

BACKEND_API_BASE_URL = "http://localhost:8080/api"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET'])
def login():
    # Call the backend to initiate OAuth
    response = requests.get(f"{BACKEND_API_BASE_URL}/auth/initiate")
    if response.status_code == 200:
        data = response.json()
        return redirect(data["url"])
    return "Failed to initiate OAuth", 500

@app.route('/auth/callback', methods=['GET'])
def oauth_callback():
    # Receive the authorization code and state from Google
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return "Missing authorization code or state", 400

    # Send code and state to backend for token exchange
    payload = {"code": code, "state": state}
    response = requests.post(f"{BACKEND_API_BASE_URL}/auth/callback", json=payload)
    if response.status_code == 200:
        tokens = response.json()
        # Display the returned JWT
        return render_template("jwt_display.html", jwt=tokens.get("user_jwt"))
    return "OAuth callback failed", 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
