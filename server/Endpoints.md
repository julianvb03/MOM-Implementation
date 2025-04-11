# API Endpoint Documentation

## Table of Contents

1. [Root Endpoints](#root-endpoints)
   - [Root](#root)
   - [Login](#login)
   - [Protected](#protected)
   - [Protected Admin](#protected-admin)
2. [MOM (Message-Oriented Middleware) Endpoints](#mom-message-oriented-middleware-endpoints)
   - [Subscribe](#subscribe)
   - [Unsubscribe](#unsubscribe)
   - [Send Message](#send-message)
   - [Receive Message](#receive-message)
3. [Admin User Management Endpoints](#admin-user-management-endpoints)
   - [Remove User](#remove-user)
   - [Create User](#create-user)
4. [Admin MOM Management Endpoints](#admin-mom-management-endpoints)
   - [Create Queue/Topic](#create-queuetopic)
   - [Delete Queue/Topic](#delete-queuetopic)

---

## Root Endpoints

### Root

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}`

#### **Method**
`GET`

#### **Description**
Returns a welcome message for the MOM TET API.

---

#### **Request Data**
- **No body parameters required.**

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| (none)   | string | Yes      | Welcome message as a plain string    |

##### Success Response (200 OK)
```json
"Welcome to MOM TET API!"
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Login

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/login/`

#### **Method**
`POST`

#### **Description**
Authenticates a user and returns a JWT token.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field     | Type   | Required | Description                |
|-----------|--------|----------|----------------------------|
| username  | string | Yes      | User’s username            |
| password  | string | Yes      | User’s password            |

##### Example Request Body:
```json
{
    "username": "admin",
    "password": "123"
}
```

#### **Response Data**

##### Body Parameters (JSON):
| Field         | Type   | Required | Description                  |
|---------------|--------|----------|------------------------------|
| access_token  | string | Yes      | JWT token for authentication|
| token_type    | string | Yes      | Type of token (e.g., "Bearer") |

##### Success Response (200 OK)
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer"
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Invalid username or password"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Protected

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/protected/`

#### **Method**
`GET`

#### **Description**
A protected endpoint requiring authentication, returns a personalized welcome message.

---

#### **Request Data**
- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

- **No body parameters required.**

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| (none)   | string | Yes      | Personalized welcome message         |

##### Success Response (200 OK)
```json
"This is a protected endpoint. Welcome, admin!"
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Protected Admin

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/admin/protected/`

#### **Method**
`GET`

#### **Description**
A protected endpoint requiring admin authentication, returns a welcome message for admins.

---

#### **Request Data**
- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

- **No body parameters required.**

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| (none)   | string | Yes      | Admin welcome message                |

##### Success Response (200 OK)
```json
"This is the protected admin endpoint. Welcome, admin!"
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Admin access required"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

## MOM (Message-Oriented Middleware) Endpoints

### Subscribe

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/queue_topic/subscribe/`

#### **Method**
`POST`

#### **Description**
Subscribes an authenticated user to a queue or topic in the message broker.

#### **Limiter**

- **Rate Limit**: 200 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| name  | string | Yes      | Name of the queue or topic to subscribe to |
| type  | string | Yes      | Type ("queue" or "topic")            |

##### Example Request Body:
```json
{
    "name": "queue-example",
    "type": "queue"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Message logging the operation information                     |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "User noadmin subscribed to topic topic-example"
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid queue/topic name"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Unsubscribe

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/queue_topic/unsubscribe/`

#### **Method**
`POST`

#### **Description**
Unsubscribes an authenticated user from a queue or topic in the message broker.

#### **Limiter**

- **Rate Limit**: 200 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field | Type   | Required | Description                            |
|-------|--------|----------|----------------------------------------|
| name  | string | Yes      | Name of the queue or topic to unsubscribe from |
| type  | string | Yes      | Type ("queue" or "topic")            |

##### Example Request Body:
```json
{
    "name": "queue-example",
    "type": "queue"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Message logging the operation information                     |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "User noadmin unsubscribed from queue-example"
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid queue/topic name"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Send Message

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/queue_topic/send/`

#### **Method**
`POST`

#### **Description**
Sends a message to a queue or topic in the message broker by an authenticated user.

#### **Limiter**

- **Rate Limit**: 200 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field   | Type   | Required | Description                          |
|---------|--------|----------|--------------------------------------|
| name    | string | Yes      | Name of the queue or topic           |
| message | string | Yes      | Message content to send              |
| type  | string | Yes      | Type ("queue" or "topic")            |

##### Example Request Body:
```json
{
    "name": "queue-example",
    "message": "Hello, world!",
    "type": "queue"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Message logging the operation information                     |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "Message published to topic topic-example"
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid queue/topic name"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Receive Message

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/queue_topic/receive/`

#### **Method**
`POST`

#### **Description**
Receives a message from a queue or topic in the message broker for an authenticated user.

#### **Limiter**

- **Rate Limit**: 200 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| name  | string | Yes      | Name of the queue or topic           |
| type  | string | Yes      | Type ("queue" or "topic")            |

##### Example Request Body:
```json
{
    "name": "queue-example",
    "type": "queue"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Content of the queue or topic receive, if the structure is empty is null                    |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "Hello, world!"
}
```
No messages in the structure: 
```json
{
    "success": true,
    "message": null
}
```


##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid queue/topic name"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

## Admin User Management Endpoints

### Remove User

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/admin/users/remove/{user}`

#### **Method**
`DELETE`

#### **Description**
Removes a specified user from the system (admin-only).

---

#### **Request Data**

##### Path Parameters:
| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| user  | string | Yes      | Username of the user to remove       |

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

- **No body parameters required.**

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| (none)   | string | Yes      | Success or not-found message         |

##### Success Response (200 OK)
```json
"User testuser removed successfully."
```

##### Success Response (User Not Found)
```json
"User testuser not found."
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Admin access required"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Create User

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/admin/users/create/`

#### **Method**
`PUT`

#### **Description**
Creates a new user in the system (admin-only).

---

#### **Request Data**

##### Body Parameters (JSON):
| Field     | Type   | Required | Description                |
|-----------|--------|----------|----------------------------|
| username  | string | Yes      | User’s username            |
| password  | string | Yes      | User’s password            |

##### Example Request Body:
```json
{
    "username": "newuser",
    "password": "password123"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| (none)   | string | Yes      | Success message                      |

##### Success Response (200 OK)
```json
"User newuser created successfully."
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Admin access required"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

## Admin MOM Management Endpoints

### Create Queue/Topic

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/admin/queue_topic/create/`

#### **Method**
`PUT`

#### **Description**
Creates a new queue or topic in the message broker (admin-only).

#### **Limiter**

- **Rate Limit**: 100 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Body Parameters (JSON):
| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| name  | string | Yes      | Name of the queue or topic           |
| type  | string | Yes      | Type ("queue" or "topic")            |

##### Example Request Body:
```json
{
    "name": "queue-example",
    "type": "queue"
}
```

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Message logging the operation information                     |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "Queue queue-example created successfully."
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid type: must be 'queue' or 'topic'"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Delete Queue/Topic

#### **Endpoint**
`/api/{API_VERSION}/{API_NAME}/admin/queue_topic/delete/{name}?type={type}`

#### **Method**
`DELETE`

#### **Description**
Deletes a queue or topic from the message broker by name (admin-only).

#### **Limiter**

- **Rate Limit**: 100 requests per minute. It was configured with the limiter.py file.

---

#### **Request Data**

##### Path Parameters:
| Field | Type   | Required | Description                          |
|-------|--------|----------|--------------------------------------|
| name  | string | Yes      | Name of the queue or topic to delete |
| type  | string | Yes      | Type ("queue" or "topic")            |

- **Headers**:
  | Field         | Type   | Required | Description                  |
  |---------------|--------|----------|------------------------------|
  | Authorization | string | Yes      | Bearer token (e.g., "Bearer <token>") |

- **No body parameters required.**

#### **Response Data**

##### Body Parameters (JSON):
| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| success   | boolean | Yes      | True if the operation was successful and False otherwise                     |
| message  | string or null | Yes      | Message logging the operation information                     |

##### Success Response (200 OK)
```json
{
    "success": true,
    "message": "Queue queue-example deleted successfully."
}
```

##### Error Response (401 Unauthorized)
```json
{
    "success": false,
    "error": "Not authenticated"
}
```

##### Error Response (403 Forbidden)
```json
{
    "success": false,
    "error": "Invalid queue/topic name"
}
```

##### Error Response (429 Too Many Requests)
```json
{
    "success": false,
    "error": "Too many requests."
}
```

##### Error Response (500 Internal Server Error)
```json
{
    "success": false,
    "error": "Internal Server Error"
}
```

---

### Notes
1. **DTOs**:
   - `UserDto`: Contains `username` and `password` fields.
   - `UserLoginResponse`: Contains `access_token` and `token_type`.
   - `QueueTopic`: Contains a `name` field and a `type` field (enum: `"queue"`, `"topic"`).
   - `MessageQueueTopic`: Contains `name` and `message` fields.
   - `ResponseError`: Contains `success` (boolean) and `error` (string).

2. **Placeholders**: Many endpoints currently return placeholder strings. Update the documentation as you implement full logic (e.g., structured JSON responses).
