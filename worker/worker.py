import pika
import time
import os
import json
import redis

# Connect to Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)

def fibonacci(n):
    # (Fibonacci function remains the same)
    if n < 0: return "Incorrect input"
    elif n == 0: return 0
    elif n == 1 or n == 2: return 1
    else: return fibonacci(n-1) + fibonacci(n-2)

def main():
    # Give RabbitMQ time to start
    print("[*] Worker waiting for RabbitMQ to start...")
    time.sleep(10)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=600, blocked_connection_timeout=300))
    channel = connection.channel()

    channel.queue_declare(queue='task_queue', durable=True)
    print(f'[*] Worker ({os.getpid()}) waiting for tasks.')

    def callback(ch, method, properties, body):
        task_info = json.loads(body.decode())
        task_id = task_info['id']
        number = int(task_info['number'])

        try:
            if number > 40:
                # print(f"[!] Worker ({os.getpid()}) received a task that is too large: {number}. Skipping.")
                # result_data = {"status": "error", "result": "Input too large"}
                # redis_client.set(task_id, json.dumps(result_data))
                # ch.basic_ack(delivery_tag=method.delivery_tag)
                # return
                raise ValueError("Input number is too large to process.")
            
            print(f"[*] Worker ({os.getpid()}) received task {task_id}: Fibonacci for {number}")
            
            result = fibonacci(number)
            
            print(f"[*] Worker ({os.getpid()}) finished task {task_id}. Result: {result}")

            # Store the result in Redis
            result_data = {"status": "complete", "result": result}
            redis_client.set(task_id, json.dumps(result_data))

            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        except Exception as e:
            print(f"[!] Worker ({os.getpid()}) failed task {task_id}: {e}")

            # Store the error message in Redis
            error_data = {"status": "failed", "error": str(e)}
            redis_client.set(task_id, json.dumps(error_data))

            # Negatively acknowledge the message and DO NOT requeue it
            ch.basic_ack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='task_queue', on_message_callback=callback)
    channel.start_consuming()

if __name__ == '__main__':
    main()