export const metadata = {
  title: 'Aurora Support',
  description: 'Support information for the Aurora ChatGPT plugin.',
};

export default function SupportPage() {
  return (
    <main>
      <p className="eyebrow">Aurora</p>
      <h1>Support</h1>
      <p>
        Aurora is a prompt-engineering plugin that uses Aurora Live Data to
        verify current AI model facts, provider guidance, and validation
        policies.
      </p>
      <div className="card">
        <h2>Before reporting a problem</h2>
        <p>
          Check whether the issue concerns Aurora itself, Aurora Live Data, or
          the target AI provider. Include the exact request, the model name,
          and the visible Aurora validation status when available. Do not send
          passwords, API keys, access tokens, or other secrets.
        </p>
      </div>
      <div className="card">
        <h2>Report an issue</h2>
        <p>
          Public technical issues can be reported in the Aurora Live Data
          GitHub repository.
        </p>
        <p>
          <a href="https://github.com/Allerxis/aurora-live-data/issues">
            github.com/Allerxis/aurora-live-data/issues
          </a>
        </p>
      </div>
      <div className="card">
        <h2>Service status</h2>
        <p>
          The MCP server is read-only and exposes public Aurora Live Data.
          Current health can be checked through the plugin's
          <code> get_status </code>
          tool.
        </p>
      </div>
      <p><a href="/">Back to Aurora</a></p>
    </main>
  );
}
