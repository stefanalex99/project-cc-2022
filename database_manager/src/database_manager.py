from flask import Flask, request, jsonify
import os
import requests
import mysql.connector
import hashlib
import sys

app = Flask(__name__)

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

def _get_user():
    user_secret_file = open(os.environ['MYSQL_USER_FILE'])

    return user_secret_file.read().rstrip('\n')


def _get_password():
    password_secret_file = open(os.environ['MYSQL_PASSWORD_FILE'])

    return password_secret_file.read().rstrip('\n')

# Start database connection
def create_connection():
    user = _get_user()
    password = _get_password()

    return mysql.connector.connect(user = user, password = password, host = os.environ['MYSQL_HOSTNAME'], database = os.environ['MYSQL_DATABASE'])

@app.route('/auth', methods=['POST'])
def auth():
    db = create_connection()
    cursor = db.cursor(buffered=True)

    username = request.args.get("user")
    password_hash = request.args.get("pass")

    sql = "SELECT * FROM users WHERE username = %s AND password = %s"
    params = (username, password_hash)
    cursor.execute(sql, params)
    result = cursor.fetchone()

    if result is None:
        return jsonify(), HTTP_NOT_FOUND

    cursor.close()
    db.close()

    return jsonify(), HTTP_OK


@app.route('/add', methods=['POST'])
def add_user():
    username = request.args.get("user")
    password_hash = request.args.get("pass")

    db = create_connection()
    cursor = db.cursor(buffered=True)

    sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
    params = (username, password_hash)
    try:
        cursor.execute(sql, params)
    except mysql.connector.Error as err:
        return jsonify(), HTTP_CONFLICT

    db.commit()

    cursor.close()
    db.close()

    return jsonify(), HTTP_OK


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8010, debug=True)
