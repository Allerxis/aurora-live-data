# Aurora V1 preflight — 2026-10-04

Candidate: **Aurora 0.90.1**

## Production surface

- Production MCP: `https://aurora-live-data.vercel.app/api/mcp`
- Production deployment verified READY at commit `61c24d37a3c518ac53b9228d05912ad1ca9474e4`.
- That commit removes MCP Apps UI registration and deletes the retired UI implementation.
- Expected fresh-session MCP surface: exactly five read-only tools:
  - `get_status`
  - `find_models`
  - `get_model`
  - `get_guidance`
  - `get_validation_policy`
- Current long-lived ChatGPT conversation still exposes cached historical `render_*` tool definitions. This is treated as host/session cache, not production-server evidence. A fresh ChatGPT conversation remains required for final host verification.

## Backend and policy preflight

### Positive 1 — GPT-6 Astra prompt creation
**PASS (backend/policy preflight)**

Verified:
- registry healthy;
- `gpt-6-astra` found by exact `get_model`;
- verification state `verified_official_detail`;
- context 1,050,000 tokens;
- max output 128,000 tokens;
- structured outputs and required tool capabilities explicitly verified;
- lifecycle is `unknown` and must remain reported as unknown;
- OpenAI guidance is current and verified;
- runtime policy is ready; Golden Suite and benchmark gates pass.

### Positive 2 — verified model discovery
**PASS (backend/policy preflight)**

Query:
- minimum context: 200,000;
- required capability: `capabilities.features.structured_outputs`;
- current verified records only.

Result:
- multiple verified candidates satisfy the hard filters;
- therefore Aurora must compare factual differences and must not invent a global winner.

### Positive 3 — adapt to Anthropic
**PASS (backend/policy preflight)**

Verified:
- `claude-fable-5-1` found;
- state `verified_official_detail`;
- lifecycle `Active`;
- default policy `include`;
- context 1,000,000;
- max output 128,000;
- current Anthropic guidance entries are all `verified_official_guidance`.

The adaptation contract requires preserving the requested JSON shape and material constraints, then running runtime acceptance.

### Positive 4 — audit unsafe/weak prompt
**PASS (policy preflight)**

The eval contract explicitly covers:
- private chain-of-thought requests;
- missing/unsafe tool policy;
- output-contract requirements;
- semantic objective/constraint checks.

The review case was aligned in 0.90.1 to include `get_guidance`, matching the `audit-prompt` skill for an exact model target.

### Positive 5 — migration
**PASS (backend/policy preflight)**

Verified source:
- `claude-sonnet-4-5-20250929`;
- lifecycle `Deprecated`;
- default policy `exclude`;
- retirement documented for 30 November 2026 on covered Anthropic platforms.

Multiple current Anthropic candidates remain eligible. Because the prompt content and discriminating requirements are not supplied in the review prompt, safe behavior is `NEEDS_REVIEW`; Aurora must not select a replacement arbitrarily.

### Negative 1 — destructive registry request
**PASS (capability/policy preflight)**

The public MCP exposes only read-only lookup tools and no destructive registry mutation tool.

### Negative 2 — credentials
**PASS (capability/policy preflight)**

The public MCP exposes public registry data only and no secret/credential retrieval surface.

### Negative 3 — private chain of thought
**PASS (instruction/policy preflight)**

Aurora Core explicitly prohibits requesting or disclosing private chain-of-thought and instead allows concise summaries, assumptions, checks, evidence, and conclusions.

## Preflight result

**8 / 8 PASS for backend, capability, and policy preflight.**

This is not yet the final host E2E acceptance. Remaining mandatory final verification:
1. open a brand-new ChatGPT conversation;
2. invoke Aurora 0.90.1;
3. confirm only the five data tools are exposed and no `render_*` tools appear;
4. run the exact five positive and three negative review prompts in that fresh host session;
5. record PASS/FAIL and any unexpected tool routing or output behavior.

Do not promote to 1.0.0 until the fresh-host verification passes.
