from flask import Flask, request, render_template, redirect
import json, random, string, requests
from google.cloud import datastore

app = Flask(__name__, template_folder="templates")
app.secret_key = 'SECRET_KEY'
db = datastore.Client()

with open("client_secret.json") as f:
    client_secret = json.load(f)
CLIENT_ID = client_secret['web']['client_id']
CLIENT_SECRET = client_secret['web']['client_secret']
REDIRECT_URI = client_secret['web']['redirect_uris'][0]
SCOPE = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"

class Connection:

    def __init__(self, client_id, redirect_uri, scope) -> None:
        self.state = self.generate_state()
        # store state in datastore
        self.url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}&state={self.state}&prompt=consent&include_granted_scopes=true"

    def generate_state(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    def get_state(self):
        return self.state

@app.route("/")
def index():
    return render_template("index.html", url="/oauth")

@app.route("/oauth")
def oauth():
    if not request.args.get("code"):
        connection = Connection(CLIENT_ID, REDIRECT_URI, SCOPE)
        state_key = db.key("state")
        state = datastore.Entity(key=state_key)
        state.update({"state": connection.get_state()})
        db.put(state)
        return redirect(connection.url)
    code = request.args.get("code")
    request_state = request.args.get("state")
    # Retrieve state from datastore
    query = db.query(kind="state")
    results = list(query.fetch())
    for result in results:
        print(result['state'])
        if result['state'] == request_state:
            state = result['state']
            break
    if request_state != state:
        return "Invalid state", 400

    url = "https://oauth2.googleapis.com/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, headers=headers, data=data)
    response_data = response.json()
    access_token = response_data.get("access_token")

    if not access_token:
        return "Failed to retrieve access token", 400
    # Send post request to google api with access code
    url = "https://www.googleapis.com/oauth2/v1/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    user_info = response.json()
    print('\n')
    print(user_info)
    print('\n')
    given_name = user_info.get("given_name")
    family_name = user_info.get("family_name")

    return render_template("personal_info.html", given_name=given_name, family_name=family_name, state=state)

if __name__ == "__main__":
    app.run(debug=True, port=8080)
