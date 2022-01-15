from flask import Flask, request, jsonify
import jwt
import os
import hashlib
import requests
import sys

app = Flask(__name__)

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

JWT_ALGORITHM = 'HS256'

def _get_jwt_secret():
    jwt_secret_file = open(os.environ['JWT_SECRET'])

    return jwt_secret_file.read().rstrip('\n')


@app.route('/login', methods=['POST'])
def login():
    body = request.get_json(silent=True)

    if not body or 'username' not in body or 'password' not in body:
        return jsonify(), HTTP_BAD_REQUEST

    username = body['username']
    password = body['password']
    password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    params = {'user' : username, 'pass' : password}

    response = requests.post('http://database_manager:8010/auth', params = params)

    if response.status_code == HTTP_NOT_FOUND:
        return jsonify(), HTTP_NOT_FOUND

    payload = {"username": username}

    JWT_SECRET = _get_jwt_secret()
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    payload = {"token": token}

    return jsonify(payload), HTTP_OK

@app.route('/register', methods=['POST'])
def register():
    body = request.get_json(silent=True)

    if not body or 'username' not in body or 'password' not in body:
        return jsonify(), HTTP_BAD_REQUEST

    username = body['username']
    password = body['password']
    password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    params = {'user' : username, 'pass' : password}

    response = requests.post('http://database_manager:8010/add', params = params)

    if response.status_code == HTTP_NOT_FOUND:
        return jsonify(), HTTP_NOT_FOUND

    return jsonify(), HTTP_OK

@app.route('/check', methods=['POST'])
def check():
    body = request.get_json(silent=True)

    print(body, file=sys.stderr)

    if 'token' not in body or 'username' not in body:
        error = {'msg': 'Missing fields'}
        return jsonify(error), HTTP_BAD_REQUEST

    token = body['token'][:-1]
    request_username = body['username'][2:]

    print(request_username, file=sys.stderr)

    try:
        JWT_SECRET = _get_jwt_secret()
        payload = jwt.decode(token, JWT_SECRET, algorithms=JWT_ALGORITHM)
        username = payload['username']
        print(username,file=sys.stderr)
    except jwt.ExpiredSignatureError:
        print("expired", file=sys.stderr)
        error = {'msg': 'Expired token'}
        return jsonify(error), HTTP_BAD_REQUEST
    except jwt.InvalidTokenError:
        error = {'msg': 'Invalid token'}
        print("invalid", file=sys.stderr)
        return jsonify(error), HTTP_BAD_REQUEST

    if username != request_username:
        return HTTP_CONFLICT

    return jsonify(payload), HTTP_OK

# Error handling
@app.errorhandler(404)
def page_not_found(e):
	return jsonify(), HTTP_NOT_FOUND

# Start web service
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8040, debug=True)

