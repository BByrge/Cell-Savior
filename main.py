from flask import request, jsonify
from __init__ import create_app
from google.cloud import datastore
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from security import auth_decorators
import requests, json, jwt, utils, datetime


app = create_app()

GOOGLE_AUTH_CLIENT_ID = app.config['GOOGLE_AUTH_CLIENT_ID']
GOOGLE_AUTH_CLIENT_SECRET = app.config['GOOGLE_AUTH_CLIENT_SECRET']
GOOGLE_AUTH_REDIRECT_URI = app.config['GOOGLE_AUTH_REDIRECT_URIS'][0]
GOOGLE_AUTH_SCOPE = app.config['GOOGLE_AUTH_SCOPE']

ERROR_400 = {"Error": "The request body is invalid"}
ERROR_401 = {"Error": "Unauthorized"}
ERROR_403 = {"Error": "You don't have permission on this resource"}
ERROR_404 = {"Error": "Not found"}

# SELF_URL = 'https://cellularsavior-442cf.uc.r.appspot.com/api/'
SELF_URL = 'http://127.0.0.1:8080/api/'

client = datastore.Client()

@app.route('/api', methods=['GET'])
def index():
    '''
    Home route. API documentation.
    '''
    return 'API Documentation will be here'

@app.route('/api/auth/initiate', methods=['GET'])
def auth_initiate():
    '''
    OAuth2.0 Authentication with google. Callback URL is /api/auth/callback.
    '''
    state = utils.generate_state()
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={GOOGLE_AUTH_CLIENT_ID}&redirect_uri={GOOGLE_AUTH_REDIRECT_URI}"
        f"&scope={GOOGLE_AUTH_SCOPE}&state={state}&prompt=consent&include_granted_scopes=true"
    )
    return jsonify({"url": url, 'state': state}), 200

@app.route('/api/auth/callback', methods=['POST'])
def oauth_callback():
    code = request.json.get("code")

    # Do we need to check the state?
    state = request.json.get("state")

    if not code or not state:
        return ERROR_400, 400

    # Exchange code for tokens
    url = "https://oauth2.googleapis.com/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "code": code,
        "client_id": GOOGLE_AUTH_CLIENT_ID,
        "client_secret": GOOGLE_AUTH_CLIENT_SECRET,
        "redirect_uri": GOOGLE_AUTH_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(url, headers=headers, data=data)
    tokens = response.json()

    # id_token is the JWT that can be used to authenticate the user
    id_token = tokens.get("id_token")
    if not id_token:
        return ERROR_400, 400

    # Verify the ID token
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token, google_requests.Request(), GOOGLE_AUTH_CLIENT_ID
        )
    except ValueError:
        return jsonify({"error": "Invalid ID token"}), 400

    # Generate a custom JWT for client to manage user sessions and provide authorization
    user_jwt = generate_custom_jwt(id_info)

    return jsonify({"id_token": id_token, "user_jwt": user_jwt, "user_info": id_info})

def generate_custom_jwt(id_info):

    # ***** this needs to be changed and managed properly *****
    SECRET_KEY = app.config['SECRET_KEY']

    # Check if user exists in database
    query = client.query(kind='users')
    query.add_filter(filter=datastore.query.PropertyFilter('sub', '=', id_info["sub"]))
    results = list(query.fetch())

    if not results:
        # Create user with role user
        user = utils.create_user(id_info)
        if user == 0:
            return ERROR_400, 400
        # Role is set to user by default. Changing this requires manual admin action.
        roles = ["user"]
    elif len(results) > 1:
        return {"Error": "Duplicate user in database"}, 500
    elif 'roles' not in results[0]:
        roles = ["user"]
    else:
        roles = results[0]['roles']

    # Refresh token will be added later
    payload = {
        "sub": id_info["sub"],
        "email": id_info["email"],
        "name": id_info["name"],
        "roles": roles,
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm="RS256")

# User routes
@app.route('/api/plans', methods=['GET'])
def get_plans():
    '''
    Get all the plans from the database. Use for browsing.
    ID is only included if the user is an admin.
    '''
    query = client.query(kind='plans')
    results = list(query.fetch())
    # We only add the id if the user is an admin
    for i in results:
        i['id'] = i.id
        i['self'] = f'{SELF_URL}plans/{i.id}'

    return results, 200

@app.route('/api/recommend', methods=['GET'])
def recommend():
    '''
    Get a plan recommendation.
    Required Fields: lines(int)
    Possible Fields: data(int), talk(int), text(int), price(float), financing_status(bool), carriers[]
    This function will return a list of plans that match or beat: data, hotspot, talk, and text.
    The list will filter out plans that are not provided by the carriers in the carriers list.
    **If financing_status is true, we will do something cool in a future update.
    '''
    data = request.get_json()
    if not data or 'lines' not in data:
        return ERROR_400, 400
    provided_fields = []

    # Get all provided fields. If only lines is provided, return all plans
    for field in data:
        provided_fields.append(field)
    # If only lines is provided, return all plans
    if len(provided_fields) == 1:
        query = client.query(kind='plans')
        results = list(query.fetch())
        # Not sure if this sorts by keys or values
        return results, 200
    
    query = client.query(kind='plans')
    if 'data' in provided_fields:
        if data['data'] == -1:
            query.add_filter(filter=datastore.query.PropertyFilter('data', '=', -1))
        else:
            query.add_filter(filter=datastore.query.PropertyFilter('data', '>=', data['data']))

    if 'hotspot' in provided_fields:
        if data['hotspot'] == -1:
            query.add_filter(filter=datastore.query.PropertyFilter('hotspot', '=', -1))
        else:
            query.add_filter(filter=datastore.query.PropertyFilter('hotspot', '>=', data['hotspot']))

    if 'talk' in provided_fields:
        if data['talk'] == -1:
            query.add_filter(filter=datastore.query.PropertyFilter('talk', '=', -1))
        else:
            data['talk'] = data['talk']
            query.add_filter(filter=datastore.query.PropertyFilter('talk', '>=', data['talk']))

    if 'text' in provided_fields:
        if data['text'] == -1:
            query.add_filter(filter=datastore.query.PropertyFilter('text', '=', -1))
        else:
            data['text'] = data['text']
            query.add_filter(filter=datastore.query.PropertyFilter('text', '>=', data['text']))

    results = list(query.fetch())

    # Filter out plans that are not provided by the carriers in the carriers list.
    if 'carriers' in provided_fields:
        for i in results:
            if i['carrier'] not in data['carriers']:
                results.remove(i)

    return results, 200

@app.route('/api/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    '''
    Get a plan by ID.
    '''
    if not plan_id:
        return ERROR_400, 400
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    
    return plan, 200


# Admin only routes.
@app.route('/api/plans', methods=['POST'])
@auth_decorators.admin_required
def create_plan():
    '''
    Add a plan to the database. Unlimited data is represented by -1.
    '''
    data = request.get_json()
    if not data:
        return ERROR_400, 400
    # Check for duplicate plan
    query = client.query(kind='plans')
    query.add_filter(filter=datastore.query.PropertyFilter('name', '=', data['name']))
    results = list(query.fetch())
    if results:
        return {"Error": "A plan with that name already exists"}, 400
    # Later verify the data but fuck that for now
    new_plan = datastore.Entity(client.key('plans'))
    new_plan.update(data)
    client.put(new_plan)
    new_plan['id'] = new_plan.id
    new_plan['self'] = f'{SELF_URL}plans/{new_plan['id']}'
    return new_plan, 201

@app.route('/api/plans/<plan_id>', methods = ['DELETE'])
@auth_decorators.admin_required
def delete_plan(plan_id):
    '''
    Delete a plan from the database.
    '''
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    client.delete(plan)
    return '', 204

@app.route('/api/plans/<plan_id>', methods=['PATCH'])
@auth_decorators.admin_required
def patch_plan(plan_id):
    '''
    Patch plan in database.
    '''
    data = request.get_json()
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    for field in data:
        plan[field] = data[field]
    client.put(plan)
    plan['id'] = plan.id
    plan['self'] = f'{SELF_URL}plans/{plan['id']}'
    return plan, 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
