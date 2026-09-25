# Strands vs ADK

Runnable code for a blog series comparing **AWS Strands Agents** and **Google ADK** by building
the same thing twice, once in each.

Each part is its own project with its own pinned dependencies. A comparison is only useful if
you can reproduce it, so the versions are frozen at what the article was written against rather
than tracking latest.

| Part | What it covers | Code |
|---|---|---|
| 1 | Hello World: tools, the agent loop, state, control points, multi-agent, evaluation, deployment | [`part1-hello-world/`](part1-hello-world/) |

## Start here

```bash
cd part1-hello-world
uv sync --extra evals --extra serve
uv run smoke_test.py
```

`smoke_test.py` parses every example, resolves every import against what you installed, and
constructs every agent, graph and app. It never calls a model, so it needs no credentials and
costs nothing. Run it before you go looking for API keys.

## Credentials

The two frameworks want different things.

**Strands** defaults to Amazon Bedrock with Claude Sonnet 4.6 and uses your normal AWS credential
chain, so it needs Bedrock model access in your region.

**ADK** reads `GOOGLE_API_KEY`, either from your shell or from a `.env` next to the agent.

Each part's README has the details.

## One thing worth knowing up front

Installing both frameworks without pinning OpenTelemetry silently downgrades `google-adk` by a
major version. ADK caps `opentelemetry-api` at 1.42.1, Strands allows anything below 2.0.0, and
pip resolves the conflict by walking ADK backwards instead of failing. Every part here pins it.
