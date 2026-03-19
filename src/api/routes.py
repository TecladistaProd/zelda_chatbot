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


async def chat_stream(request: ChatRequest):
    history = session_store.get_history(request.session_id)
    messages = history + [HumanMessage(content=request.message)]

    yield await sse_event("progress", "Summoning Zelda wisdom...")

    full_messages = messages.copy()

    try:
        async for event in agent.astream_events({"messages": messages}, version="v2"):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_tool_start":
                tool_name = event.get("name", "tool")
                yield await sse_event("token", f"\n\n*Using tool: {tool_name}...*\n\n")

            elif kind == "on_tool_end":
                yield await sse_event("token", f"\n\n*Done with: {name}*\n\n")

            elif kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and chunk.content:
                    content = chunk.content
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                yield await sse_event("token", block["text"])
                    elif isinstance(content, str):
                        yield await sse_event("token", content)

            elif kind == "on_chain_end" and name == "ZeldaAgent":
                output = event["data"].get("output", {})
                full_messages = output.get("messages", full_messages)

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
