# 🦡 Zookeeper API – Message-Oriented Middleware (MOM)

This microservice is responsible for coordinating queues and topics within a distributed MOM system. It manages node registration, assignment tracking, node health, and failure simulation.

---

## 🚀 Technologies Used

- **FastAPI**
- **Redis**
- **Docker (optional)**
- **JSON-based communication**
- **No authentication required (token handled externally by MomServer)**

---

## 🌐 Base URL

```
http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper
```

---

## 📁 .env.example

```env
# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=strongpassword123*

# Node identity
NODE_ID=mom-local
NODE_HOST=http://localhost:8000

# Zookeeper instance
ZOOKEEPER_HOST=localhost
ZOOKEEPER_PORT=2181
```

---

## 🧠 How It Works

- Uses Redis to store queue/topic assignments and node metadata.
- Registers queues/topics under: `zookeeper:queue_topic_registry`
- Stores node-specific assignments under: `zookeeper:node:{NODE_ID}`
- Tracks active nodes in: `zookeeper:nodes`
- Logs events under keys like: `log:events`

---

## 📦 Endpoints

### 1. Register Queue or Topic

**POST** `/queue_topic/registry`

Registers a queue or topic with origin and replica nodes.

#### Request Body
```json
{
  "name": "queue_demo",
  "type": "queue", // or "topic"
  "operation": "create",
  "origin_node": "mom-local",
  "replica_nodes": ["mom-b", "mom-c"]
}
```

#### Response
```json
{
  "status": "success",
  "registry": { ... }
}
```

---

### 2. Delete Queue or Topic

**DELETE** `/queue_topic/registry`

#### Request Body
```json
{
  "name": "queue_demo",
  "type": "queue"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Assignment removed"
}
```

---

### 3. Get All Queue/Topic Registry

**GET** `/queue_topic`

Returns all stored queue/topic assignments.

---

### 4. Get Specific Queue/Topic Info

**GET** `/queue_topic/registry/{name}`

Example:
```
/queue_topic/registry/queue_demo
```

---

### 5. Get Nodes Assigned to a Queue/Topic

**GET** `/queue_topic/assigned_nodes?name=queue_demo&type=queue`

Returns a list of node IDs that hold the given queue/topic.

---

### 6. List All Active Nodes

**GET** `/nodes`

Returns all nodes currently marked as active in the registry.

---

### 7. Check Node Health

**GET** `/node/health?node=mom-local`

Returns:
```json
{
  "node": "mom-local",
  "alive": true
}
```

---

### 8. View Node Assignments (Query Param)

**GET** `/node/assignments?node=mom-local`

---

### 9. View Node Assignments (Path Param)

**GET** `/registry/node/{node_id}`

Example:
```
/registry/node/mom-local
```

---

### 10. View System Logs

**GET** `/logs`

Returns Redis-stored logs, e.g.:
```json
{
  "logs": {
    "log:events": [
      {
        "timestamp": "2025-04-14 15:21:21",
        "node": "mom-1",
        "message": "✅ Node registered"
      }
    ]
  }
}
```

---

### 11. Simulate Node Failure (for testing)

**POST** `/zk/failure/{node_id}`

Example:
```
POST /zk/failure/mom-local
```

Response:
```json
{
  "status": "node_failure_logged",
  "node": "mom-local"
}
```

---

## 🧪 Testing with cURL

```bash
# Register a new queue
curl -X POST http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/queue_topic/registry   -H "Content-Type: application/json"   -d '{
    "name": "queue_demo",
    "type": "queue",
    "operation": "create",
    "origin_node": "mom-local",
    "replica_nodes": ["mom-b"]
  }'

# List all nodes
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/nodes

# Get queue assignments
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/queue_topic

# Get node-specific assignments
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/registry/node/mom-local

# Delete queue
curl -X DELETE http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/queue_topic/registry   -H "Content-Type: application/json"   -d '{"name": "queue_demo", "type": "queue"}'

# Simulate failure
curl -X POST http://localhost:8100/zk/failure/mom-local
```

---

## ✅ Status Codes

| Code | Meaning                |
|------|------------------------|
| 200  | OK                     |
| 400  | Bad Request            |
| 404  | Not Found              |
| 500  | Internal Server Error  |

---

## 📌 Notes

- All operations are **stateless**, stored in Redis.
- Can be integrated directly into FastAPI's admin panel via Swagger.
- Works **independently** of authentication, relying on other microservices (e.g., `MomServer`) to manage users and tokens.
