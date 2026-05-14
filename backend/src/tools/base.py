from langchain_core.tools import tool


@tool
def search_knowledge(query: str) -> str:
    """Search the internal knowledge base for relevant information."""
    return f"No results found for: {query}"
