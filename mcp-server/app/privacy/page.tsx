export const metadata = {
  title: 'Aurora Privacy Policy',
  description: 'Privacy policy for the Aurora ChatGPT plugin and Aurora Live Data MCP.',
};

export default function PrivacyPage() {
  return (
    <main>
      <p className="eyebrow">Aurora</p>
      <h1>Privacy Policy</h1>
      <p>Effective date: 3 October 2026.</p>

      <div className="card">
        <h2>What Aurora processes</h2>
        <p>
          Aurora Live Data is a public, read-only MCP service. Its tools are
          designed to receive only structured lookup parameters needed to
          retrieve public AI-model information, such as provider names, model
          identifiers, capability filters, and validation-policy names.
        </p>
        <p>
          The MCP service does not require an Aurora account, name, email
          address, uploaded files, payment information, government identifiers,
          passwords, API keys, authentication secrets, or health information.
          Users should not submit secrets or personal data to Aurora tools.
        </p>
      </div>

      <div className="card">
        <h2>Purpose</h2>
        <p>
          Tool inputs are processed only to retrieve and return the requested
          public registry information, provider guidance, or Aurora validation
          policy. Aurora does not use MCP tool inputs for advertising or user
          profiling.
        </p>
      </div>

      <div className="card">
        <h2>Storage and retention</h2>
        <p>
          Aurora does not maintain an application database of user prompts,
          MCP tool arguments, or tool responses. Application-level retention
          for this content is therefore 0 days. The server code does not
          intentionally log request bodies or tool arguments.
        </p>
        <p>
          The hosting platform may generate ordinary operational network and
          runtime metadata under its own infrastructure policies. Aurora does
          not intentionally add prompt or tool-input content to those logs.
        </p>
      </div>

      <div className="card">
        <h2>Service providers and recipients</h2>
        <p>
          Vercel hosts the public MCP endpoint. GitHub hosts the public Aurora
          Live Data registry that the MCP server reads. OpenAI processes the
          ChatGPT conversation and invokes the plugin according to OpenAI's
          own terms and privacy practices.
        </p>
      </div>

      <div className="card">
        <h2>User controls</h2>
        <p>
          Because Aurora does not maintain user accounts or an application
          database of tool content, there is normally no Aurora-held personal
          profile to access, correct, or delete. Users can stop use at any time
          by disabling or uninstalling the plugin in ChatGPT.
        </p>
      </div>

      <div className="card">
        <h2>Changes</h2>
        <p>
          This policy may be updated when Aurora's data handling changes. The
          effective date above will be updated when material changes are made.
        </p>
      </div>

      <p>
        Privacy questions can be submitted through the public support channel:
        {' '}
        <a href="/support">Aurora Support</a>.
      </p>
      <p><a href="/">Back to Aurora</a></p>
    </main>
  );
}
