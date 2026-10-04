# Aurora Release Candidate

Status date: 2026-10-04

## Candidate

- Aurora plugin: **0.65.0**
- Scope: private/user while final public-site and submission work is pending
- Production MCP: `https://aurora-live-data.vercel.app/api/mcp`
- Aurora Live Data schema: **0.19.0**

## End-to-end checks completed

- ChatGPT successfully connects to the production MCP.
- `get_status` works from ChatGPT.
- `find_models` works from ChatGPT, including exact search for `gpt-6-astra`.
- `get_model` works from ChatGPT.
- `get_guidance` works from ChatGPT.
- `get_validation_policy` works from ChatGPT.
- Exact-model routing was corrected so a named model uses `get_model` directly after `get_status`.
- Unknown lifecycle state is not treated as proof that a verified model is unavailable.

Latest checked state:
- registry healthy: true
- sources: 21/21 reachable and fresh
- semantically verified models: 153
- verified prompting guidance rules: 13
- golden suite: pass
- deterministic benchmark: 17/17
- runtime acceptance: ready
- replay: ready
- migration: ready

## Infrastructure

- Vercel deployment: production-ready
- MCP implementation: native `mcp-handler` v2 / Streamable HTTP
- Authentication: none; public read-only data only
- MCP runtime errors during final test window: none
- GitHub MCP build CI: pass
- Vercel ignored-build rule: enabled so registry-only commits do not rebuild the MCP application

## Review package prepared

Aurora 0.65.0 contains:
- product metadata;
- English primary listing;
- French translation;
- release notes;
- exactly 5 positive review cases;
- exactly 3 negative review cases;
- production MCP endpoint;
- temporary HTTPS product/support/privacy/terms URLs.

Final review URLs:
- Product: `https://aurora.le-corre-alexis.fr/`
- Support: `https://aurora.le-corre-alexis.fr/support`
- Privacy: `https://aurora.le-corre-alexis.fr/privacy`
- Terms: `https://aurora.le-corre-alexis.fr/terms`
- Creator: `https://le-corre-alexis.fr/`

## Before public submission

The official Aurora URLs are now the final listing URLs.

Remaining steps:
1. run the 5 positive and 3 negative review cases against the exact final candidate;
2. complete developer/business identity requirements in the OpenAI submission portal;
3. connect and scan the production MCP;
4. complete the domain-verification challenge requested by OpenAI;
5. record and provide the reviewer-accessible demonstration video;
6. review policy attestations;
7. submit for public review.

## Release discipline

Do not add new Aurora infrastructure features before public-release preparation unless a final test exposes a blocker. Changes from this point should be limited to:
- bug fixes;
- factual/live-data correctness;
- submission compliance;
- official-site integration;
- documentation and presentation.
