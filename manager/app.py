import pika
import redis
import json
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Allow requests from the frontend

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

def get_rabbitmq_connection():
    return pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

@app.route('/task', methods=['POST'])
def add_task():
    data = request.get_json()
    number = data.get('number')
    if number is None:
        return jsonify({"error": "No number provided"}), 400

    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    task_info = {"id": task_id, "number": number}

    # Set initial status in Redis
    redis_client.set(task_id, json.dumps({"status": "pending"}))

    # Send task to RabbitMQ
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=json.dumps(task_info),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    
    # Return the task ID to the client
    return jsonify({"task_id": task_id}), 202

@app.route('/task/<task_id>', methods=['GET'])
def get_task_result(task_id):
    result = redis_client.get(task_id)
    if result is None:
        return jsonify({"status": "not_found"}), 404
    
    return jsonify(json.loads(result)), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)