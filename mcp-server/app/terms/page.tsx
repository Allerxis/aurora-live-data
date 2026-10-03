export const metadata = {
  title: 'Aurora Terms of Service',
  description: 'Terms of service for the Aurora ChatGPT plugin.',
};

export default function TermsPage() {
  return (
    <main>
      <p className="eyebrow">Aurora</p>
      <h1>Terms of Service</h1>
      <p>Effective date: 3 October 2026.</p>

      <div className="card">
        <h2>Service</h2>
        <p>
          Aurora provides prompt-engineering assistance and read-only access
          to Aurora Live Data, a registry of AI-model facts, provider prompting
          guidance, and Aurora validation policies derived from public sources.
        </p>
      </div>

      <div className="card">
        <h2>Permitted use</h2>
        <p>
          You may use Aurora to create, audit, optimize, adapt, evaluate, and
          migrate prompts. You must use Aurora and any resulting prompts in
          accordance with applicable law, OpenAI's terms, and the terms of any
          third-party AI provider or service involved in your workflow.
        </p>
      </div>

      <div className="card">
        <h2>Limitations</h2>
        <p>
          AI model capabilities, prices, lifecycle states, interfaces, and
          provider guidance can change. Aurora attempts to verify volatile
          facts before using them, but does not guarantee that every public
          source is complete, continuously available, or error-free.
        </p>
        <p>
          Aurora does not provide legal, medical, financial, or other
          regulated professional advice. Users remain responsible for
          reviewing prompts and outputs before relying on them in consequential
          contexts.
        </p>
      </div>

      <div className="card">
        <h2>No destructive actions</h2>
        <p>
          The Aurora Live Data MCP is read-only. It does not modify provider
          accounts, purchase services, send messages, delete user data, or
          store credentials.
        </p>
      </div>

      <div className="card">
        <h2>Availability and changes</h2>
        <p>
          Aurora may change, suspend, or update its data sources, validation
          rules, tools, or supported models as providers evolve. Reasonable
          efforts are made to keep public documentation and validation
          behavior aligned with the deployed service.
        </p>
      </div>

      <div className="card">
        <h2>Disclaimer</h2>
        <p>
          Aurora is provided on an "as is" and "as available" basis to the
          extent permitted by law. No guarantee is made that a prompt will
          produce a particular result on a third-party model or service.
        </p>
      </div>

      <p>For questions, see <a href="/support">Aurora Support</a>.</p>
      <p><a href="/">Back to Aurora</a></p>
    </main>
  );
}
