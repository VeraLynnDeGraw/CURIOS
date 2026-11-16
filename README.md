# CURIOS

A small, local-first AI chat room for connecting to AI providers through APIs.

## Initial scope

- Local browser interface with a Python standard-library backend.
- OpenAI-compatible API connections (including local Ollama endpoints).
- Provider settings and API keys stored locally in `~/.config/curios/providers.json`.
- Explicit ONLINE / OFFLINE control; CURIOS starts OFFLINE.
- No cloud account, database, telemetry, or autostart.
- The server starts only when you launch CURIOS and stops when you press `Ctrl+C`.
- CURIOS only terminates the browser process it launched itself.

> This is an initial foundation, not a security-hardened multi-user service. Keep it bound to
> `127.0.0.1`; do not expose it to your network. API keys are stored in a local file with
> owner-only permissions, not encrypted by this starter version.

## Requirements

- Linux
- Python 3.10+
- Firefox or Chromium/Chrome (optional; if none is detected, open the URL manually)

No third-party Python packages are required.

## Run

From the extracted project directory:

```bash
python -m curios
```

CURIOS will start its local server and try to open a dedicated browser window/profile.
Press `Ctrl+C` in the terminal to stop the server and close the browser process CURIOS started.

If the browser does not open automatically, visit:

```text
http://127.0.0.1:8765
```

## Configure a provider

In the chat interface, open **Connections** and add:

- A display name, e.g. `Ollama` or `My API`
- An API base URL
- A model name
- An API key (optional for local Ollama)

Examples:

| Service | Base URL | Example model |
|---|---|---|
| Ollama | `http://127.0.0.1:11434/v1` | `qwen2.5:latest` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Other OpenAI-compatible service | Its documented `/v1` base URL | Provider's model ID |

CURIOS currently supports the OpenAI-compatible Chat Completions format. Anthropic and
Gemini need separate provider adapters and are not included yet.

## Important behavior

- CURIOS makes API requests only after you select a configured provider and send a message.
- A local Ollama connection stays local to your machine.
- Remote API providers receive the messages you send them, according to their own policies.
- Conversation messages remain in the current browser tab only; this version does not persist chat history.
- The browser profile is stored under `~/.local/share/curios/browser-profile`.
- The provider configuration is stored under `~/.config/curios/providers.json`.
- To remove saved provider credentials, use **Connections → Remove**, or delete that file while CURIOS is stopped.

## Project layout

```text
CURIOS/
├── curios/
│   ├── __init__.py
│   ├── __main__.py
│   ├── network.py
│   ├── providers.py
│   └── server.py
├── web/
│   ├── index.html
│   ├── app.css
│   └── app.js
├── curios-menu.sh
├── commands.txt
├── .gitignore
├── LICENSE
└── README.md
```
