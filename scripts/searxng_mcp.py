
from mcp.server.fastmcp import FastMCP
import httpx
import os

# Initialize FastMCP Server
mcp = FastMCP("SearXNG Search")

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://127.0.0.1:8080")

@mcp.tool()
async def search_web(query: str, num_results: int = 5) -> str:
    """
    Search the web using a local SearXNG instance.
    Use this tool to find information about current events, facts, or general knowledge.
    
    Args:
        query: The search query string.
        num_results: Number of results to return (default: 5).
    """
    url = f"{SEARXNG_URL}/search"
    params = {
        "q": query,
        "format": "json",
        "safesearch": 1,
        "language": "pt-BR"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])[:num_results]
            
            if not results:
                return "No results found."

            formatted_results = []
            for i, res in enumerate(results, 1):
                title = res.get("title", "No Title")
                link = res.get("url", "#")
                content = res.get("content", "No description available.")
                formatted_results.append(f"{i}. [{title}]({link})\n   {content}")
            
            return "\n\n".join(formatted_results)

        except Exception as e:
            return f"Error searching SearXNG: {str(e)}"

if __name__ == "__main__":
    mcp.run()
