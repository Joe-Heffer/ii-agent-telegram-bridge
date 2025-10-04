# II-Agent Backend API Documentation

This document provides comprehensive documentation for all REST API endpoints and WebSocket interfaces in the II-Agent backend.

## Base URL

- Development: `http://localhost:8000`
- Production: Configured via deployment settings

## Authentication

Currently, the API does not require authentication. CORS is enabled for all origins.

---

## REST API Endpoints

### Sessions API

#### Get Sessions by Device ID

Retrieves all sessions associated with a specific device ID, sorted by creation time (newest first).

**Endpoint:** `GET /api/sessions/{device_id}`

**Path Parameters:**
- `device_id` (string, required): The device identifier to look up sessions for

**Response:** `200 OK`

```json
{
  "sessions": [
    {
      "id": "string (UUID)",
      "workspace_dir": "string",
      "created_at": "string (ISO 8601 timestamp)",
      "device_id": "string",
      "name": "string"
    }
  ]
}
```

**Error Responses:**
- `500 Internal Server Error`: Database or server error

**Example Request:**
```bash
curl http://localhost:8000/api/sessions/device-123
```

**Example Response:**
```json
{
  "sessions": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "workspace_dir": "/workspace/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "created_at": "2025-10-04T12:30:45.123456",
      "device_id": "device-123",
      "name": "My Agent Session"
    }
  ]
}
```

---

#### Get Session Events

Retrieves all events for a specific session, sorted by timestamp (oldest first).

**Endpoint:** `GET /api/sessions/{session_id}/events`

**Path Parameters:**
- `session_id` (string, required): The session UUID to retrieve events for

**Response:** `200 OK`

```json
{
  "events": [
    {
      "id": "string (UUID)",
      "session_id": "string (UUID)",
      "timestamp": "string (ISO 8601 timestamp)",
      "event_type": "string",
      "event_payload": {},
      "workspace_dir": "string"
    }
  ]
}
```

**Event Types:**
- `query`: User query/message
- `tool_use`: Agent tool invocation
- `tool_result`: Tool execution result
- `response`: Agent response
- `error`: Error event
- And other custom event types

**Error Responses:**
- `500 Internal Server Error`: Database or server error

**Example Request:**
```bash
curl http://localhost:8000/api/sessions/a1b2c3d4-e5f6-7890-abcd-ef1234567890/events
```

**Example Response:**
```json
{
  "events": [
    {
      "id": "e1f2g3h4-i5j6-7890-klmn-op1234567890",
      "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "timestamp": "2025-10-04T12:31:00.000000",
      "event_type": "query",
      "event_payload": {
        "text": "Help me build a web app",
        "files": []
      },
      "workspace_dir": "/workspace/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ]
}
```

---

### Settings API

#### Get Settings

Retrieves the current application settings with API keys redacted for security.

**Endpoint:** `GET /api/settings`

**Response:** `200 OK`

```json
{
  "llm_api_key_set": true,
  "search_api_key_set": false,
  "llm_configs": {
    "anthropic": {
      "api_key": null,
      "model": "claude-sonnet-4-20250514",
      "max_tokens": 8192
    }
  },
  "sandbox_config": {
    "sandbox_type": "local",
    "sandbox_api_key": null,
    "template_id": null
  },
  "search_config": {
    "serpapi_api_key": null,
    "tavily_api_key": null,
    "firecrawl_api_key": null,
    "jina_api_key": null
  },
  "audio_config": {
    "openai_api_key": null
  },
  "media_config": {
    "google_ai_studio_api_key": null
  },
  "third_party_integration_config": {
    "vercel_api_key": null,
    "openai_api_key": null,
    "neon_db_api_key": null
  }
}
```

**Fields:**
- `llm_api_key_set` (boolean): Indicates if any LLM API key is configured (actual keys redacted)
- `search_api_key_set` (boolean): Indicates if search API key is configured
- `llm_configs` (object): LLM provider configurations (API keys set to null in response)
- `sandbox_config` (object): Sandbox environment settings
- `search_config` (object): Web search provider settings
- `audio_config` (object): Audio/TTS settings
- `media_config` (object): Media processing settings
- `third_party_integration_config` (object): Third-party integration settings

**Error Responses:**
- `404 Not Found`: Settings not found

**Security Note:** All API keys are redacted (set to `null`) in the response. The `*_api_key_set` boolean fields indicate whether keys are configured without exposing the actual values.

---

#### Update Settings

Stores or updates application settings. Existing settings are merged with new values.

**Endpoint:** `POST /api/settings`

**Request Body:**

```json
{
  "llm_configs": {
    "anthropic": {
      "api_key": "sk-ant-...",
      "model": "claude-sonnet-4-20250514",
      "max_tokens": 8192
    }
  },
  "sandbox_config": {
    "sandbox_type": "docker"
  }
}
```

**Response:** `200 OK`

```json
{
  "message": "Settings stored"
}
```

**Error Responses:**
- `500 Internal Server Error`: Failed to store settings

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "llm_configs": {
      "anthropic": {
        "api_key": "sk-ant-api-key",
        "model": "claude-sonnet-4-20250514"
      }
    }
  }'
```

**Note:** Only provided fields are updated; existing settings are preserved.

---

### File Upload API

#### Upload File

Uploads a file to the workspace for a specific session. Supports both text and binary files (via base64 encoding). Handles filename collisions automatically.

**Endpoint:** `POST /api/upload`

**Request Body:**

```json
{
  "session_id": "string (UUID)",
  "file": {
    "path": "string (filename)",
    "content": "string (file content or base64 data URL)"
  }
}
```

**Content Formats:**
- Text files: Plain string content
- Binary files: Base64 data URL format: `data:<mime-type>;base64,<base64-encoded-content>`

**Response:** `200 OK`

```json
{
  "message": "File uploaded successfully",
  "file": {
    "path": "string (relative path in workspace)",
    "saved_path": "string (absolute filesystem path)"
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing `session_id` or file data
- `404 Not Found`: Workspace not found for session
- `500 Internal Server Error`: Upload failed

**Example Request (Text File):**
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "file": {
      "path": "example.txt",
      "content": "Hello, World!"
    }
  }'
```

**Example Request (Binary File):**
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "file": {
      "path": "document.pdf",
      "content": "data:application/pdf;base64,JVBERi0xLjQKJ..."
    }
  }'
```

**Example Response:**
```json
{
  "message": "File uploaded successfully",
  "file": {
    "path": "/uploads/example.txt",
    "saved_path": "/workspace/a1b2c3d4-e5f6-7890-abcd-ef1234567890/uploads/example.txt"
  }
}
```

**Behavior Notes:**
- Files are uploaded to `{workspace}/{session_id}/uploads/` directory
- Absolute paths in `file.path` are converted to filenames only
- If a file with the same name exists, a suffix is added (e.g., `file_1.txt`, `file_2.txt`)
- Upload directory is created automatically if it doesn't exist

---

## WebSocket API

### Connection

**Endpoint:** `ws://localhost:8000/ws`

The WebSocket endpoint provides real-time bidirectional communication for agent chat sessions.

**Connection Flow:**
1. Client connects to `/ws`
2. Server creates a new session and workspace
3. Client sends initialization and query messages
4. Server streams events back to client
5. Session persists until disconnection

---

### WebSocket Message Format

All messages follow this structure:

```json
{
  "type": "string (message type)",
  "content": {}
}
```

---

### Client → Server Messages

#### Initialize Agent

Initializes the agent with specific model and configuration.

```json
{
  "type": "init_agent",
  "content": {
    "model_name": "claude-sonnet-4-20250514",
    "tool_args": {},
    "thinking_tokens": 0
  }
}
```

**Fields:**
- `model_name` (string): LLM model identifier
- `tool_args` (object): Optional tool-specific arguments
- `thinking_tokens` (number): Extended thinking budget (0 = disabled)

---

#### Send Query

Sends a user query/message to the agent.

```json
{
  "type": "query",
  "content": {
    "text": "Help me build a web app",
    "resume": false,
    "files": ["/uploads/requirements.txt"]
  }
}
```

**Fields:**
- `text` (string): User message text
- `resume` (boolean): Whether to resume previous conversation
- `files` (array): Paths to files to include in context

---

#### Edit Query

Edits a previous query (for conversation editing/branching).

```json
{
  "type": "edit_query",
  "content": {
    "text": "Actually, make it a Python Flask app",
    "resume": false,
    "files": []
  }
}
```

---

#### Review Result

Provides feedback on agent's work for self-review loop.

```json
{
  "type": "review_result",
  "content": {
    "user_input": "Looks good, proceed"
  }
}
```

---

#### Enhance Prompt

Requests AI-powered prompt enhancement.

```json
{
  "type": "enhance_prompt",
  "content": {
    "model_name": "claude-sonnet-4-20250514",
    "text": "build web app",
    "files": []
  }
}
```

---

#### Interrupt

Stops the current agent execution.

```json
{
  "type": "interrupt"
}
```

---

### Server → Client Events

The server streams various event types back to the client during agent execution:

#### Agent Response Events

**Text Deltas:**
```json
{
  "type": "agent_response",
  "content": {
    "delta": "Partial response text..."
  }
}
```

**Tool Use:**
```json
{
  "type": "tool_use",
  "content": {
    "tool_name": "bash",
    "tool_input": {"command": "ls -la"},
    "tool_use_id": "toolu_123"
  }
}
```

**Tool Result:**
```json
{
  "type": "tool_result",
  "content": {
    "tool_use_id": "toolu_123",
    "output": "total 24\ndrwxr-xr-x ...",
    "is_error": false
  }
}
```

---

#### Status Events

**Agent Thinking:**
```json
{
  "type": "agent_thinking",
  "content": {
    "thinking": "I need to analyze the requirements..."
  }
}
```

**Error:**
```json
{
  "type": "error",
  "content": {
    "error": "API rate limit exceeded",
    "details": {...}
  }
}
```

**Session Info:**
```json
{
  "type": "session_info",
  "content": {
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "workspace_dir": "/workspace/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

## Static Files

### Workspace Files

**Endpoint:** `GET /workspace/{session_id}/{path}`

Serves static files from session workspaces.

**Example:**
```
GET /workspace/a1b2c3d4-e5f6-7890-abcd-ef1234567890/uploads/screenshot.png
```

**Response:** File content with appropriate MIME type

**Error Responses:**
- `404 Not Found`: File or workspace doesn't exist

---

## Error Handling

All API endpoints follow consistent error response patterns:

```json
{
  "error": "Error message description",
  "detail": "Additional error details"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

---

## Data Models

### SessionInfo

```typescript
{
  id: string;              // UUID
  workspace_dir: string;   // Filesystem path
  created_at: string;      // ISO 8601 timestamp
  device_id: string;       // Device identifier
  name: string;            // Optional session name
}
```

### EventInfo

```typescript
{
  id: string;              // UUID
  session_id: string;      // Session UUID
  timestamp: string;       // ISO 8601 timestamp
  event_type: string;      // Event type identifier
  event_payload: object;   // Event-specific data
  workspace_dir: string;   // Workspace path
}
```

### FileInfo

```typescript
{
  path: string;            // Filename or relative path
  content: string;         // Text content or base64 data URL
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Configure external rate limiting if deploying to production.

---

## CORS Configuration

CORS is enabled for all origins with:
- All HTTP methods allowed
- All headers allowed
- Credentials supported

**Production Note:** Restrict `allow_origins` to specific domains in production deployments.

---

## WebSocket Connection Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Initialize agent
  ws.send(JSON.stringify({
    type: 'init_agent',
    content: {
      model_name: 'claude-sonnet-4-20250514',
      tool_args: {},
      thinking_tokens: 0
    }
  }));

  // Send query
  ws.send(JSON.stringify({
    type: 'query',
    content: {
      text: 'Help me create a Python script',
      resume: false,
      files: []
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.content);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket connection closed');
};
```

---

## Environment Variables

Configure the backend using these environment variables:

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account JSON (for Vertex AI)
- `STATIC_FILE_BASE_URL`: Base URL for serving workspace files
- `HOST_WORKSPACE_PATH`: Local workspace directory (default: `~/.ii_agent/workspace`)
- `CODE_SERVER_PORT`: Port for code-server integration (default: 9000)

---

## Architecture Notes

- **Database**: SQLite with Alembic migrations (`data/sessions.db`)
- **Session Persistence**: Sessions and events are stored in the database
- **Workspace Management**: Each session has an isolated workspace directory
- **WebSocket Sessions**: Managed by `ConnectionManager` in `server/websocket/chat_session.py`
- **Event Streaming**: Real-time event streaming during agent execution

---

## See Also

- [Project README](../README.md)
- [Development Setup](../CLAUDE.md)
- [GAIA Benchmark](../run_gaia.py)
- [Running with Local Models](../RUNNING_WITH_LOCAL_MODELS.md)
