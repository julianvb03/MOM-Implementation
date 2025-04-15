
# 🦡 Zookeeper API – MOM Coordination Service

This microservice provides support for message-oriented middleware (MOM) coordination, including management of queues/topics, node health checks, and registry via Redis.

---

## 📍 Base URL

```
http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper
```

---

## 📦 Endpoints Summary

| Method | Endpoint                                                                                          | Description                            |
|--------|---------------------------------------------------------------------------------------------------|----------------------------------------|
| GET    | `/nodes`                                                                                           | List all registered nodes              |
| GET    | `/queue_topic`                                                                                     | Get full queue/topic registry          |
| GET    | `/logs`                                                                                            | Retrieve all system logs               |
| POST   | `/queue_topic/registry`                                                                            | Register a new queue or topic          |
| DELETE | `/queue_topic/registry`                                                                            | Delete a queue or topic                |
| GET    | `/queue_topic/registry/{name}`                                                                     | Get a specific queue/topic entry       |
| GET    | `/queue_topic/assigned_nodes?name={name}&type={type}`                                              | Get nodes that have a specific queue/topic |
| GET    | `/node/health?node={node_id}`                                                                      | Check if a node is active              |
| GET    | `/node/assignments?node={node_id}`                                                                 | Get all assignments for a node         |
| GET    | `/registry/node/{node_id}`                                                                         | Alternate: Get all assignments for node via path |

---

## 🧪 Example `curl` Requests

### ✅ Register Queue/Topic
```bash
curl -X POST http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cola_demo",
    "type": "queue",
    "operation": "create",
    "origin_node": "mom-a",
    "replica_nodes": ["mom-b"]
  }'
```

---


### ❌ Delete Queue/Topic
```bash
curl -X DELETE http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cola_demo",
    "type": "queue"
  }'
```

---

### 🔍 Get All Queue/Topic Registry
```bash
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic
```

---

### 📄 Get Specific Queue/Topic
```bash
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry/cola_demo
```

---

### 📡 Get Nodes with Specific Queue/Topic
```bash
curl "http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/assigned_nodes?name=cola_demo&type=queue"
```

---

### 💬 Get All Logs
```bash
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/logs
```

---

### 📋 List All Registered Nodes
```bash
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/nodes
```

---

### ❤️ Check Node Health
```bash
curl "http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/node/health?node=mom-a"
```

---

### 🧾 Get Assignments for a Node (Query Param)
```bash
curl "http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/node/assignments?node=mom-a"
```
---

This documentation is automatically generated for the local dev version. Adjust URLs and configuration if deploying to production.

## 🧪 Complete cURL Test Suite

```bash
# 1. Create queue/topic
curl -X POST http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry -H "Content-Type: application/json" -d '{
  "name": "cola_demo",
  "type": "queue",
  "operation": "create",
  "origin_node": "mom-a",
  "replica_nodes": ["mom-b", "mom-c"]
}'

# 2. Delete queue/topic
curl -X DELETE http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry -H "Content-Type: application/json" -d '{
  "name": "cola_demo",
  "type": "queue"
}'

# 3. Get all queue/topic registry
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic

# 4. Get details of a queue/topic
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/registry/cola_demo

# 5. Get nodes with a queue/topic
curl "http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/queue_topic/assigned_nodes?name=cola_demo&type=queue"

# 6. Get all active nodes
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/nodes

# 7. Check node health
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/node/health?node=mom-local

# 8. View logs
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/logs

# 9. Get queues/topics for node (path param)
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/registry/node/mom-local

# 10. Get queues/topics for node (query param)
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/node/assignments?node=mom-local

# 11. Simulate failure of a node (if endpoint exists)
curl -X POST http://localhost:8100/zk/failure/mom-local
```


### 🧾 Get Assignments for a Node (Path Param)
```bash
curl http://localhost:8100/api/v1.0.0/MomServer/admin/zookeeper/zookeeper/registry/node/mom-a
```

---

## ⚙️ .env.example

```env
API_NAME=MomServer
API_VERSION=v1.0.0

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=strongpassword123*

DEFAULT_USER_NAME=admin
DEFAULT_USER_PASSWORD=123

ZOOKEEPER_HOST=zookeeper
ZOOKEEPER_PORT=2181

NODE_A_IP=localhost
NODE_B_IP=localhost
NODE_C_IP=localhost
GRPC_PORT=50051
WHOAMI=mom-local
```

---

## 🏁 Running the Service

```bash
uvicorn app.main:app --reload --port 8100
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8100
```

> Swagger Docs: [http://localhost:8100/docs](http://localhost:8100/docs)

---

## 🧠 Internal Keys in Redis

- `zookeeper:nodes` → Set of registered nodes
- `zookeeper:queue_topic_registry` → All queues and topics
- `zookeeper:node:{node_id}` → Assignments per node
- `log:*` → Logs by node or operation

---