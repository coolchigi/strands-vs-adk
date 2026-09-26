# Hand-off

Paste everything below the line into a fresh session started in this repo.

---

Two part blog series comparing AWS Strands Agents and Google ADK. Part 1 is written and
verified. Part 2's system is built but has never produced a course. I want both published by
tomorrow, Sunday 27 September 2026.

Read `PROGRESS.md` first. It has the current state, the Part 2 blocker already isolated, and
the credentials that work.

The job:

1. **Get Part 2 running end to end.** It dies on the first model call. Redesign it if that is
   what it takes, I would rather ship something that works.
2. **Write the Part 2 article** from that run, not from what the code claims.
3. **Make sure nothing is stale.** We shipped "Claude Sonnet 4" when the default is 4.6. Check
   every version, default, model id and limit against the installed packages. Check the links.
4. **Publish both.**

Three things I care about:

**The code has to run.** If someone copies a block out of the article, it works.

**My voice.** Read `~/.claude/voice-dna.md` and use the `writing` skill for prose. Part 1 is
the reference.

**Real tests.** Part 2 has 235 green tests and cannot make a single model call, because they
all drive fakes that return what the code expects. Write tests that fail when the thing is
broken, and prove it by breaking it. Anything that talks to a model needs a test that talks to
a model.

Use in-session todos. Keep `PROGRESS.md` as the only tracking doc, no new ones. Run the code
rather than reading it, every real bug here was found by running. When you fix a claim, grep
for it everywhere before calling it done.
