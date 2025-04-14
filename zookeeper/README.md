# 🦡 Zookeeper API - Message-Oriented Middleware

This microservice coordinates the creation and assignment of queues and topics in a distributed MOM (Message-Oriented Middleware) system. It also allows node registration, failure simulation, and tracking of MOM node health.

---

## 🧩 Technologies Used

- **FastAPI**
- **Redis**
- **Docker (optional)**
- **JSON for data exchange**
- **Authentication via MomServer (JWT-based)**

---

## 📦 Available Endpoints

### 1. 🚀 Create Queue or Topic

Registers a new queue or topic, with origin node and replicas.

```http
POST /queue_topic/registry
```

#### Payload:
```json
{
  "name": "demo_queue",
  "type": "queue", // or "topic"
  "operation": "create",
  "origin_node": "mom-a",
  "replica_nodes": ["mom-b", "mom-c"]
}
```

#### Response:
```json
{
  "status": "success",
  "registry": {
    ...
  }
}
```

---

### 2. ❌ Delete Queue or Topic

Deletes a queue/topic assignment.

```http
DELETE /queue_topic/registry
```

#### Payload:
```json
{
  "name": "demo_queue",
  "type": "queue"
}
```

---

### 3. 📚 List All Registry Entries

```http
GET /queue_topic
```

---

### 4. 📄 Get Registry Info by Name

```http
GET /queue_topic/registry/{name}
```

---

### 5. 🧠 Get Nodes that Have a Queue/Topic

```http
GET /queue_topic/assigned_nodes?name=demo_queue&type=queue
```

---

### 6. 🧭 List Active MOM Nodes

```http
GET /nodes
```

---

### 7. ❤️ Check Node Health

```http
GET /node/health?node=mom-a
```

---

### 8. 📜 View System Logs

```http
GET /logs
```

---

### 9. 📦 Get Assignments of a Node (by path)

```http
GET /registry/node/{node_id}
```

---

### 10. 📦 Get Assignments of a Node (by query param)

```http
GET /node/assignments?node=mom-local
```

---

## ⚙️ Internal Redis Keys

- `zookeeper:queue_topic_registry`
- `zookeeper:node:{node_id}`
- `zookeeper:nodes`
- `log:*`

---

## 🧪 CURL Test Examples

```bash
# Create queue
curl -X POST http://localhost:8100/queue_topic/registry -H "Content-Type: application/json" -d '{
  "name": "queue_demo",
  "type": "queue",
  "operation": "create",
  "origin_node": "mom-a",
  "replica_nodes": ["mom-b", "mom-c"]
}'

# Check which nodes have it
curl "http://localhost:8100/queue_topic/assigned_nodes?name=queue_demo&type=queue"

# Delete queue
curl -X DELETE http://localhost:8100/queue_topic/registry -H "Content-Type: application/json" -d '{
  "name": "queue_demo",
  "type": "queue"
}'

# Check node assignments
curl http://localhost:8100/registry/node/mom-a

# Check node health
curl http://localhost:8100/node/health?node=mom-a
```

---

## 🛠️ .env.example

```env
# Basic info
API_NAME=MomServer
API_VERSION=v1.0.0
JWT_SECRET=mysupersecret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=strongpassword123*

# MOM Node Info
NODE_ID=mom-local
NODE_HOST=http://localhost:8000

# Optional: For discovery or logging
GRPC_PORT=50051

# Zookeeper
ZOOKEEPER_HOST=localhost
ZOOKEEPER_PORT=2181
```

---

## ▶️ How to Run

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Export your environment variables or create a `.env` file.

3. Run the API:
```bash
uvicorn app.main:app --reload --port 8100
```

4. Test with `curl` or Swagger UI at:
```
http://localhost:8100/docs
```
