'''
API for Cellular Savior. This file only contains the API routes.
Functions/ROUTES: home, index, auth_initiate, oauth_callback, get_user, get_public_key, get_plans, recommend, get_plan, create_plan, delete_plan, patch_plan
Exceptions: ERROR_400, ERROR_401, ERROR_403, ERROR_404
'''

from flask import request, jsonify
from __init__ import create_app
from google.cloud import datastore
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from security import auth_decorators
import requests, utils


app = create_app()

GOOGLE_AUTH_CLIENT_ID = app.config['GOOGLE_AUTH_CLIENT_ID']
GOOGLE_AUTH_CLIENT_SECRET = app.config['GOOGLE_AUTH_CLIENT_SECRET']
GOOGLE_AUTH_REDIRECT_URI = app.config['GOOGLE_AUTH_REDIRECT_URIS'][0]
GOOGLE_AUTH_SCOPE = app.config['GOOGLE_AUTH_SCOPE']

ERROR_400 = {"Error": "The request body is invalid"}
ERROR_401 = {"Error": "Unauthorized"}
ERROR_403 = {"Error": "You don't have permission on this resource"}
ERROR_404 = {"Error": "Not found"}

SELF_URL = 'https://api.cellularsavior.com/'

client = datastore.Client()


@app.route('/', methods=['GET'])
def index():
    '''
    Root for the api. API documentation.
    '''
    return 'API Documentation will be here. /api/auth/key for public key.', 200


# Authentication routes
@app.route('/auth/initiate', methods=['GET'])
def auth_initiate():
    '''
    Returns the URL for the user to authenticate with Google. This url contains the client_id, redirect_uri, scope, and state.
    Client is responsible for the redirection to the URL.
    State is a random string that is used to prevent CSRF attacks.
    Returns:
        dict: url, state
    '''
    state = utils.generate_state()
    # Store state in datastore with an expiration date. Check state in callback route.
    entity = datastore.Entity(client.key('state'))
    entity['state'] = state
    entity['expiration'] = utils.get_expiration()
    client.put(entity)

    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?response_type=code&client_id={GOOGLE_AUTH_CLIENT_ID}&redirect_uri={GOOGLE_AUTH_REDIRECT_URI}"
        f"&scope={GOOGLE_AUTH_SCOPE}&state={state}&prompt=consent&include_granted_scopes=true"
    )
    return jsonify({"url": url, 'state': state}), 200

@app.route('/auth/callback', methods=['POST'])
def oauth_callback():
    '''
    Callback route for OAuth2.0. This route exchanges the code for tokens and verifies the ID token.
    This route is called by the client after the user has authenticated with Google.
    Request Body: code, state
    Returns:
        dict: id_token, user_jwt, user_info
    '''
    code = request.json.get("code")
    state = request.json.get("state")
    if not code or not state:
        return ERROR_400, 400

    # Verify state to prevent CSRF attacks
    # Check if state exists in datastore and is not expired
    query = client.query(kind='state')
    query.add_filter(filter=datastore.query.PropertyFilter('state', '=', state))
    results = list(query.fetch())
    if not results:
        print('State not found')
        return ERROR_403, 403
    elif not utils.get_expiration(results[0]['expiration']):
        print('State expired')
        # Delete the state from the datastore
        client.delete(results[0].key)
        return ERROR_403, 403

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
        print('No id token')
        return ERROR_400, 400

    # Verify the ID token
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token, google_requests.Request(), GOOGLE_AUTH_CLIENT_ID
        )
    except ValueError:
        return jsonify({"error": "Invalid ID token"}), 400

    # Generate a custom JWT for client to manage user sessions and provide authorization.
    # A new user will be created in generate_custom_jwt if the user does not exist.
    user_jwt = utils.generate_custom_jwt(id_info)
    if user_jwt == 0:
        return ERROR_400, 400

    return jsonify({"id_token": id_token, "user_jwt": user_jwt, "user_info": id_info})  

@app.route('/auth/key', methods=['GET'])
def get_public_key():
    '''
    Get the public key for verifying JWTs.
    Returns:
        dict: key
    '''
    public_key = app.config['PUBLIC_KEY']
    return {"key": public_key}, 200

@app.route('/auth/verifyjwt', methods=['POST'])
def verify_jwt():
    '''
    Verify a JWT token.
    Request Body: token
    Returns:
        boolean
    '''
    token = request.json.get("token")
    if not token:
        return ERROR_400, 400

    valid = utils.verify_JWT(token)
    if valid == 0:
        return ERROR_401, 401
    return {"valid": valid}, 200

# User routes
@app.route('/plans', methods=['GET'])
def get_plans():
    '''
    Get all the plans from the database.
    Client should use this router to get all the plans.
    Returns:
        list: plans
    '''
    query = client.query(kind='plans')
    results = list(query.fetch())
    # We only add the id if the user is an admin
    for i in results:
        i['id'] = i.id
        i['self'] = f'{SELF_URL}plans/{i.id}'

    return results, 200

@app.route('/recommend', methods=['POST'])
def recommend():
    '''
    Get a plan recommendation.
    This function will return a list of plans that match or beat: data, hotspot, talk, and text.
    The list will filter out plans that are not provided by the carriers in the carriers list.
    Request Body:
                lines: int (required)   
                data: int (optional)
                hotspot: int (optional)
                talk: int (optional)
                text: int (optional)
                price: float (optional)
                financing_status: bool (optional)
                carriers: list (optional)

    Returns:
        list: plans
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
        return {'results': results}, 200
    
    query = client.query(kind='plans')
    if 'data' in provided_fields:
        query.add_filter('data', '>=', int(data['data']))

    if 'hotspot' in provided_fields:
        query.add_filter('hotspot', '>=', int(data['hotspot']))

    if 'talk' in provided_fields:
        query.add_filter('talk', '>=', int(data['talk']))

    if 'text' in provided_fields:
        query.add_filter('text', '>=', int(data['text']))
    results = list(query.fetch())

    # Filter out plans that are not provided by the carriers in the carriers list.
    if 'carriers' in provided_fields:
        for i in results:
            if i['carrier'] not in data['carriers']:
                results.remove(i)

    # Filter plans that don't have the desired line number. 
    # This need to be done after the DB query because of the way we stored price.
    results = [plan for plan in results if str(data['lines']) in plan['price']]

    for i in results:
        i['id'] = i.id
        i['self'] = f'{SELF_URL}plans/{i.id}'
    return {'results': results}, 200

@app.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    '''
    Get a plan by ID.
    Arguments:
        plan_id: int
    Returns:
        plan
    '''
    if not plan_id:
        return ERROR_400, 400
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    
    return plan, 200


# Admin only routes.
@app.route('/plans', methods=['POST'])
@auth_decorators.admin_required
def create_plan():
    '''
    Add a plan to the database.
    Plan: name, data, hotspot, talk, text, price, carrier, description, payoff
    Request Body:
            name: str (required)
            data: int (required)
            hotspot: int (required)
            talk: int (required)
            text: int (required)
            price: dict {lines: string, amount: string} (required)
            carrier: str (required)
            networks: list (required)
            description: str (required)
            payoff: bool (required)
            url: str (required)
    Returns:
        plan
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
    # Later verify the data
    new_plan = datastore.Entity(client.key('plans'))
    # Add date added to the plan
    data['date_added'] = utils.get_date_time()
    new_plan.update(data)
    client.put(new_plan)
    new_plan['id'] = new_plan.id
    new_plan['self'] = f'{SELF_URL}plans/{new_plan['id']}'
    print(new_plan)
    return new_plan, 201

@app.route('/plans/<plan_id>', methods = ['DELETE'])
@auth_decorators.admin_required
def delete_plan(plan_id):
    '''
    Delete a plan from the database. 
    Arguments: 
            plan_id
    '''
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    client.delete(plan)
    return '', 204

@app.route('/plans/<plan_id>', methods=['PATCH'])
@auth_decorators.admin_required
def patch_plan(plan_id):
    '''
    Patch plan in database.
    Arguments: 
            plan_id
    Return:
        plan
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
