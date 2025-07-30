# fastapi-template-SSE-Engine-MVC-

Using the Model View Controller Paradigm, State can be easily synchronized with the Dom Via Server Side Events and eventSource.onmessage

Idea based on datastar and fixi.js 

## Features

- **SSE-Driven DOM Updates**: Server queues HTML fragments that update specific DOM elements via EventSource
- **JavaScript Execution over SSE**: Execute JavaScript commands server-side via `{"js": {"exec": "code"}}` for enhanced control
- **HTMX Form Integration**: Declarative form handling with `hx-post` attributes that integrate seamlessly with SSE updates
- **Hypermedia-Compliant**: Server controls all client behavior through structured data messages, maintaining hypermedia principles
- **MVC Architecture**: Clean separation with FastAPI backend, Jinja2 templates, and class-based models

## How It Works

1. **Form Submission**: HTMX handles form posts declaratively with `hx-post="/add_post"`
2. **Server Processing**: Backend processes form data, updates model state, queues multiple SSE updates
3. **Dual SSE Messages**: Server sends HTML updates followed by JavaScript execution commands
4. **Client SSE Handler**: EventSource processes both `html` updates (DOM replacement) and `js` updates (variable assignment or code execution)

## SSE Message Types

The SSE handler processes structured JSON messages to control client behavior:

| Message Type | Format | Example | Description |
|--------------|--------|---------|-------------|
| **HTML Update** | `{"html": {"elementId": "htmlContent"}}` | `{"html": {"posts": "<li>New post</li>"}}` | Replaces DOM element content by ID |
| **JS Variable** | `{"js": {"varName": value}}` | `{"js": {"userCount": 42}}` | Sets `window.varName = value` |
| **JS Execution** | `{"js": {"exec": "code"}}` | `{"js": {"exec": "alert('Hello!')"}}` | Executes JavaScript code |

Multiple messages can be sent in sequence from a single endpoint, allowing complex client orchestration like updating multiple DOM elements followed by form resets or notifications.

The SSE message handler supports two JavaScript patterns: `{"js": {"varName": value}}` for setting window variables, and `{"js": {"exec": "code"}}` for executing JavaScript commands. This pairs beautifully with HTMX's SSE plugin, providing excellent locality of behavior where server-sent messages directly control specific client actions. The approach maintains hypermedia compliance by having the server orchestrate all client-side behavior through structured data rather than requiring complex client-side logic.

<img src="https://raw.githubusercontent.com/RetributionByRevenue/fastapi-template-SSE-Engine-MVC-/refs/heads/main/screenshot.gif">
