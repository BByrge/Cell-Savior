from flask import Flask, request, jsonify, send_file
from google.cloud import datastore

import utils

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

client = datastore.Client()
# SELF_URL = 'https://cellularsavior-442cf.uc.r.appspot.com/'
SELF_URL = 'http://127.0.0.1:8080/'

ERROR_400 = {"Error": "The request body is invalid"}
ERROR_401 = {"Error": "Unauthorized"}
ERROR_403 = {"Error": "You don't have permission on this resource"}
ERROR_404 = {"Error": "Not found"}

@app.route('/', methods=['GET'])
def index():
    return 'API Documentation will be here'

# User and admin routes
@app.route('/plans', methods=['GET'])
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
    return jsonify(results), 200

@app.route('/recommend', methods=['GET'])
def recommend():
    '''
    Get a plan recommendation. Lines is required, all other fields are optional.
    Fields: data(str), talk(str), text(str), price(float), financing_status(bool), carriers[]
    This function will return a list of plans that match or beat: data, hotspot, talk, text, price
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
        return jsonify(results), 200
    
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

    return jsonify(results), 200

# Admin only routes. Auth will be added later.
@app.route('/plans', methods=['POST'])
def create_plan():
    '''
    Add a plan to the database. Unlimited data is represented by -1.
    '''
    data = request.get_json()
    if not data:
        return ERROR_400, 400
    # Check for duplicate plan
    query = client.query(kind='plans')
    query.add_filter('name', '=', data['name'])
    results = list(query.fetch())
    if results:
        return {"Error": "A plan with that name already exists"}, 400
    # Later verify the data but fuck that for now
    new_plan = datastore.Entity(client.key('plans'))
    new_plan.update(data)
    client.put(new_plan)
    new_plan['id'] = new_plan.id
    new_plan['self'] = f'{SELF_URL}plans/{new_plan['id']}'
    return jsonify(new_plan), 201

@app.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    '''
    Get a plan by ID.
    '''
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404, 404
    return jsonify(plan), 200

@app.route('/plans/<plan_id>', methods = ['DELETE'])
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

@app.route('/plans/<plan_id>', methods=['PATCH'])
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
    return jsonify(plan), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
