# Hand-off

Paste the block below into a fresh session, started in `/Users/ceke/Desktop/strands-vs-adk`.

---

I'm publishing a two part blog series comparing AWS Strands Agents and Google ADK. Part 1 is
written, Part 2 is not. I want both live by tomorrow, Sunday 27 September 2026.

Work in `/Users/ceke/Desktop/strands-vs-adk`. Use in-session todos and keep them updated so I
can see what is done and what is not.

## Three things I care about, in order

**1. The code in the blogs has to run.** If someone copies a block out of the article, it
works. Part 1's examples have been run live against Bedrock and Gemini. Part 2's system has
never produced a course and currently crashes on its first model call (details below).

**2. Nothing outdated.** We shipped "Claude Sonnet 4" when the default is Sonnet 4.6, and it
took me reading the Strands docs to catch it. Check every stated version, default, model id,
region and limit against the installed packages, not against memory or docs. Check every link
resolves. The failure mode to avoid: verifying that an API *exists* while never checking the
*value* the article claims about it.

**3. My voice.** Read `~/.claude/voice-dna.md` and apply it. No em dashes, no semicolons, no
banned words, and no negative parallelisms, which the file calls the fatal one. Use the
`writing` skill for any prose. Part 1 is the reference for tone.

## Where things stand

`PROGRESS.md` in the repo root is the single tracking doc. Please keep using it rather than
creating new ones. I ended up with 18 markdown files last time and it was a mess.

**Part 1** is done and verified. Article at `blog-series/part1-hello-world/article.md`, 9,281
words. Runnable examples in `part1-hello-world/`, 20 files, published at
github.com/coolchigi/strands-vs-adk. Dev.to draft id `4725533`, unpublished, synced. My API key
is at `~/.devto`. Images are pinned to commit `f76de7a`.

**Part 2** has a built system at `blog-series/part2/`, 29 files, 4,052 lines, both frameworks,
235 passing tests. The article is barely started: `blog-series/part2/article.md` has an opening
section and nothing else.

## The Part 2 bug, already isolated

The 235 tests all drive fake models (`ScriptedModel`, `ScriptedLlm`), so none of them ever hit
a real API. The first live run fails immediately:

```
400 INVALID_ARGUMENT: Please enable tool_config.include_server_side_tool_invocations
to use Built-in tools with Function calling.
```

`impl/adk/researcher.py` puts `output_schema` and `google_search` on the same agent. Isolated:

| config | result |
|---|---|
| `output_schema` alone | works |
| `output_schema` + a plain function tool | works |
| `google_search` alone | works |
| `output_schema` + `google_search` | 400 |

`GoogleSearchTool(bypass_multi_tools_limit=True)` does **not** fix it. Still 400.

This also makes `FINDINGS.md` finding 1 wrong. It says ADK "allows `output_schema` and `tools`
on the same agent", which is ADK's own docstring and is true for function tools and false for
built-in ones.

Three ways out, my call needed if you want to change the shape of the story:

- Split into two agents, one searching without a schema, one structuring. Costs an extra call.
- Drop `output_schema` on the searching agent and parse its text.
- Drop `google_search` and give ADK the same Tavily MCP path as Strands.

Redesigning the learning system is fine if that's what it takes. The Researcher is stage one,
so Curriculum, Teacher, Feedback and the refresh path have never executed either.

## Credentials that work

- **Gemini**: `GOOGLE_API_KEY` in `part1-hello-world/.env`, gitignored. Billing is topped up.
- **Bedrock**: AWS profile `aws-agent`, region `us-east-1`. Always name the profile, my
  `~/.aws/config` has no default on purpose. If you authenticate with `aws login` you also need
  `botocore[crt]` or boto3 fails before Strands is involved.
- **Tavily**: I don't have a key. The Strands researcher needs one. Tell me if you need it.
- **Dev.to**: `~/.devto`.

## Versions

Pinned at `strands-agents 1.55.1`, `google-adk 2.9.0`, and verified against those. Newer exist
(1.57.0, 2.9.2) and I've deliberately not taken them. Don't bump without asking.

## What I want by the end

Part 2's system actually produces a course end to end, Part 2's article written from what
happened rather than from what the code claims, both articles free of stale facts and dead
links, and both published.

## How I'd like you to work

Verify, don't assert. Run the code rather than reading it, since every real bug in this project
was found by running and none by reading. When you fix a claim, grep for it everywhere before
calling it fixed, because the same wrong sentence has shown up in four files more than once.
Resolve doubts before mentioning them. One thing at a time, and tell me what you actually did.
