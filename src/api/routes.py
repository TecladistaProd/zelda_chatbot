import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent.agent import agent
from src.agent.session import session_store

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    session_id: str
    message: str


async def sse_event(event: str, text: str) -> str:
    return f"event: {event}\ndata: {json.dumps({'text': text})}\n\n"

def handle_text(is_used_tools: bool, text: str) -> str:
    if is_used_tools:
        return f"\n{text}"
    return text

async def chat_stream(request: ChatRequest):
    history = session_store.get_history(request.session_id)
    messages = history + [HumanMessage(content=request.message)]

    yield await sse_event("progress", "Thinking...")

    full_messages = messages.copy()
    used_tools = False
    try:
        async for event in agent.astream_events({"messages": messages}, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_tool_start":
                tool_input = event.get("data", {}).get("input", {})
                query = tool_input.get("query", name) if isinstance(tool_input, dict) else name
                used_tools = True
                yield await sse_event("progress", f"*Searching the Zelda archives: \"{query}\"...*\n\n")

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    content = chunk.content
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = handle_text(used_tools, block["text"])
                                used_tools = False
                                yield await sse_event("token", text)
                    elif isinstance(content, str):
                        text = handle_text(used_tools, content)
                        used_tools = False
                        yield await sse_event("token", text)

            elif kind == "on_chain_end" and name == "ZeldaAgent":
                output = event["data"].get("output", {})
                full_messages = output.get("messages", full_messages)
                used_tools = False

        session_store.update_history(request.session_id, full_messages)
        yield await sse_event("done", "")

    except Exception as e:
        yield await sse_event("error", str(e))


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(chat_stream(request), media_type="text/event-stream")
