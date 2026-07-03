# Agentic Code Assistant

A simple learning project for experimenting with agentic AI workflows in Python.

The project exposes a FastAPI server with two code-assistant workflows:

1. **Code Review Agent** — reviews Python code and can use tools to read or save local project files.
2. **Multi-Agent Code Generator** — uses a coder/auditor loop where one agent writes code and another agent audits it for bugs, security issues, and edge cases.

The goal of this project is to practice building small agentic systems with API endpoints, tool calling, structured model responses, authentication, logging, and local testing.

---

## Features

* FastAPI-based backend API
* Bearer-token authentication
* Console-based test client
* Single-agent code review workflow
* Tool-enabled agent with local file read/write tools
* Multi-agent coder/auditor workflow
* Structured audit output using Pydantic schemas
* Environment-based configuration with `.env`
* Lazy imports and lazy client initialization to keep server startup lightweight

---

## Project Structure

```text
apps/
├── main.py                  # FastAPI app entry point
├── router.py                # API router registration
├── code_endpoints.py        # /code/review and /code/generate endpoints
├── agent_with_tools.py      # Single code-review agent with tools
├── multi_agent_system.py    # Coder/auditor multi-agent workflow
├── test_request.py          # Console client for testing API requests
├── config.py                # Logging configuration
└── .env                     # Local environment variables
```

---

## Workflows

### 1. Code Review Agent

The review workflow accepts Python code or a file-related instruction and sends it to a code-review agent.

The agent can use local tools such as:

* `read_local_file`
* `save_local_file`

This allows the agent to inspect files inside the project directory and optionally save refactored output.

Endpoint:

```text
POST /code/review
```

Example payload:

```json
{
  "review_content": "def div(a: int, b: int):\n    return a / b"
}
```

---

### 2. Multi-Agent Code Generator

The generation workflow uses two agent roles:

* **Coder** — writes Python code based on the user request.
* **Auditor** — reviews the generated code for bugs, edge cases, security issues, and quality concerns.

The agents communicate through a shared message ledger. The loop continues until the auditor passes the code or the maximum number of rounds is reached.

Endpoint:

```text
POST /code/generate
```

Example payload:

```json
{
  "generate_rounds": 3,
  "generate_content": "Create a Python function to merge overlapping intervals."
}
```

---

## Requirements

* Python 3.11+
* FastAPI
* Uvicorn
* Requests
* Pydantic
* python-dotenv
* Google GenAI SDK
* uv package manager

---

## Environment Variables

Create a `.env` file in the project root or app directory:

```env
API_TOKEN=your-local-api-token
GEMINI_API_KEY=your-gemini-api-key
PROJECT_PATH=/absolute/path/to/your/project
```

### Variable descriptions

| Variable         | Purpose                                                |
| ---------------- | ------------------------------------------------------ |
| `API_TOKEN`      | Bearer token used to protect the FastAPI endpoints     |
| `GEMINI_API_KEY` | API key used by the Gemini model client                |
| `PROJECT_PATH`   | Root directory allowed for local file read/write tools |

Do not commit `.env` files or real API keys to version control.

---

## Running the Server

From the `apps` directory:

```bash
uv run uvicorn main:code_app --host 127.0.0.1 --port 8000 --log-level debug
```

During development, you can also use reload mode:

```bash
uv run uvicorn main:code_app --reload --log-level debug
```

If reload mode behaves unexpectedly, run without `--reload` and restart the server manually.

---

## Testing with the Console Client

Start the server first, then run:

```bash
uv run python test_request.py
```

The script prompts for one of two modes:

```text
R = code review
G = code generation
```

For code review, enter code and finish input with:

```text
END
```

Example:

```text
Enter 'R' for code review or 'G' for code generation: R
def div(a: int, b: int):
    return a / b
END
```

---

## API Authentication

All `/code/...` endpoints require a Bearer token.

Example request:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"review_content": "def div(a: int, b: int):\n    return a / b"}' \
  http://localhost:8000/code/review
```

---

## Learning Goals

This project is intended to demonstrate practical understanding of:

* FastAPI route design
* API authentication
* Environment-based configuration
* Agent loops
* Tool calling
* Structured LLM output
* Error handling
* Logging
* Local development/debugging workflow
* Separating API startup from expensive runtime dependencies
