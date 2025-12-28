# Customization Guide

## 1. Rename the Product

Search and replace these strings:

- `productname` → your product name (lowercase, no spaces)
- `lt_` → your API key prefix (e.g., `cj_`, `eb_`)
- `Lautrek Product` → your product display name

## 2. Add Your Tools

### Server Side (`server/src/api/main.py`)

```python
class MyToolRequest(BaseModel):
    param1: str
    param2: int = 10

@app.post("/api/v1/tools/my-tool")
async def my_tool(
    body: MyToolRequest,
    user: APIKeyInfo = Depends(require_auth),
    usage: UsageInfo = Depends(require_rate_limit),
):
    # Your business logic here
    result = do_something(body.param1, body.param2)
    return {"status": "success", "result": result}
```

### Client Side (`client/productname/mcp_server.py`)

```python
@mcp.tool()
async def my_tool(param1: str, param2: int = 10) -> str:
    """My tool description.

    Args:
        param1: First parameter
        param2: Second parameter
    """
    return await _call_api("my-tool", param1=param1, param2=param2)
```

## 3. Configure Stripe

1. Create products in Stripe Dashboard
2. Add price IDs to `.env`:
   ```
   STRIPE_PRICE_FREE_MONTHLY=price_xxx
   STRIPE_PRICE_PRO_MONTHLY=price_yyy
   ```

## 4. Deploy

### DigitalOcean App Platform

1. Update `.do/app.yaml` with your repo
2. Run: `doctl apps create --spec .do/app.yaml`
3. Set secrets in DO dashboard

### Custom Domain

1. Add CNAME record pointing to your app URL
2. Configure domain in DO App Platform
