import { createMcpHandler } from 'mcp-handler';
import { registerAuroraUi } from '../../../lib/ui-tools';
import { z } from 'zod';
import {
  POLICY_NAMES,
  PROVIDERS,
  explicitlySupported,
  fetchRegistry,
  getPath,
  jsonText,
} from '../../../lib/registry';

export const runtime = 'nodejs';
export const maxDuration = 60;

const providerSchema = z.enum(PROVIDERS);
const policySchema = z.enum(POLICY_NAMES);
const defaultPolicySchema = z.enum([
  'include',
  'include_with_warning',
  'specialized',
  'exclude',
  'stale',
]);

const handler = createMcpHandler(
  (server) => {
    registerAuroraUi(server);
    server.registerTool(
      'get_status',
      {
        title: 'Get Aurora Live Data status',
        annotations: {
          readOnlyHint: true,
          destructiveHint: false,
          openWorldHint: true,
          idempotentHint: true,
        },
        description:
          'Read Aurora Live Data health, freshness, coverage counters, validation gates, and policy hashes. Use this first for volatile Aurora model or prompt-engineering questions.',
        inputSchema: z.object({}),
      },
      async () => {
        const status = await fetchRegistry('status.json');
        return jsonText(status);
      },
    );

    server.registerTool(
      'find_models',
      {
        title: 'Find verified AI models',
        annotations: {
          readOnlyHint: true,
          destructiveHint: false,
          openWorldHint: true,
          idempotentHint: true,
        },
        description:
          'Search the current verified Aurora model selector. Missing or null facts mean unknown, never unsupported. Use only constraints that materially matter to the user task.',
        inputSchema: z.object({
          provider_slug: providerSchema.optional(),
          query: z.string().optional(),
          default_policies: z.array(defaultPolicySchema).optional(),
          min_context_tokens: z.number().int().positive().optional(),
          min_output_tokens: z.number().int().positive().optional(),
          required_capabilities: z.array(z.string()).optional(),
          only_current_verified: z.boolean().default(true),
          limit: z.number().int().min(1).max(50).default(20),
        }),
      },
      async ({
        provider_slug,
        query,
        default_policies,
        min_context_tokens,
        min_output_tokens,
        required_capabilities,
        only_current_verified,
        limit,
      }) => {
        const selector = await fetchRegistry<{
          generated_at?: string;
          models?: Array<Record<string, unknown>>;
        }>('selector.json');

        const provider = provider_slug?.toLowerCase() ?? null;
        const needle = query?.trim().toLowerCase() ?? '';
        const policies = default_policies
          ? new Set(default_policies)
          : null;

        const models = (selector.models ?? [])
          .filter((model) => {
            if (
              provider &&
              String(model.provider_slug ?? '').toLowerCase() !== provider
            ) {
              return false;
            }

            if (needle) {
              const haystack = (
                String(model.model_key ?? '') +
                ' ' +
                String(model.display_name ?? '')
              ).toLowerCase();

              if (!haystack.includes(needle)) return false;
            }

            if (
              policies &&
              !policies.has(
                String(model.default_policy ?? '') as
                  | 'include'
                  | 'include_with_warning'
                  | 'specialized'
                  | 'exclude'
                  | 'stale',
              )
            ) {
              return false;
            }

            if (
              only_current_verified &&
              model.verification_state !== 'verified_official_detail'
            ) {
              return false;
            }

            if (min_context_tokens !== undefined) {
              if (
                typeof model.context_window_tokens !== 'number' ||
                model.context_window_tokens < min_context_tokens
              ) {
                return false;
              }
            }

            if (min_output_tokens !== undefined) {
              if (
                typeof model.max_output_tokens !== 'number' ||
                model.max_output_tokens < min_output_tokens
              ) {
                return false;
              }
            }

            for (const path of required_capabilities ?? []) {
              const resolved = getPath(model, path);
              if (
                !resolved.exists ||
                !explicitlySupported(resolved.value)
              ) {
                return false;
              }
            }

            return true;
          })
          .slice(0, limit);

        return jsonText({
          generated_at: selector.generated_at,
          count: models.length,
          models,
          interpretation:
            'Missing or null facts are unknown. default_policy is a safety/lifecycle filter, not a quality ranking.',
        });
      },
    );

    server.registerTool(
      'get_model',
      {
        title: 'Get verified model details',
        annotations: {
          readOnlyHint: true,
          destructiveHint: false,
          openWorldHint: true,
          idempotentHint: true,
        },
        description:
          'Get the current Aurora selector record and official-source detail record for one exact provider/model pair.',
        inputSchema: z.object({
          provider_slug: providerSchema,
          model_key: z.string().min(1),
        }),
      },
      async ({ provider_slug, model_key }) => {
        const [selector, details] = await Promise.all([
          fetchRegistry<{
            models?: Array<Record<string, unknown>>;
          }>('selector.json'),
          fetchRegistry<{
            models?: Array<Record<string, unknown>>;
          }>(`models/${provider_slug}.json`),
        ]);

        const modelKey = model_key.toLowerCase();

        const selectorRecord =
          (selector.models ?? []).find(
            (model) =>
              String(model.provider_slug ?? '').toLowerCase() ===
                provider_slug &&
              String(model.model_key ?? '').toLowerCase() === modelKey,
          ) ?? null;

        const detailRecord =
          (details.models ?? []).find(
            (model) =>
              String(model.model_key ?? '').toLowerCase() === modelKey,
          ) ?? null;

        return jsonText({
          provider_slug,
          model_key,
          found: Boolean(selectorRecord || detailRecord),
          selector_record: selectorRecord,
          detail_record: detailRecord,
          interpretation:
            'Only verified_official_detail fields are current authoritative semantic facts. Missing or null means unknown.',
        });
      },
    );

    server.registerTool(
      'get_guidance',
      {
        title: 'Get verified provider guidance',
        annotations: {
          readOnlyHint: true,
          destructiveHint: false,
          openWorldHint: true,
          idempotentHint: true,
        },
        description:
          'Read current provider prompting guidance verified against official documentation. Stale and unverified rules are excluded by default.',
        inputSchema: z.object({
          provider_slug: z
            .enum(['openai', 'anthropic', 'google', 'mistral', 'xai'])
            .optional(),
          only_current_verified: z.boolean().default(true),
        }),
      },
      async ({ provider_slug, only_current_verified }) => {
        const guidance = await fetchRegistry<{
          generated_at?: string;
          counts?: unknown;
          guidance?: Array<Record<string, unknown>>;
        }>('guidance.json');

        const rules = (guidance.guidance ?? []).filter((rule) => {
          if (
            provider_slug &&
            String(rule.provider_slug ?? '').toLowerCase() !==
              provider_slug
          ) {
            return false;
          }

          if (
            only_current_verified &&
            rule.verification_state !== 'verified_official_guidance'
          ) {
            return false;
          }

          return true;
        });

        return jsonText({
          generated_at: guidance.generated_at,
          counts: guidance.counts,
          guidance: rules,
        });
      },
    );

    server.registerTool(
      'get_validation_policy',
      {
        title: 'Get Aurora validation policy',
        annotations: {
          readOnlyHint: true,
          destructiveHint: false,
          openWorldHint: true,
          idempotentHint: true,
        },
        description:
          'Read one current Aurora validation/lifecycle policy document: evals, benchmarks, golden, runtime, traceability, comparison, replay, or migration.',
        inputSchema: z.object({
          name: policySchema,
        }),
      },
      async ({ name }) => {
        const document = await fetchRegistry(`${name}.json`);
        return jsonText(document);
      },
    );
  },
);

export { handler as GET, handler as POST, handler as DELETE };
