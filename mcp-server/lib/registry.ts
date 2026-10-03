const REGISTRY_BASE =
  'https://raw.githubusercontent.com/Allerxis/aurora-live-data/main/registry';

export const PROVIDERS = [
  'openai',
  'anthropic',
  'google',
  'mistral',
  'xai',
  'meta',
] as const;

export const POLICY_NAMES = [
  'evals',
  'benchmarks',
  'golden',
  'runtime',
  'traceability',
  'comparison',
  'replay',
  'migration',
] as const;

export async function fetchRegistry<T = unknown>(path: string): Promise<T> {
  const response = await fetch(`${REGISTRY_BASE}/${path}`, {
    headers: {
      accept: 'application/json',
      'user-agent': 'AuroraLiveDataMCP/1.0',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(
      `Aurora Live Data returned HTTP ${response.status} for ${path}`,
    );
  }

  return (await response.json()) as T;
}

export function getPath(
  value: unknown,
  path: string,
): { exists: boolean; value: unknown } {
  let current = value;

  for (const part of path.split('.')) {
    if (
      !current ||
      typeof current !== 'object' ||
      !(part in (current as Record<string, unknown>))
    ) {
      return { exists: false, value: null };
    }
    current = (current as Record<string, unknown>)[part];
  }

  return { exists: true, value: current };
}

export function explicitlySupported(value: unknown): boolean {
  if (value === true) return true;
  if (typeof value !== 'string') return false;

  const normalized = value.trim().toLowerCase();
  return new Set([
    'supported',
    'true',
    'yes',
    'available',
    'input_and_output',
    'input_only',
    'output_only',
  ]).has(normalized);
}

export function jsonText(value: unknown) {
  const structuredContent =
    value && typeof value === 'object' && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : { value };

  return {
    structuredContent,
    content: [
      {
        type: 'text' as const,
        text: JSON.stringify(value),
      },
    ],
  };
}
