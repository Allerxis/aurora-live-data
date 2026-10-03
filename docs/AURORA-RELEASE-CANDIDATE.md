# Aurora Release Candidate

Status date: 2026-10-03

## Candidate

- Aurora plugin: **0.62.0**
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

Aurora 0.61.0 contains:
- product metadata;
- English primary listing;
- French translation;
- release notes;
- exactly 5 positive review cases;
- exactly 3 negative review cases;
- production MCP endpoint;
- temporary HTTPS product/support/privacy/terms URLs.

Temporary review URLs:
- Product: `https://aurora-live-data.vercel.app/`
- Support: `https://aurora-live-data.vercel.app/support`
- Privacy: `https://aurora-live-data.vercel.app/privacy`
- Terms: `https://aurora-live-data.vercel.app/terms`

## Before public submission

The existing official Aurora website should be updated first:

`https://aurora.le-corre-alexis.fr/`

After that update:
1. replace the temporary Vercel listing URLs with the official Aurora website URLs;
2. run the 5 positive and 3 negative review cases in the final public candidate;
3. complete developer/business identity requirements in the OpenAI submission portal;
4. connect and scan the production MCP;
5. complete the domain-verification challenge requested by OpenAI;
6. record and provide the reviewer-accessible demonstration video;
7. review policy attestations;
8. submit for public review.

## Release discipline

Do not add new Aurora infrastructure features before public-release preparation unless a final test exposes a blocker. Changes from this point should be limited to:
- bug fixes;
- factual/live-data correctness;
- submission compliance;
- official-site integration;
- documentation and presentation.


## Interactive MCP Apps UI

Aurora 0.62.0 adds four optional ChatGPT-compatible MCP Apps surfaces while keeping the five data tools independent from presentation:

- `render_live_data_status` — Live Data health/readiness dashboard.
- `render_model_comparison` — factual side-by-side comparison for 2–4 verified models.
- `render_validation_report` — PASS / NEEDS_REVIEW / FAIL report with criterion details and repair actions.
- `render_migration_plan` — migration status, compatible candidates, warnings and target-selection actions.

The resources are versioned under:
- `ui://aurora/status/v1.html`
- `ui://aurora/model-comparison/v1.html`
- `ui://aurora/validation-report/v1.html`
- `ui://aurora/migration-plan/v1.html`

The UI layer is presentation-only. It does not replace Aurora Live Data facts, eval policies, runtime gates, or migration logic. If a host does not render MCP Apps, Aurora must still return the equivalent result in normal chat text.
