# Aurora Live Data MCP

Read-only MCP server for Aurora, deployed from this directory on Vercel.

## Endpoint

`/api/mcp`

## Authentication

None. The server exposes only public Aurora Live Data already published in this repository.

## Tools

- `get_status`
- `find_models`
- `get_model`
- `get_guidance`
- `get_validation_policy`

## Deployment

Configure the Vercel project's Root Directory to `mcp-server`. The implementation uses Vercel's `mcp-handler` package with Streamable HTTP support.
