# Messaging API Specification

## Base URL

/api/v1/messages

## Endpoints

### List Channels

GET /api/v1/messages/channels

#### Purpose
List channels visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`message:read`

### Create Channel

POST /api/v1/messages/channels

#### Purpose
Create a new messaging channel.

#### Authentication
JWT required.

#### Permission
`message:create`

### Get Channel by ID

GET /api/v1/messages/channels/{id}

#### Purpose
Retrieve a channel and its metadata.

#### Authentication
JWT required.

#### Permission
`message:read`

### List Channel Messages

GET /api/v1/messages/channels/{id}/messages

#### Purpose
Retrieve message history for a channel.

#### Authentication
JWT required.

#### Permission
`message:read`

### Create Message

POST /api/v1/messages/channels/{id}/messages

#### Purpose
Send a message into a channel.

#### Authentication
JWT required.

#### Permission
`message:create`

#### Request Body
```json
{
  "body": "Hello team"
}
```

### Update Message

PATCH /api/v1/messages/{id}

#### Purpose
Edit an existing message.

#### Authentication
JWT required.

#### Permission
`message:update`

### Delete Message

DELETE /api/v1/messages/{id}

#### Purpose
Delete a message.

#### Authentication
JWT required.

#### Permission
`message:delete`
