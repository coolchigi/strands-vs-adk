# Hand-off

Paste everything below the line into a fresh session started in this repo.

---

Two part blog series comparing AWS Strands Agents and Google ADK. Part 1 is written, Part 2's
system is built but has never produced a course. I want both published by tomorrow, Sunday
27 September 2026.

Read `PROGRESS.md` first. Current state, the Part 2 blocker already isolated, and the
credentials that work, including my Dev.to API key at `~/.devto` and draft id `4725533`.

The job:

1. **Get Part 2 running end to end** and produce a real artifact: a learn by doing course on
   Terraform. It dies on the first model call today. Redesign it if that is what it takes.
2. **Write the Part 2 article** from that run, not from what the code claims.
3. **Polish Part 1 to publish-ready.** It is close, so Part 2 is the focus, but do not assume
   it is clean.
4. **Publish both.**

The bar: **neither part carries outdated information, and every code sample is runnable.** If a
reader copies a block, it works.

The standard I want on finding problems: you find them, not me. I have had to poke at this
series to surface a broken hello world, a squatted package, a graph that burned ten minutes on
retries, and a model version that was a whole point release out of date. Every one was
findable. Check claimed values against the installed packages rather than confirming a name
exists. Run the code rather than reading it. When you fix a claim, grep for it everywhere
before calling it done.

**My voice**: read `~/.claude/voice-dna.md`, use the `writing` skill for prose, Part 1 is the
reference.

**Real tests**: Part 2 has 235 green tests and cannot make a single model call, because they
all drive fakes that return what the code expects. Write tests that fail when the thing is
broken, and prove it by breaking it.

Use in-session todos. Keep `PROGRESS.md` as the only tracking doc.
