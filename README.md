# Chat Zelda

A conversational AI chatbot specialized in The Legend of Zelda universe. Ask about characters, lore, timelines, items, places, games — and get accurate, streaming answers powered by a LangGraph ReAct agent with RAG retrieval.

---

## Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — API server and static file serving
- [LangGraph](https://langchain-ai.github.io/langgraph/) — agent graph with ReAct loop (agent → tools → agent)
- [LangChain Anthropic](https://python.langchain.com/docs/integrations/chat/anthropic/) — `claude-haiku-4-5` as the LLM
- [FAISS](https://github.com/facebookresearch/faiss) + [HuggingFace Embeddings](https://huggingface.co/) — local vector store for RAG (`sentence-transformers/all-MiniLM-L6-v2`)
- [langdetect](https://github.com/Mimino666/langdetect) — detects the user's language and instructs the agent to reply in kind
- [Uvicorn](https://www.uvicorn.org/) — ASGI server

**Frontend**
- [Alpine.js](https://alpinejs.dev/) — reactive UI without a build step
- [marked.js](https://marked.js.org/) — renders markdown responses in the chat
- [Font Awesome](https://fontawesome.com/) — icons
- Vanilla CSS with Zelda BOTW/TOTK color palette, dark and light themes

---

## How it works

1. The user sends a message via the chat UI
2. The frontend opens a `POST /api/chat` request and reads the response as a **Server-Sent Events (SSE)** stream
3. The backend runs a **LangGraph ReAct agent**:
   - Detects the user's language with `langdetect` and injects a language instruction into the system prompt
   - Decides whether to call the `zelda_rag` tool (FAISS similarity search over local `.md` and `.txt` knowledge files)
   - If tools are called, results are fed back and the agent loops until it has enough to answer
   - Streams the final answer token by token back to the client
4. Each browser session gets its own message history with a 30-minute TTL — no history survives a page reload or expiry

---

## Project structure

```
chat_zelda/
├── main.py                  # FastAPI app, lifespan, static mount
├── Makefile                 # dev and start scripts
├── requirements.txt
├── .env                     # secrets (not committed)
├── .env.example
├── static/
│   ├── index.html
│   ├── script.js            # Alpine.js app, SSE consumer
│   └── style.css            # Zelda-themed, dark/light
└── src/
    ├── agent/
    │   ├── agent.py         # LangGraph StateGraph, ReAct node, language detection
    │   └── session.py       # TTL session store with background cleanup
    ├── api/
    │   └── routes.py        # POST /api/chat SSE endpoint
    ├── core/
    │   └── config.py        # Pydantic Settings
    ├── data/
    │   ├── characters.md    # Zelda character lore
    │   └── games.txt        # Game summaries
    └── rag/
        └── rag.py           # FAISS vectorstore, zelda_rag tool
```

---

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup and running

**1. Clone the repository**

```bash
git clone https://github.com/your-username/chat_zelda.git
cd chat_zelda
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

```bash
cp .env.example .env
```

Open `.env` and fill in your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

**5. Run**

Development mode (auto-reload):

```bash
make dev
```

Production mode:

```bash
make start
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

> The RAG vectorstore is built in-process on first request from the files inside `src/data/`. No external database required.

---

## Adding knowledge

Drop any `.md` or `.txt` files into `src/data/`. They are automatically picked up and indexed when the server starts. Markdown files are split by heading sections; plain text files are chunked with a recursive splitter.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send a message, receive SSE stream |
| `GET` | `/api/health` | Health check |

**Request body**

```json
{
  "session_id": "session_...",
  "message": "Who is Midna?"
}
```

**SSE event types**

| Event | Description |
|-------|-------------|
| `progress` | Status messages (thinking, searching archives) |
| `token` | Streamed answer chunk |
| `done` | Stream finished |
| `error` | Something went wrong |
