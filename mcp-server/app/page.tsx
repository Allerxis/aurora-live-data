const tools = [
  'get_status',
  'find_models',
  'get_model',
  'get_guidance',
  'get_validation_policy',
];

export default function Home() {
  return (
    <main>
      <p className="eyebrow">Aurora</p>
      <h1>Prompt engineering grounded in live model data.</h1>
      <p>
        Aurora creates, audits, optimizes, adapts, and evaluates prompts for
        current AI models. Aurora Live Data verifies model capabilities,
        provider guidance, and validation policies before Aurora relies on
        volatile facts.
      </p>

      <div className="card">
        <h2>What Aurora does</h2>
        <p>
          Create reusable prompts, optimize an existing prompt for a named
          model, compare verified model capabilities, adapt prompts across
          providers, audit prompt quality, and revalidate prompts when models
          or provider guidance change.
        </p>
      </div>

      <div className="card">
        <h2>Aurora Live Data</h2>
        <p>
          The public MCP server is read-only and exposes verified registry
          data through five data tools:
        </p>
        {tools.map((tool) => <p key={tool}><code>{tool}</code></p>)}
        <p><strong>MCP endpoint</strong></p>
        <code>https://aurora-live-data.vercel.app/api/mcp</code>
      </div>

      <div className="card">
        <h2>Privacy by design</h2>
        <p>
          Aurora Live Data does not require an Aurora account and does not
          maintain an application database of user prompts or tool responses.
          The MCP surface is designed for structured public-registry lookups.
        </p>
      </div>

      <div className="card">
        <h2>Information</h2>
        <p><a href="/support">Support</a></p>
        <p><a href="/privacy">Privacy Policy</a></p>
        <p><a href="/terms">Terms of Service</a></p>
        <p>
          <a href="https://github.com/Allerxis/aurora-live-data">
            Source and public registry
          </a>
        </p>
      </div>
    </main>
  );
}
