# Strands vs ADK, Part 1: Hello World

Runnable code for every example in Part 1. One folder per question the article asks,
Strands and ADK side by side in each.

Versions are pinned to the ones the article was written against: `strands-agents 1.55.1`
and `google-adk 2.9.0`. Verified on Python 3.13 and 3.14.

## Setup

```bash
uv sync --extra evals --extra serve
```

Or with pip:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Either way you get the exact versions the article was written against. The pins are
deliberate: this is a comparison at a fixed point, so running it months from now should
still produce what the article describes.

Then check the install without spending a token:

```bash
uv run smoke_test.py      # or: python smoke_test.py
```

That parses every file, resolves every import against what you installed, and constructs
every agent, graph and app for real. It does not call a model, so it needs no credentials
and costs nothing. All 20 files should come back `ok`.

Every example in here has been run against a live model. Strands against Bedrock
(Claude Sonnet 4.6, `us-east-1`) and ADK against Gemini (`gemini-flash-latest`).

A few things worth knowing that only showed up by running them:

- `01-hello-world` and `02-tools` get different answers to the same question. The first has
  no tool so it asks what you mean, the second calls `get_course_topic` and answers.
- The control points fire in the same order on both sides,
  `model -> tool -> model`, even though Strands attaches hooks to an agent you already hold
  and ADK takes callbacks at construction.
- `06-multi-agent` sometimes replies as `[curriculum_builder]` rather than `[course_agent]`.
  The parent hands the turn over when the request suits the child, and the speaker label is
  where you see it happen. Ask it to outline a curriculum and it delegates. Ask it what to
  teach and the parent answers itself.

## Credentials

The two frameworks want different things, and neither is set up for you.

**Strands** defaults to Amazon Bedrock with Claude Sonnet 4.6, so it uses your normal AWS
credential chain and needs Bedrock model access in your region.

```bash
export AWS_REGION=us-east-1
# plus your usual AWS credentials, or a configured profile
```

If you authenticate with `aws login`, add one more thing:

```bash
uv sync --extra aws-login        # or: pip install "botocore[crt]"
```

That credential provider needs the CRT bindings. The AWS CLI ships them and a virtualenv
does not, so `aws sts get-caller-identity` succeeds while the same profile fails inside
Python with `MissingDependencyException`. The error names botocore, and it arrives before
Strands is involved at all.

**ADK** reads `GOOGLE_API_KEY`, which you can get free from
[Google AI Studio](https://aistudio.google.com/apikey). One file at the root of this folder
covers every section:

```bash
cp .env.example .env     # then put your key in it
```

`adk run` walks up from the agent folder looking for a `.env`, so it finds that one from any
section. It is gitignored.

`python main.py` does not read it. ADK only loads `.env` through its CLI, so export the
variable for those:

```bash
export GOOGLE_API_KEY="..."
cd 03-agent-loop && python main.py
```

## The sections

| Folder | Article question | Strands | ADK |
|---|---|---|---|
| `01-hello-world` | Hello World | `hello-world.py` | `course_agent/` |
| `02-tools` | Giving our agent a tool | `hello-world.py` | `course_agent/` |
| `03-agent-loop` | What runs the agent loop? | `hello-world.py` | `main.py` |
| `04-state` | Where does state live? | `conversation.py`, `agent_state.py` | `main.py` |
| `05-control-points` | What control points do we have? | `hooks.py` | `course_agent/` |
| `06-multi-agent` | What if one agent isn't enough? | `graph.py` | `course_agent/`, `workflow.py` |
| `07-evaluation` | Evaluation and observability | `evaluate_strands.py`, `observe_strands.py` | `test_researcher.py` |
| `08-deployment` | How can I deploy what I've built? | `app.py` | see notes below |

## Running them

Strands files are plain Python:

```bash
cd 01-hello-world
python hello-world.py
```

ADK agent folders run through the CLI, from the folder that contains `course_agent`:

```bash
cd 01-hello-world
adk run course_agent
```

The files called `main.py` drive ADK from Python instead, with a `Runner` and a session:

```bash
cd 03-agent-loop
python main.py
```

`04-state/agent_state.py` is the one example that needs no credentials at all. It only
touches `agent.state`, so it is the fastest way to confirm your environment works.

## Things that will bite you

**Install both frameworks without the OpenTelemetry pins and pip silently downgrades
`google-adk` to 1.x.** ADK caps `opentelemetry-api` at 1.42.1, Strands allows anything
below 2.0.0, and pip resolves the conflict by walking ADK back a major version instead of
failing. That is why `requirements.txt` pins it.

**The evals package is not called what you would guess.** You install
`strands-agents-evals` and you import `strands_evals`. `pip install strands-evals` gets
you an unrelated 4KB package by another author.

**`event.is_final_response()` is `True` for error events, and those have no `content`.**
Every `main.py` here guards it. Without the guard, a bad API key reaches you as
`AttributeError: 'NoneType' object has no attribute 'parts'` instead of the message Google
actually sent.

**Some ADK pieces need extras the base install does not carry.** The BigQuery analytics
plugin and `DiscoveryEngineSearchTool` both need `google-adk[bigquery-analytics]`, and both
fail with `No module named 'google.api_core'`, which names neither the thing you wanted nor
the extra you are missing.

**Section 08 has no ADK file.** ADK ships `adk deploy` with four targets
(`agent_engine`, `cloud_run`, `docker`, `gke`), so there is nothing to write. Point it at
any of the `course_agent` folders here. Strands has no deploy command, which is why the
Strands side is a FastAPI app you write yourself.
