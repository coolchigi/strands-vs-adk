# Strands vs ADK, where things stand

One document. If something is worth tracking it goes here rather than into a new file.

Last updated 25 September 2026.

## Part 1: Hello World

**Article** `blog-series/part1-hello-world/article.md`, 9,281 words. Complete.

**Code** `part1-hello-world/`, 20 files, one folder per question the article asks, both
frameworks in each. Published at github.com/coolchigi/strands-vs-adk.

**Dev.to** draft `4725533`, unpublished, synced with the article. Cover and three
animations pinned to commit `f76de7a`.

Verified: every example run live against Bedrock and Gemini, every stated default and limit
checked against the installed packages, every quoted error triggered rather than grepped,
38/38 links, all code blocks parse and the multi-part files assemble into runnable scripts.

### What the audits found, in order

Round 1 and 2 read the article. Rounds 3 onwards ran it, which is where the real bugs were.

- `main.py` was not runnable as printed. Four blocks using `await` with no `async def` or
  `asyncio.run` anywhere. The central ADK example could not execute.
- `event.is_final_response()` is `True` for error events, which carry no `content`, so the
  unguarded print turned every API error into `AttributeError: 'NoneType'`.
- Agents as tools and a `Graph` do not stack. Passing the tool-wired agents to
  `GraphBuilder` makes Strands refuse the re-entrant call, and the graph retries rather than
  failing, so a run takes ten minutes instead of ninety seconds and never finishes.
- The BigQuery plugin import fails on a base install, and the error names
  `google.api_core` rather than the missing extra.
- The evals section pointed at `strands-evals`, an unrelated squatted package. The real one
  is `strands-agents-evals`, imported as `strands_evals`.
- Eleven Strands documentation links died overnight when their docs restructured.
- The Bedrock default is Claude Sonnet 4.6, not Sonnet 4, and `us-west-2` is the fallback
  region rather than the default anyone with a configured profile gets.
- `LoopAgent` warns on construction, not on import.
- The repo's FastAPI example had drifted from the article and returned a Python repr
  instead of JSON.
- The ADK sub-agent handoff is prompt dependent, not unconditional.

## Part 2: the learning system

**Article** not written. This is the outstanding work.

**System** `blog-series/part2/`, 29 implementation files, 4,052 lines, both frameworks,
235 tests passing.

**Never run against a real model.** The tests drive `ScriptedModel` and `ScriptedLlm`, so
they prove the machinery routes correctly and prove nothing about whether the courses are
any good. Running it needs `GOOGLE_API_KEY`, which we have, and `TAVILY_API_KEY`, which we
do not. The Strands researcher reaches Tavily over MCP, so without that key only the ADK
half can run.

**Fourteen framework differences** are recorded in `part2/FINDINGS.md`, each verified
against the installed packages. That file, plus `ARCHITECTURE.md`, `DEPLOY.md` and
`TESTING.md`, is raw material for the article and should fold into it once written.

## The Part 2 blocker

The 235 tests all drive `ScriptedModel` / `ScriptedLlm` fakes, so none has ever hit a real
API. The first live run dies on the first model call:

```
400 INVALID_ARGUMENT: Please enable tool_config.include_server_side_tool_invocations
to use Built-in tools with Function calling.
```

`impl/adk/researcher.py` puts `output_schema` and `google_search` on one agent. Isolated:

| config | result |
|---|---|
| `output_schema` alone | works |
| `output_schema` + a plain function tool | works |
| `google_search` alone | works |
| `output_schema` + `google_search` | 400 |

`GoogleSearchTool(bypass_multi_tools_limit=True)` does not fix it.

This makes `FINDINGS.md` finding 1 wrong. ADK's docstring says `output_schema` and `tools`
work together, which holds for function tools and fails for built-in ones.

Ways out: split into two agents (one searches, one structures), drop `output_schema` and
parse the text, or give ADK the same Tavily path as Strands. Researcher is stage one, so
Curriculum, Teacher, Feedback and refresh have never run either.

## Credentials

- Gemini: `GOOGLE_API_KEY` in `part1-hello-world/.env`, billing topped up
- Bedrock: AWS profile `aws-agent`, `us-east-1`. Always name the profile, there is no
  default on purpose. `aws login` auth also needs `botocore[crt]`
- Tavily: no key yet, the Strands researcher needs one
- Dev.to: `~/.devto`, draft id `4725533`

## Open

**Part 2 must produce a real artifact.** A learn by doing course on Terraform, built from
sources that say what the lessons claim. That is the thing the article is about, so it has to
exist before the article is written. Terraform is the subject I want because it is the one I
used when we first tested how each framework would handle "I'd like to deeply understand
Terraform and build projects along the way."

**Part 1 is close but not assumed clean.** Every issue in it so far was found by me pushing
back rather than by a check catching it. Treat it as needing a pass, not a glance.


- Write the Part 2 article.
- Run the Part 2 system live. Needs a Tavily key.
- Publish Part 1 when you are ready. Tags are still a guess.

## Versions

Pinned at `strands-agents 1.55.1`, `google-adk 2.9.0`. Newer exist and were deliberately
not taken: strands-agents 1.57.0, google-adk 2.9.2, strands-agents-evals 1.4.0, mcp 2.2.0.
