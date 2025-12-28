"""Thin MCP adapter that proxies tool calls to hosted server.

Environment:
    MCP_BACKEND_URL: Server URL (default: https://productname.lautrek.com)
    MCP_API_KEY: Your API key
    MCP_TIMEOUT: Request timeout (default: 60)
"""
import json
import logging
import os
import httpx
from mcp.server.fastmcp import FastMCP

BACKEND_URL = os.getenv("MCP_BACKEND_URL", "https://productname.lautrek.com")
API_KEY = os.getenv("MCP_API_KEY", "")
TIMEOUT = float(os.getenv("MCP_TIMEOUT", "60.0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP(name="productname", instructions="Product description and tools")
_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=TIMEOUT, headers={"X-API-Key": API_KEY})
    return _client


async def _call_api(endpoint: str, **params) -> str:
    client = await _get_client()
    try:
        response = await client.post(f"/api/v1/tools/{endpoint}", json=params)
        response.raise_for_status()
        return json.dumps(response.json(), indent=2)
    except Exception as e:
        logger.error(f"API error: {e}")
        return json.dumps({"status": "error", "error": str(e)}, indent=2)


@mcp.tool()
async def status() -> str:
    """Get server status and available tools."""
    return await _call_api("status")


@mcp.tool()
async def example_tool(param1: str, param2: int = 10) -> str:
    """Example tool - replace with your product tools.

    Args:
        param1: First parameter
        param2: Second parameter (default: 10)
    """
    return await _call_api("example-tool", param1=param1, param2=param2)


def main() -> None:
    if not API_KEY:
        logger.warning("MCP_API_KEY not set")
    logger.info(f"Starting MCP server -> {BACKEND_URL}")
    mcp.run()


if __name__ == "__main__":
    main()
