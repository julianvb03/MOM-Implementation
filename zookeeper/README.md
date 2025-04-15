
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
# ========================
# 🔧 API Basic Configuration
# ========================
API_NAME=MomServer                  # Name of the main MOM API service
API_VERSION=v1.0.0                  # Current version of the API

# ========================
# 🧠 Redis Configuration
# ========================
REDIS_HOST=localhost                # Redis host (localhost or container name)
REDIS_PORT=6379                     # Redis default port
REDIS_PASSWORD=strongpassword123*   # Redis password (change in production)

# ========================
# 👤 Default Internal Admin User
# ========================
DEFAULT_USER_NAME=admin             # Initial admin username
DEFAULT_USER_PASSWORD=123           # Initial admin password

# ========================
# 🐘 Zookeeper Settings
# ========================
ZOOKEEPER_HOST=zookeeper            # Hostname or container name of the Zookeeper service
ZOOKEEPER_PORT=2181                 # Default Zookeeper port

# ========================
# 🌐 MOM Cluster Node IPs
# ========================
NODE_A_IP=172.31.85.206             # IP address of Node A
NODE_B_IP=172.31.93.141             # IP address of Node B
NODE_C_IP=172.31.80.53              # IP address of Node C
GRPC_PORT=50051                     # Port used for gRPC communication between nodes

# ========================
# 🆔 Node Runtime Identity (Set individually before running each node)
# ========================
# These must be overridden at runtime or in individual env files per node

# NODE_ID=mom-a                     # Unique internal ID for the node
# NODE_HOST=http://172.31.85.206:8000  # Public HTTP host of this node
# WHOAMI=mom-a                      # Logical name of the node (used in logs, assignments, etc.)

# ========================
# ▶️ Example Run Commands Per Node (Optional)
# ========================
# 👉 Run this manually depending on the node
# NODE_ID=mom-a NODE_HOST=http://172.31.85.206:8000 WHOAMI=mom-a uvicorn app.main:app --host 0.0.0.0 --port 8000
# NODE_ID=mom-b NODE_HOST=http://172.31.93.141:8000 WHOAMI=mom-b uvicorn app.main:app --host 0.0.0.0 --port 8000
# NODE_ID=mom-c NODE_HOST=http://172.31.80.53:8000 WHOAMI=mom-c uvicorn app.main:app --host 0.0.0.0 --port 8000


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