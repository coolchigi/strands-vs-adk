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

## Open

- Write the Part 2 article.
- Run the Part 2 system live. Needs a Tavily key.
- Publish Part 1 when you are ready. Tags are still a guess.

## Versions

Pinned at `strands-agents 1.55.1`, `google-adk 2.9.0`. Newer exist and were deliberately
not taken: strands-agents 1.57.0, google-adk 2.9.2, strands-agents-evals 1.4.0, mcp 2.2.0.
