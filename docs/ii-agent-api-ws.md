# WebSocket Chat Interface Documentation

This document provides comprehensive guidance on connecting to the II-Agent WebSocket API and managing chat sessions.

## Overview

The II-Agent WebSocket API enables real-time, bidirectional communication with AI agents. The chat interface supports:

- Real-time agent responses with streaming
- Tool execution and result feedback
- File attachment support
- Session persistence across reconnections
- Multi-turn conversations with context management

## Connection Flow

The typical flow for starting a chat session:

1. **Connect** to WebSocket endpoint
2. **Receive** connection confirmation
3. **Initialize** agent with model configuration
4. **Wait** for agent initialization
5. **Send** queries and receive responses
6. **Handle** events (responses, tool use, errors)

---

## Python Examples

### Basic Chat Session

```python
import asyncio
import json
import websockets
from typing import Dict, Any

async def chat_session():
    """Basic example of connecting and chatting with II-Agent."""

    # Connect to WebSocket with device ID
    uri = "ws://localhost:8000/ws?device_id=my-python-client"

    async with websockets.connect(uri) as websocket:
        print("Connected to II-Agent")

        # Wait for connection confirmation
        response = await websocket.recv()
        event = json.loads(response)
        print(f"Connection: {event['type']}")
        print(f"Workspace: {event['content']['workspace_path']}")

        # Initialize the agent
        init_message = {
            "type": "init_agent",
            "content": {
                "model_name": "claude-sonnet-4-20250514",
                "tool_args": {},
                "thinking_tokens": 0
            }
        }
        await websocket.send(json.dumps(init_message))
        print("Initializing agent...")

        # Wait for agent initialization
        while True:
            response = await websocket.recv()
            event = json.loads(response)

            if event['type'] == 'AGENT_INITIALIZED':
                print("Agent ready!")
                print(f"VS Code URL: {event['content'].get('vscode_url', 'N/A')}")
                break
            elif event['type'] == 'ERROR':
                print(f"Error: {event['content']['message']}")
                return

        # Send a query
        query_message = {
            "type": "query",
            "content": {
                "text": "Create a simple Python script that prints 'Hello, World!'",
                "resume": False,
                "files": []
            }
        }
        await websocket.send(json.dumps(query_message))
        print("\nSent query, waiting for response...\n")

        # Listen for responses
        while True:
            response = await websocket.recv()
            event = json.loads(response)

            if event['type'] == 'agent_response':
                # Print agent text responses
                if 'delta' in event['content']:
                    print(event['content']['delta'], end='', flush=True)
                elif 'text' in event['content']:
                    print(event['content']['text'])

            elif event['type'] == 'tool_use':
                # Agent is using a tool
                tool_name = event['content']['tool_name']
                print(f"\n[Tool: {tool_name}]")

            elif event['type'] == 'tool_result':
                # Tool execution result
                output = event['content'].get('output', '')
                is_error = event['content'].get('is_error', False)
                if is_error:
                    print(f"[Error] {output}")
                else:
                    print(f"[Result] {output[:200]}...")  # Truncate long output

            elif event['type'] == 'STREAM_COMPLETE':
                # Agent finished responding
                print("\n\nAgent finished.")
                break

            elif event['type'] == 'ERROR':
                print(f"\nError: {event['content']['message']}")
                break

if __name__ == "__main__":
    asyncio.run(chat_session())
```

---

### Interactive Chat Loop

```python
import asyncio
import json
import websockets
from typing import Optional

class IIAgentClient:
    """Client for interacting with II-Agent WebSocket API."""

    def __init__(self, uri: str = "ws://localhost:8000/ws", device_id: str = "python-client"):
        self.uri = f"{uri}?device_id={device_id}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.workspace_path: Optional[str] = None

    async def connect(self):
        """Establish WebSocket connection."""
        self.websocket = await websockets.connect(self.uri)

        # Receive connection confirmation
        response = await self.websocket.recv()
        event = json.loads(response)

        if event['type'] == 'CONNECTION_ESTABLISHED':
            self.workspace_path = event['content']['workspace_path']
            print(f"✓ Connected to II-Agent")
            print(f"  Workspace: {self.workspace_path}")
            return True

        return False

    async def initialize_agent(self, model_name: str = "claude-sonnet-4-20250514",
                               thinking_tokens: int = 0, tool_args: dict = None):
        """Initialize the agent with specified model."""
        if not self.websocket:
            raise RuntimeError("Not connected. Call connect() first.")

        init_message = {
            "type": "init_agent",
            "content": {
                "model_name": model_name,
                "tool_args": tool_args or {},
                "thinking_tokens": thinking_tokens
            }
        }

        await self.websocket.send(json.dumps(init_message))

        # Wait for initialization
        while True:
            response = await self.websocket.recv()
            event = json.loads(response)

            if event['type'] == 'AGENT_INITIALIZED':
                print(f"✓ Agent initialized with {model_name}")
                return True
            elif event['type'] == 'ERROR':
                print(f"✗ Initialization error: {event['content']['message']}")
                return False

    async def send_query(self, text: str, files: list = None, resume: bool = False):
        """Send a query to the agent."""
        if not self.websocket:
            raise RuntimeError("Not connected.")

        query_message = {
            "type": "query",
            "content": {
                "text": text,
                "resume": resume,
                "files": files or []
            }
        }

        await self.websocket.send(json.dumps(query_message))

    async def listen_for_events(self, callback=None):
        """Listen for events from the agent.

        Args:
            callback: Optional function to handle events.
                     Should accept (event_type, content) as parameters.
        """
        if not self.websocket:
            raise RuntimeError("Not connected.")

        while True:
            try:
                response = await self.websocket.recv()
                event = json.loads(response)
                event_type = event['type']
                content = event['content']

                # Call custom callback if provided
                if callback:
                    should_continue = callback(event_type, content)
                    if should_continue is False:
                        break
                else:
                    # Default handler
                    if event_type == 'agent_response':
                        if 'delta' in content:
                            print(content['delta'], end='', flush=True)
                    elif event_type == 'STREAM_COMPLETE':
                        print("\n")
                        break
                    elif event_type == 'ERROR':
                        print(f"\nError: {content['message']}")
                        break

            except websockets.exceptions.ConnectionClosed:
                print("\nConnection closed")
                break

    async def cancel_query(self):
        """Cancel the current query execution."""
        if not self.websocket:
            raise RuntimeError("Not connected.")

        cancel_message = {"type": "cancel"}
        await self.websocket.send(json.dumps(cancel_message))

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None


async def interactive_chat():
    """Interactive chat loop with II-Agent."""
    client = IIAgentClient(device_id="interactive-client")

    # Connect and initialize
    await client.connect()
    await client.initialize_agent(model_name="claude-sonnet-4-20250514")

    print("\n" + "="*60)
    print("Interactive Chat with II-Agent")
    print("Type 'exit' to quit, 'cancel' to stop current query")
    print("="*60 + "\n")

    try:
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()

            if user_input.lower() == 'exit':
                print("Goodbye!")
                break

            if user_input.lower() == 'cancel':
                await client.cancel_query()
                print("Cancelled current query.")
                continue

            if not user_input:
                continue

            # Send query
            await client.send_query(user_input)

            print("\nAgent: ", end='', flush=True)

            # Listen for response
            await client.listen_for_events()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(interactive_chat())
```

---

### Advanced: Custom Event Handler

```python
import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any, List

class AdvancedAgentClient:
    """Advanced client with detailed event tracking."""

    def __init__(self, uri: str = "ws://localhost:8000/ws", device_id: str = "advanced-client"):
        self.uri = f"{uri}?device_id={device_id}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.event_log: List[Dict[str, Any]] = []
        self.tool_calls: List[Dict[str, Any]] = []

    async def connect_and_init(self, model_name: str = "claude-sonnet-4-20250514"):
        """Connect and initialize in one step."""
        self.websocket = await websockets.connect(self.uri)

        # Handle connection
        event = json.loads(await self.websocket.recv())
        self.log_event(event)

        # Initialize agent
        await self.websocket.send(json.dumps({
            "type": "init_agent",
            "content": {
                "model_name": model_name,
                "tool_args": {},
                "thinking_tokens": 0
            }
        }))

        # Wait for init confirmation
        while True:
            event = json.loads(await self.websocket.recv())
            self.log_event(event)

            if event['type'] in ['AGENT_INITIALIZED', 'ERROR']:
                break

        return event['type'] == 'AGENT_INITIALIZED'

    def log_event(self, event: Dict[str, Any]):
        """Log event with timestamp."""
        self.event_log.append({
            'timestamp': datetime.now().isoformat(),
            'type': event['type'],
            'content': event['content']
        })

    async def query_with_detailed_tracking(self, text: str):
        """Send query and track all events in detail."""
        # Send query
        await self.websocket.send(json.dumps({
            "type": "query",
            "content": {
                "text": text,
                "resume": False,
                "files": []
            }
        }))

        # Track response
        response_text = ""
        current_tool_call = None

        print(f"\n{'='*60}")
        print(f"Query: {text}")
        print(f"{'='*60}\n")

        while True:
            event = json.loads(await self.websocket.recv())
            self.log_event(event)

            event_type = event['type']
            content = event['content']

            if event_type == 'PROCESSING':
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {content['message']}")

            elif event_type == 'agent_response':
                if 'delta' in content:
                    response_text += content['delta']
                    print(content['delta'], end='', flush=True)

            elif event_type == 'agent_thinking':
                thinking = content.get('thinking', '')
                print(f"\n💭 Thinking: {thinking}\n")

            elif event_type == 'tool_use':
                current_tool_call = {
                    'tool_name': content['tool_name'],
                    'tool_use_id': content['tool_use_id'],
                    'input': content.get('tool_input', {}),
                    'start_time': datetime.now()
                }
                print(f"\n🔧 Using tool: {content['tool_name']}")
                print(f"   Input: {json.dumps(content.get('tool_input', {}), indent=2)}")

            elif event_type == 'tool_result':
                if current_tool_call:
                    current_tool_call['output'] = content.get('output', '')
                    current_tool_call['is_error'] = content.get('is_error', False)
                    current_tool_call['end_time'] = datetime.now()
                    self.tool_calls.append(current_tool_call)

                is_error = content.get('is_error', False)
                output = content.get('output', '')

                if is_error:
                    print(f"   ❌ Error: {output[:200]}")
                else:
                    print(f"   ✓ Result: {output[:200]}")

                current_tool_call = None

            elif event_type == 'STREAM_COMPLETE':
                print(f"\n\n{'='*60}")
                print(f"Query completed")
                print(f"{'='*60}\n")
                break

            elif event_type == 'ERROR':
                print(f"\n❌ Error: {content['message']}\n")
                break

        return response_text

    def print_summary(self):
        """Print summary of the session."""
        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(f"Total events: {len(self.event_log)}")
        print(f"Tool calls: {len(self.tool_calls)}")

        if self.tool_calls:
            print("\nTool Usage:")
            tool_usage = {}
            for call in self.tool_calls:
                tool_name = call['tool_name']
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1

            for tool_name, count in tool_usage.items():
                print(f"  - {tool_name}: {count} time(s)")

        print("="*60 + "\n")

    async def close(self):
        """Close connection."""
        if self.websocket:
            await self.websocket.close()


async def advanced_example():
    """Example using advanced client."""
    client = AdvancedAgentClient(device_id="advanced-example")

    try:
        # Connect and initialize
        success = await client.connect_and_init()

        if not success:
            print("Failed to initialize agent")
            return

        # Send a query
        await client.query_with_detailed_tracking(
            "Create a Python script that generates the first 10 Fibonacci numbers"
        )

        # Print session summary
        client.print_summary()

        # Optional: Save event log to file
        with open('session_log.json', 'w') as f:
            json.dump(client.event_log, f, indent=2)
        print("Event log saved to session_log.json")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(advanced_example())
```

---

### Working with File Attachments

```python
import asyncio
import json
import websockets
from pathlib import Path

async def chat_with_file_attachment():
    """Example of sending a query with file attachments."""

    uri = "ws://localhost:8000/ws?device_id=file-client"

    async with websockets.connect(uri) as websocket:
        # Connection handshake
        event = json.loads(await websocket.recv())
        print(f"Connected: {event['content']['workspace_path']}")

        # Initialize agent
        await websocket.send(json.dumps({
            "type": "init_agent",
            "content": {
                "model_name": "claude-sonnet-4-20250514",
                "tool_args": {},
                "thinking_tokens": 0
            }
        }))

        # Wait for init
        while True:
            event = json.loads(await websocket.recv())
            if event['type'] == 'AGENT_INITIALIZED':
                break

        print("Agent initialized")

        # First, upload a file using the REST API
        import requests

        # Read file content
        file_path = Path("example.txt")
        if not file_path.exists():
            # Create example file
            file_path.write_text("This is example content for the agent to analyze.")

        # Upload via REST API
        session_id = event['content'].get('session_id', 'your-session-id')
        upload_response = requests.post(
            "http://localhost:8000/api/upload",
            json={
                "session_id": session_id,
                "file": {
                    "path": file_path.name,
                    "content": file_path.read_text()
                }
            }
        )

        if upload_response.status_code == 200:
            uploaded_file_path = upload_response.json()['file']['path']
            print(f"File uploaded: {uploaded_file_path}")

            # Send query referencing the file
            await websocket.send(json.dumps({
                "type": "query",
                "content": {
                    "text": "Analyze the content of the uploaded file and summarize it",
                    "resume": False,
                    "files": [uploaded_file_path]
                }
            }))

            # Listen for response
            print("\nAgent response:")
            while True:
                event = json.loads(await websocket.recv())

                if event['type'] == 'agent_response' and 'delta' in event['content']:
                    print(event['content']['delta'], end='', flush=True)
                elif event['type'] == 'STREAM_COMPLETE':
                    print("\n")
                    break
                elif event['type'] == 'ERROR':
                    print(f"\nError: {event['content']['message']}")
                    break


if __name__ == "__main__":
    asyncio.run(chat_with_file_attachment())
```

---

### Resume Previous Conversation

```python
import asyncio
import json
import websockets

async def resume_conversation():
    """Example of resuming a previous conversation."""

    # Connect with an existing session UUID
    existing_session_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    uri = f"ws://localhost:8000/ws?device_id=resume-client&session_uuid={existing_session_id}"

    async with websockets.connect(uri) as websocket:
        # Connection
        event = json.loads(await websocket.recv())
        print(f"Reconnected to session: {existing_session_id}")

        # Initialize agent
        await websocket.send(json.dumps({
            "type": "init_agent",
            "content": {
                "model_name": "claude-sonnet-4-20250514",
                "tool_args": {},
                "thinking_tokens": 0
            }
        }))

        # Wait for init
        while True:
            event = json.loads(await websocket.recv())
            if event['type'] == 'AGENT_INITIALIZED':
                break

        print("Agent initialized with previous context")

        # Send query with resume=True to continue previous conversation
        await websocket.send(json.dumps({
            "type": "query",
            "content": {
                "text": "Continue from where we left off",
                "resume": True,  # This maintains conversation history
                "files": []
            }
        }))

        # Listen for response
        while True:
            event = json.loads(await websocket.recv())

            if event['type'] == 'agent_response' and 'delta' in event['content']:
                print(event['content']['delta'], end='', flush=True)
            elif event['type'] == 'STREAM_COMPLETE':
                print("\n")
                break


if __name__ == "__main__":
    asyncio.run(resume_conversation())
```

---

## WebSocket Message Reference

### Client → Server Messages

#### init_agent

Initialize the agent with a specific LLM model.

```python
{
    "type": "init_agent",
    "content": {
        "model_name": "claude-sonnet-4-20250514",  # Required
        "tool_args": {                              # Optional
            "enable_reviewer": False,
            "sequential_thinking": False
        },
        "thinking_tokens": 0                        # Optional (0 = disabled)
    }
}
```

**Model Names:**
- `claude-sonnet-4-20250514` (Anthropic)
- `gemini-2.0-flash-exp` (Google)
- `gpt-4` (OpenAI)
- See your settings for configured models

---

#### query

Send a user query to the agent.

```python
{
    "type": "query",
    "content": {
        "text": "Your question or task",  # Required
        "resume": False,                   # Continue previous conversation
        "files": [                         # Optional file attachments
            "/uploads/document.pdf",
            "/uploads/screenshot.png"
        ]
    }
}
```

---

#### cancel

Stop the current query execution.

```python
{
    "type": "cancel"
}
```

---

#### edit_query

Edit the previous query (rolls back to last user message).

```python
{
    "type": "edit_query",
    "content": {
        "text": "Revised question",
        "resume": False,
        "files": []
    }
}
```

---

#### enhance_prompt

Request AI-powered prompt enhancement.

```python
{
    "type": "enhance_prompt",
    "content": {
        "model_name": "claude-sonnet-4-20250514",
        "text": "build website",
        "files": []
    }
}
```

---

#### ping

Check connection status.

```python
{
    "type": "ping"
}
```

Server responds with `PONG` event.

---

### Server → Client Events

#### CONNECTION_ESTABLISHED

Sent immediately after WebSocket connection.

```python
{
    "type": "CONNECTION_ESTABLISHED",
    "content": {
        "message": "Connected to Agent WebSocket Server",
        "workspace_path": "/path/to/workspace/session-uuid"
    }
}
```

---

#### AGENT_INITIALIZED

Agent is ready to accept queries.

```python
{
    "type": "AGENT_INITIALIZED",
    "content": {
        "message": "Agent initialized",
        "vscode_url": "http://localhost:9000"  # If code-server enabled
    }
}
```

---

#### PROCESSING

Query is being processed.

```python
{
    "type": "PROCESSING",
    "content": {
        "message": "Processing your request..."
    }
}
```

---

#### agent_response

Agent text response (streamed as deltas or complete text).

```python
# Streaming delta
{
    "type": "agent_response",
    "content": {
        "delta": "partial text..."
    }
}

# Complete text
{
    "type": "agent_response",
    "content": {
        "text": "complete response text"
    }
}
```

---

#### agent_thinking

Extended thinking output (if thinking_tokens > 0).

```python
{
    "type": "agent_thinking",
    "content": {
        "thinking": "I need to analyze the requirements..."
    }
}
```

---

#### tool_use

Agent is invoking a tool.

```python
{
    "type": "tool_use",
    "content": {
        "tool_name": "bash",
        "tool_use_id": "toolu_abc123",
        "tool_input": {
            "command": "ls -la"
        }
    }
}
```

---

#### tool_result

Tool execution completed.

```python
{
    "type": "tool_result",
    "content": {
        "tool_use_id": "toolu_abc123",
        "output": "total 24\ndrwxr-xr-x...",
        "is_error": False
    }
}
```

---

#### STREAM_COMPLETE

Agent finished responding to the query.

```python
{
    "type": "STREAM_COMPLETE",
    "content": {}
}
```

---

#### ERROR

An error occurred.

```python
{
    "type": "ERROR",
    "content": {
        "message": "Error description"
    }
}
```

---

#### SYSTEM

System messages (e.g., reviewer status, commands).

```python
{
    "type": "SYSTEM",
    "content": {
        "message": "Query cancelled",
        "type": "reviewer_agent"  # Optional subtype
    }
}
```

---

#### PROMPT_GENERATED

Enhanced prompt result.

```python
{
    "type": "PROMPT_GENERATED",
    "content": {
        "result": "Enhanced, detailed prompt...",
        "original_request": "build website"
    }
}
```

---

## Slash Commands

Send these as regular queries (the server detects the `/` prefix).

- `/compact` - Summarize and compress conversation history
- `/help` - Show available commands

```python
await websocket.send(json.dumps({
    "type": "query",
    "content": {
        "text": "/compact",
        "resume": False,
        "files": []
    }
}))
```

---

## Connection Parameters

### Query Parameters

- `device_id` (required): Unique identifier for the client device
- `session_uuid` (optional): Resume a specific session by UUID

```python
# New session
uri = "ws://localhost:8000/ws?device_id=my-client"

# Resume existing session
uri = "ws://localhost:8000/ws?device_id=my-client&session_uuid=existing-uuid"
```

---

## Error Handling

### Connection Errors

```python
import websockets.exceptions

try:
    async with websockets.connect(uri) as websocket:
        # ... your code
        pass
except websockets.exceptions.ConnectionClosed:
    print("Connection closed unexpectedly")
except websockets.exceptions.WebSocketException as e:
    print(f"WebSocket error: {e}")
```

### Event Errors

Always check for `ERROR` event type:

```python
event = json.loads(await websocket.recv())

if event['type'] == 'ERROR':
    error_message = event['content']['message']
    print(f"Agent error: {error_message}")
    # Handle error appropriately
```

---

## Best Practices

### 1. Always Initialize Before Querying

```python
# ✓ Correct
await websocket.send(init_agent_message)
# Wait for AGENT_INITIALIZED
await websocket.send(query_message)

# ✗ Incorrect
await websocket.send(query_message)  # Will fail - agent not ready
```

### 2. Handle All Event Types

Don't assume only `agent_response` events. Handle:
- `tool_use` / `tool_result` for tool execution
- `ERROR` for failures
- `STREAM_COMPLETE` to know when agent is done

### 3. Use Structured Event Handling

```python
event_handlers = {
    'agent_response': handle_response,
    'tool_use': handle_tool_use,
    'tool_result': handle_tool_result,
    'ERROR': handle_error,
    'STREAM_COMPLETE': handle_complete
}

handler = event_handlers.get(event['type'], handle_unknown)
handler(event['content'])
```

### 4. Implement Reconnection Logic

```python
async def connect_with_retry(uri, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await websockets.connect(uri)
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### 5. Clean Up Resources

```python
try:
    async with websockets.connect(uri) as websocket:
        # Your code
        pass
finally:
    # Cleanup if needed
    pass
```

---

## Session Management

### Get Session History

Use the REST API to retrieve previous sessions:

```python
import requests

device_id = "my-client"
response = requests.get(f"http://localhost:8000/api/sessions/{device_id}")

sessions = response.json()['sessions']
for session in sessions:
    print(f"Session: {session['id']}")
    print(f"  Created: {session['created_at']}")
    print(f"  Name: {session['name']}")
```

### Get Session Events

```python
import requests

session_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
response = requests.get(f"http://localhost:8000/api/sessions/{session_id}/events")

events = response.json()['events']
for event in events:
    print(f"{event['timestamp']}: {event['event_type']}")
```

---

## Advanced Features

### Extended Thinking

Enable extended thinking for complex tasks:

```python
{
    "type": "init_agent",
    "content": {
        "model_name": "claude-sonnet-4-20250514",
        "thinking_tokens": 10000  # Enable thinking with 10k token budget
    }
}
```

The agent will emit `agent_thinking` events with its reasoning process.

### Reviewer Agent

Enable self-review for quality improvement:

```python
{
    "type": "init_agent",
    "content": {
        "model_name": "claude-sonnet-4-20250514",
        "tool_args": {
            "enable_reviewer": True
        }
    }
}
```

After completing a task, send a review request:

```python
{
    "type": "review_result",
    "content": {
        "user_input": "Please review and improve the output"
    }
}
```

---

## Troubleshooting

### "Agent not initialized" error

Make sure you send `init_agent` and wait for `AGENT_INITIALIZED` before sending queries.

### "A query is already being processed" error

Wait for `STREAM_COMPLETE` before sending another query, or send `cancel` first.

### Connection drops during long tasks

This is normal for very long-running tasks. Implement reconnection logic and use `session_uuid` to resume.

### Files not found

Files must be uploaded via the `/api/upload` endpoint first. The returned path should be used in the `files` array.

---

## See Also

- [API Documentation](API.md) - REST API reference
- [Project README](../README.md) - General project information
- [Development Guide](../CLAUDE.md) - Development setup and architecture
