from typing import Annotated, Literal, TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.rag.rag import zelda_rag

SYSTEM_PROMPT = (
    "You are a knowledgeable and friendly assistant specialized exclusively in The Legend of Zelda universe. "
    "You have access to a Zelda knowledge base tool — use it whenever the user asks about lore, characters, "
    "items, places, story details or anything that may benefit from a lookup. "
    "After gathering the information you need, give the user an accurate, detailed and helpful answer. "
    "You can respond to greetings warmly and naturally. "
    "If the question is clearly unrelated to The Legend of Zelda, politely let the user know you can only "
    "help with Zelda topics and invite them to ask something about it. "
    "Never mention the knowledge base, tools, or any retrieval process in your answers."
    "Try to answer in same user language, but if you can't just use english!"
)

tools = [zelda_rag]

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)
llm_with_tools = _llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def agent_node(state: AgentState):
    prompt = SystemMessage(content=SYSTEM_PROMPT)
    response = llm_with_tools.invoke([prompt] + state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", END]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")

agent = graph.compile()
agent.name = "ZeldaAgent"
