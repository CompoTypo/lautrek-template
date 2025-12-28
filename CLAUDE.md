# CLAUDE.md

This is a Lautrek product template. See README.md for setup.

## Quick Reference

```bash
make dev    # Run dev server on :8080
make test   # Run tests
make lint   # Check code style
```

## Architecture

- `server/src/api/main.py` - FastAPI app
- `server/src/auth/` - Authentication (API keys, sessions)
- `server/src/billing/` - Rate limiting by tier
- `server/src/db/` - SQLite database
- `client/productname/mcp_server.py` - Thin MCP adapter

## Adding Tools

1. Add endpoint in `server/src/api/main.py`
2. Add corresponding tool in `client/productname/mcp_server.py`
3. Both should have matching names and parameters

## Environment

Copy `.env.example` to `.env` and configure:
- `API_KEY_PREFIX` - Your product prefix (e.g., `cj_`)
- `MCP_BACKEND_URL` - Server URL for MCP adapter
- `MCP_API_KEY` - API key for MCP adapter
