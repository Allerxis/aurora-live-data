
import { z } from 'zod';
import {
  registerAppResource,
  registerAppTool,
  RESOURCE_MIME_TYPE,
} from '@modelcontextprotocol/ext-apps/server';
import { fetchRegistry } from './registry';
import { createAuroraWidgetHtml } from './ui';

const MIGRATION_UI = 'ui://aurora/migration-plan/v2.html';
const STATUS_UI_V2 = 'ui://aurora/status/v2.html';
const COMPARISON_UI_V2 = 'ui://aurora/model-comparison/v2.html';
const VALIDATION_UI_V2 = 'ui://aurora/validation-report/v2.html';
const UI_DOMAIN = 'https://aurora-live-data.vercel.app';

const providerSchema = z.enum([
  'openai',
  'anthropic',
  'google',
  'mistral',
  'xai',
  'meta',
]);

const validationOutcomeSchema = z.enum([
  'pass',
  'fail',
  'needs_review',
  'not_applicable',
]);

const validationCriterionSchema = z.object({
  id: z.string().min(1),
  label: z.string().optional(),
  outcome: validationOutcomeSchema,
  severity: z.enum(['blocker', 'error', 'warning', 'info']).optional(),
  note: z.string().optional(),
});

const migrationCandidateSchema = z.object({
  provider_slug: z.string(),
  model_key: z.string(),
  display_name: z.string().optional(),
  verification_state: z.string().optional(),
  semantic_hash: z.string().optional(),
  default_policy: z.string().optional(),
  usage_state: z.string().optional(),
  same_provider: z.boolean().optional(),
  context_window_tokens: z.number().nullable().optional(),
  max_output_tokens: z.number().nullable().optional(),
  pricing: z.record(z.string(), z.unknown()).nullable().optional(),
  semantic_source_url: z.string().optional(),
});

function uiResource(
  uri: string,
  kind: 'status' | 'comparison' | 'validation' | 'migration',
  description: string,
) {
  return {
    contents: [
      {
        uri,
        mimeType: RESOURCE_MIME_TYPE,
        text: createAuroraWidgetHtml(kind),
        _meta: {
          ui: {
            prefersBorder: true,
            domain: UI_DOMAIN,
            csp: {
              connectDomains: [],
              resourceDomains: [],
            },
          },
          'openai/ui': {
            availableDisplayModes:
              kind === 'comparison' || kind === 'validation' || kind === 'migration'
                ? ['inline', 'fullscreen']
                : ['inline'],
          },
          'openai/widgetDescription': description,
        },
      },
    ],
  };
}

export function registerAuroraUi(server: any) {
  registerAppResource(
    server,
    'aurora-live-data-status-ui',
    STATUS_UI_V2,
    {
      description: 'Aurora Live Data status dashboard',
      _meta: { ui: { domain: UI_DOMAIN } },
    },
    async () =>
      uiResource(
        STATUS_UI_V2,
        'status',
        'Compact Aurora Live Data health and validation readiness dashboard.',
      ),
  );

  registerAppResource(
    server,
    'aurora-model-comparison-ui',
    COMPARISON_UI_V2,
    {
      description: 'Aurora verified model comparison',
      _meta: { ui: { domain: UI_DOMAIN } },
    },
    async () =>
      uiResource(
        COMPARISON_UI_V2,
        'comparison',
        'Side-by-side factual comparison of verified AI model records.',
      ),
  );

  registerAppResource(
    server,
    'aurora-validation-report-ui',
    VALIDATION_UI_V2,
    {
      description: 'Aurora validation report',
      _meta: { ui: { domain: UI_DOMAIN } },
    },
    async () =>
      uiResource(
        VALIDATION_UI_V2,
        'validation',
        'Interactive Aurora PASS / NEEDS_REVIEW / FAIL validation report.',
      ),
  );

  registerAppResource(
    server,
    'aurora-migration-plan-ui',
    MIGRATION_UI,
    {
      description: 'Aurora prompt migration plan',
      _meta: { ui: { domain: UI_DOMAIN } },
    },
    async () =>
      uiResource(
        MIGRATION_UI,
        'migration',
        'Interactive Aurora prompt-migration plan with compatible targets and warnings.',
      ),
  );

  registerAppTool(
    server,
    'render_live_data_status',
    {
      title: 'Show Aurora Live Data status',
      description:
        'Render the Aurora Live Data status dashboard. Use this only when the user asks to see health, coverage, freshness, or validation readiness; internal get_status checks should stay data-only.',
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: true,
        idempotentHint: true,
      },
      inputSchema: z.object({}),
      _meta: {
        ui: { resourceUri: STATUS_UI_V2, visibility: ['model', 'app'] },
        'openai/outputTemplate': STATUS_UI_V2,
        'openai/toolInvocation/invoking': 'Loading Aurora Live Data status…',
        'openai/toolInvocation/invoked': 'Aurora Live Data status ready.',
      },
    },
    async () => {
      const status = await fetchRegistry<Record<string, unknown>>('status.json');
      return {
        structuredContent: status,
        content: [
          {
            type: 'text' as const,
            text:
              'Aurora Live Data status: ' +
              (status.healthy === true ? 'healthy' : 'degraded') +
              '.',
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    'render_model_comparison',
    {
      title: 'Compare verified AI models',
      description:
        'Render a side-by-side Aurora comparison for 2 to 4 exact model IDs. Use get_model/find_models first to identify relevant targets, then render only the finalists that matter to the user.',
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: true,
        idempotentHint: true,
      },
      inputSchema: z.object({
        models: z
          .array(
            z.object({
              provider_slug: providerSchema,
              model_key: z.string().min(1),
            }),
          )
          .min(2)
          .max(4),
      }),
      _meta: {
        ui: { resourceUri: COMPARISON_UI_V2, visibility: ['model', 'app'] },
        'openai/outputTemplate': COMPARISON_UI_V2,
        'openai/toolInvocation/invoking': 'Preparing model comparison…',
        'openai/toolInvocation/invoked': 'Model comparison ready.',
      },
    },
    async ({ models }: { models: Array<{ provider_slug: string; model_key: string }> }) => {
      const selector = await fetchRegistry<{
        generated_at?: string;
        models?: Array<Record<string, unknown>>;
      }>('selector.json');

      const selected = models
        .map(({ provider_slug, model_key }) =>
          (selector.models ?? []).find(
            (model) =>
              String(model.provider_slug ?? '').toLowerCase() ===
                provider_slug.toLowerCase() &&
              String(model.model_key ?? '').toLowerCase() ===
                model_key.toLowerCase(),
          ),
        )
        .filter(
          (model): model is Record<string, unknown> => model !== undefined,
        );

      const labels = selected
        .map((model) => String(model.model_key ?? 'unknown'))
        .join(', ');

      return {
        structuredContent: {
          generated_at: selector.generated_at,
          count: selected.length,
          models: selected,
          interpretation:
            'Missing or null facts are unknown. default_policy is a safety/lifecycle filter, not a quality ranking.',
        },
        content: [
          {
            type: 'text' as const,
            text:
              selected.length > 0
                ? 'Showing a factual comparison of ' +
                  selected.length +
                  ' verified model record(s): ' +
                  labels +
                  '.'
                : 'No matching verified model records were found for the requested comparison.',
          },
        ],
      };
    },
  );

  registerAppTool(
    server,
    'render_validation_report',
    {
      title: 'Show Aurora validation report',
      description:
        'Render a normalized Aurora validation report after prompt-evaluator/runtime-acceptance has established the gate and criterion outcomes. Do not invent criterion outcomes just to populate the UI.',
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      inputSchema: z.object({
        status: z.enum(['pass', 'needs_review', 'fail']),
        summary: z.string().optional(),
        target_model: z.string().optional(),
        eval_release_gate: z.string().optional(),
        golden_release_gate: z.string().optional(),
        runtime_gate: z.string().optional(),
        repair_passes: z.number().int().min(0).max(2).default(0),
        criteria: z.array(validationCriterionSchema).default([]),
        unresolved: z.array(z.string()).default([]),
      }),
      _meta: {
        ui: { resourceUri: VALIDATION_UI_V2, visibility: ['model', 'app'] },
        'openai/outputTemplate': VALIDATION_UI_V2,
        'openai/toolInvocation/invoking': 'Rendering Aurora validation…',
        'openai/toolInvocation/invoked': 'Aurora validation report ready.',
      },
    },
    async (report: {
      status: 'pass' | 'needs_review' | 'fail';
      summary?: string;
      target_model?: string;
      eval_release_gate?: string;
      golden_release_gate?: string;
      runtime_gate?: string;
      repair_passes: number;
      criteria: Array<Record<string, unknown>>;
      unresolved: string[];
    }) => ({
      structuredContent: report,
      content: [
        {
          type: 'text' as const,
          text:
            'Aurora validation: ' +
            report.status.toUpperCase() +
            (report.summary ? ' — ' + report.summary : '') +
            '.',
        },
      ],
    }),
  );

  registerAppTool(
    server,
    'render_migration_plan',
    {
      title: 'Show Aurora prompt migration plan',
      description:
        'Render a prompt-migration plan only after prompt-migration has established its status, constraints, compatible candidates, warnings, and selected target if any. Ambiguous plans must remain NEEDS_REVIEW.',
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        openWorldHint: false,
        idempotentHint: true,
      },
      inputSchema: z.object({
        status: z.enum([
          'not_needed',
          'plan_ready',
          'needs_review',
          'blocked',
        ]),
        trigger: z.string().optional(),
        source_target: z
          .object({
            provider_slug: z.string().nullable().optional(),
            model_key: z.string().nullable().optional(),
            found_in_selector: z.boolean().optional(),
            verification_state: z.string().nullable().optional(),
            lifecycle_status: z.string().nullable().optional(),
            default_policy: z.string().nullable().optional(),
          })
          .optional(),
        selected_target: migrationCandidateSchema.nullable().optional(),
        eligible_candidates: z
          .array(migrationCandidateSchema)
          .max(12)
          .default([]),
        warnings: z.array(z.string()).default([]),
        required_actions: z.array(z.string()).default([]),
      }),
      _meta: {
        ui: { resourceUri: MIGRATION_UI, visibility: ['model', 'app'] },
        'openai/outputTemplate': MIGRATION_UI,
        'openai/toolInvocation/invoking': 'Rendering migration plan…',
        'openai/toolInvocation/invoked': 'Migration plan ready.',
      },
    },
    async (plan: {
      status: 'not_needed' | 'plan_ready' | 'needs_review' | 'blocked';
      trigger?: string;
      source_target?: Record<string, unknown>;
      selected_target?: Record<string, unknown> | null;
      eligible_candidates: Array<Record<string, unknown>>;
      warnings: string[];
      required_actions: string[];
    }) => {
      const selectedKey =
        plan.selected_target &&
        typeof plan.selected_target.model_key === 'string'
          ? plan.selected_target.model_key
          : null;

      return {
        structuredContent: plan,
        content: [
          {
            type: 'text' as const,
            text:
              'Aurora migration plan: ' +
              plan.status.toUpperCase() +
              (selectedKey ? ' → ' + selectedKey : '') +
              '.',
          },
        ],
      };
    },
  );
}
