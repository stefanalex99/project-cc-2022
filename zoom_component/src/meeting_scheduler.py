from pyzoom import ZoomClient
from flask import request
from datetime import datetime as dt
import requests
import os
import random
import string
import pika
import sys
from time import sleep

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

def _get_api_key():
    api_key_file = open(os.environ['API_KEY'])

    return api_key_file.read().rstrip('\n')


def _get_api_secret():
    api_secret_file = open(os.environ['API_SECRET'])

    return api_secret_file.read().rstrip('\n')


sleep(20)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='broker'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

def generate():
    #   Get zoom client.
    API_KEY = _get_api_key()
    API_SECRET = _get_api_secret()

    client = ZoomClient(API_KEY, API_SECRET)

    PASSWORD_LENGTH = 8
    LETTERS = string.ascii_lowercase
    password = ''.join(random.choice(LETTERS) for i in range(PASSWORD_LENGTH))

    meeting = client.meetings.create_meeting(topic = 'Medical Appointment',
                                            start_time = dt.now().isoformat(),
                                            duration_min = 60,
                                            password = password)

    return meeting.join_url + " " + password


def on_request(ch, method, props, body):
    parsed_body = str(body).split()

    response = ""

    if not len(parsed_body) == 2:
        response = str(HTTP_BAD_REQUEST)
    else:
        username = parsed_body[0]
        token = parsed_body[1]

        params = {'username' : username, 'token': token}
        http_response = requests.post('http://auth:8040/check', json = params)

        if http_response.status_code == HTTP_BAD_REQUEST:
            response = str(HTTP_BAD_REQUEST)
        elif http_response.status_code == HTTP_CONFLICT:
            response = str(HTTP_CONFLICT)
        else:
            response = generate()


    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

channel.start_consuming()
