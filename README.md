# distributed-task-queue-system
A system with one "manager" and multiple "worker" nodes that process tasks concurrently.

## Project Structure
The project is composed of three directories:
- fronted
- worker
- manager
```
distributed-task-queue/
├── docker-compose.yml
├── manager/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── worker.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        └── App.js
```

### Architecture/Workflow
The data flow look like this:
#### Frontend (React): The user submits a task via a web form.
The process begins when the user enters a number into the web UI and clicks the "Calculate" button.

```
              +-------------------+
              |                   |
[👨‍💻 User] --> |   React Frontend  |
              |  (localhost:3000) |
              +-------------------+
                  |
                  | 1. HTTP POST Request
                  |    (e.g., {"number": 35})
                  v
```

#### Manager (Flask): Receives the request, generates a unique Task ID, and pushes a message { "id": "...", "number": "..." } to RabbitMQ. It immediately returns the Task ID to the frontend.
- The Manager (Flask API) receives the request.
- It generates a unique Task ID (e.g., abc-123).
- It immediately sends this Task ID back to the frontend.
- Crucially, it pushes the task (with its ID and the number) onto the task_queue in RabbitMQ.

```
            +-----------------+      +------------------+
            |  Flask Manager  |      |                  |
            | (localhost:5000)|--+   |     RabbitMQ     |
            +-----------------+  |   |   (Message Queue)|
                  ^              |   +------------------+
                  |              |         ^
                  |              |         | 2. Pushes Task
                  |              +---------+    {"id": "abc-123", "number": 35}
                  |
                  | 1b. Returns Task ID
                  |     {"task_id": "abc-123"}
                  |
            +------------------+
            |  React Frontend  |
            +------------------+
```

#### Worker: Picks up the task from RabbitMQ, calculates the result.
- One of the available, idle Worker containers is listening to the queue.
- It immediately grabs the new task message.
- It performs the heavy computation (the Fibonacci calculation).

```
                             +------------------+
                             |                  |
[ idle worker ] <------------|     RabbitMQ     |
                             |   (Message Queue)|
                             +------------------+
                                   |
                                   | 3. Grabs Task {"id": "abc-123", "number": 35}
                                   v
                             +------------------+
                             |  Python Worker   |
                             |  (Processing...) |
                             +------------------+
                                   |
                                   | 4. Calculates fib(35)
                                   v
                             +------------------+
                             |      Result      |
                             |     (9227465)    |
                             +------------------+
```

#### Worker to Redis: The worker stores the result in Redis using the Task ID as the key.
- Once the calculation is done, the worker connects to the Redis cache.
- It stores the result using the unique Task ID as the key.

```
         +------------------+      +-------------------+
         |  Python Worker   |      |                   |
         |   (Has Result)   |----->|      Redis        |
         +------------------+      |  (Key-Value Store)|
                                   +-------------------+
                                     |
                                     | 5. SET "abc-123"
                                     |    {"status": "complete", "result": 9227465}
```

#### Frontend to Manager: The frontend periodically asks the Manager ("polls") for the result of its Task ID.
- Meanwhile, the React Frontend has been periodically asking (polling) the Manager's `/task/<task_id>` endpoint for an update.
- Initially, the Manager would have found nothing in Redis and told the frontend the status was still "pending".
- Once the worker stores the result in Redis, the Manager's next check is successful.
- The Manager sends the final result back to the frontend.
- The UI automatically updates to show the task is complete and displays the final number.

```
    +------------------+      +------------------+      +------------------+
    |  React Frontend  |----->|  Flask Manager   |----->|      Redis       |
    |  (Polling...)    |      | (Checks for Task)|      | (Has the Result) |
    +------------------+      +------------------+      +------------------+
           ^      |                  |                        |
           |      | 6. GET /task/abc-123 (every 2s)           | 7. GET "abc-123"
           |      |                  |                        |
           |      +------------------+------------------------+
           |                         |
           | 8. Returns Result       |
           | {"status": "complete", "result": 9227465}
           |                         |
           |                         |
           v                         v
    +----------------------+
    |    UI Updates!       |
    | Status: Complete     |
    | Result: 9227465      |
    +----------------------+
```

#### Manager to Redis: The Manager checks Redis for the result.

#### Result to Frontend: Once the result is found in Redis, the Manager sends it back to the frontend, which updates the UI.