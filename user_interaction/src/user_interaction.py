from flask import Flask, request, jsonify
import requests
import pika
import uuid
import sys

app = Flask(__name__)


# RabbitMQ
class MeetingRpcClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='broker'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange = '',
            routing_key = 'rpc_queue',
            properties = pika.BasicProperties(
                reply_to = self.callback_queue,
                correlation_id = self.corr_id,
            ),
            body = str(n))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

# HTTP Status Codes
HTTP_OK = 200

# Routes
@app.route('/login', methods=['POST'])
def req_login():
    body = request.get_json(silent=True)
    new_req = requests.post('http://auth:8040/login', json = body)

    if new_req.status_code != HTTP_OK:
        return jsonify(), new_req.status_code

    return new_req.json()

@app.route('/register', methods=['POST'])
def req_register():
    body = request.get_json(silent=True)
    new_req = requests.post('http://auth:8040/register', json = body)

    if new_req.status_code != HTTP_OK:
        return jsonify(), new_req.status_code

    return new_req.json()

@app.route('/schedule_meeting', methods=['POST'])
def req_create_meeting():
    body = request.get_json(silent=True)

    args = body['username'] + " " + body['token']
    meeting_rpc = MeetingRpcClient()
    resp = meeting_rpc.call(args)

    print(resp, file=sys.stderr)

    resp_parsed = str(resp.decode("utf-8")).split()

    if len(resp_parsed) == 1:
        return jsonify(), int(resp_parsed[0])

    response = {'join_url' : resp_parsed[0], 'meeting_password' : resp_parsed[1]}

    return jsonify(response)

# Start web server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
