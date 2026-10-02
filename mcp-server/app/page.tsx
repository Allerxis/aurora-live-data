const tools = ['get_status', 'find_models', 'get_model', 'get_guidance', 'get_validation_policy'];

export default function Home() {
  return (
    <main>
      <p className="eyebrow">Aurora infrastructure</p>
      <h1>Aurora Live Data MCP</h1>
      <p>Read-only Model Context Protocol server for Aurora's verified live model registry, provider guidance, and validation policies.</p>
      <div className="card">
        <p><strong>MCP endpoint</strong></p>
        <code>/api/mcp</code>
        <p><strong>Authentication</strong></p>
        <code>None</code>
      </div>
      <div className="card">
        <p><strong>Tools</strong></p>
        {tools.map((tool) => <p key={tool}><code>{tool}</code></p>)}
      </div>
      <p>No prompt content, user manifests, API keys, or secrets are stored by this server.</p>
    </main>
  );
}
