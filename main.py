from flask import Flask, request, jsonify, send_file
from google.cloud import datastore

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

client = datastore.Client()

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
    # for i in results:
    #     i['id'] = i.id
    return jsonify(results)

@app.route('/recommend', methods=['GET'])
def recommend():
    '''
    Get a plan recommendation.
    '''
    return 'not implemented', 200


# Admin only routes. Auth will be added later.
@app.route('/plans', methods=['POST'])
def create_plan():
    '''
    Add a plan to the database.
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
    print(new_plan['self'])
    return jsonify(new_plan), 201

@app.route('/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    '''
    Get a plan by ID.
    '''
    key = client.key('plans', int(plan_id))
    plan = client.get(key)
    if not plan:
        return ERROR_404
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
    return 204

@app.route('/plans/<plan_id>', methods=['PATCH'])
def patch_plan(plan_id):
    '''
    Patch plan in database.
    '''
    return 'not implemented', 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
