from langchain.tools import tool
from langchain_tavily import TavilySearch

_tavily = TavilySearch(max_results=4, topic="general")


@tool
def internet_search(query: str) -> str:
    """Search the internet for up-to-date information. Use this when the knowledge base does not have the answer or when recent/external information is needed."""
    print("Searching into internet")
    response = _tavily.invoke({"query": query})
    results = response.get("results", [])
    if not results:
        return "No results found."

    parts = []
    sources = []

    for item in results:
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("url", "")

        parts.append(f"**{title}**\n{content}")
        if url:
            sources.append(f"- [{title}]({url})" if title else f"- {url}")

    output = "\n\n".join(parts)
    if sources:
        output += "\n\n**Sources:**\n" + "\n".join(sources)

    return output
