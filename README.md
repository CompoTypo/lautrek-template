# Lautrek Template

Forkable template for building Lautrek SaaS products with:
- **FastAPI server** with auth, billing, and rate limiting
- **Thin MCP adapter** that proxies to hosted server
- **SQLite + Litestream** for persistent data with S3 replication
- **DigitalOcean App Platform** deployment ready

## Quick Start

1. **Fork this repository**

2. **Search & replace:**
   - `productname` → your product name
   - `lt_` → your API key prefix (e.g., `cj_`, `eb_`)

3. **Install dependencies:**
   ```bash
   cd server && uv sync
   cd ../client && uv sync
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run development server:**
   ```bash
   make dev
   ```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Public Client (PyPI)                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  client/productname/mcp_server.py (~200 lines)          │    │
│  │  - Thin MCP adapter                                      │    │
│  │  - Proxies all calls to server API                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │ HTTPS + API Key                      │
│  ════════════════════════╪══════════════════════════════════    │
│                          ▼                                      │
│  Private Server (never publish)                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  server/src/                                             │    │
│  │  ├── api/main.py      - FastAPI app                      │    │
│  │  ├── auth/            - API keys, sessions, passwords    │    │
│  │  ├── billing/         - Rate limiting, usage tracking    │    │
│  │  ├── db/              - SQLite + migrations              │    │
│  │  └── core/            - YOUR PRODUCT LOGIC HERE          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Structure

```
lautrek-template/
├── client/                    # Public MCP adapter (publish to PyPI)
│   ├── productname/
│   │   └── mcp_server.py      # Thin adapter (~200 lines)
│   └── pyproject.toml
├── server/                    # Private backend (never publish)
│   ├── src/
│   │   ├── api/main.py        # FastAPI app
│   │   ├── auth/              # Authentication
│   │   ├── billing/           # Rate limiting
│   │   ├── db/                # Database
│   │   └── core/              # Product-specific logic
│   └── pyproject.toml
├── .do/app.yaml               # DigitalOcean deployment
├── .env.example               # Environment template
├── Makefile                   # Development commands
└── docker-compose.yml         # Local development
```

## Features

### Authentication
- API key generation with configurable prefix (`lt_`, `cj_`, etc.)
- Session-based auth for web UI
- Argon2id password hashing
- Device fingerprinting

### Billing
- Tier-based rate limiting (Free/Pro/Enterprise)
- Database-backed usage tracking
- Monthly operation limits
- Stripe integration ready

### Infrastructure
- SQLite with WAL mode
- Litestream replication to S3/DO Spaces
- Alembic migrations
- DigitalOcean App Platform deployment

## Commands

```bash
make dev         # Run development server
make test        # Run tests
make lint        # Run linter
make format      # Format code
make docker-dev  # Run with Docker
```

## Customization

See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for detailed instructions.

## License

MIT
