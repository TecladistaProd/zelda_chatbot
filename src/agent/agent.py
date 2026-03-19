from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode

from src.rag.rag import zelda_rag

SYSTEM_PROMPT = (
    "You are a helpful assistant specialized exclusively in The Legend of Zelda universe. "
    "You can respond to greetings and casual conversation naturally. "
    "However, if the user asks about anything unrelated to The Legend of Zelda — such as other games, "
    "general knowledge, coding, or any other topic — politely let them know that you can only help "
    "with questions about The Legend of Zelda, and invite them to ask something about it."
)

tools = [zelda_rag]

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.2,
    max_retries=3
)
llm_with_tools = llm.bind_tools(tools)


def call_model(state: MessagesState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["tools", END]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(tools)

graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("tools", tool_node)
graph.add_edge(START, "model")
graph.add_conditional_edges("model", should_continue)
graph.add_edge("tools", "model")

agent = graph.compile()
agent.name = "ZeldaAgent"
