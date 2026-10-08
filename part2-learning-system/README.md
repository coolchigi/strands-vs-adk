# Part 2: the learning system

Tell it what you want to learn, in your own words. It asks a couple of questions, reads the
official docs, plans a course around what you want to be able to do, and writes lessons you
learn by doing: you build something, the tests tell you whether it works, and the answers
stay hidden until you've tried. Every fact in a lesson links to the page it came from.

It's built twice, once on AWS Strands Agents and once on Google ADK, which is what the blog
series is about. As a learner you don't need to care which one runs.

## Install it once

You need [uv](https://docs.astral.sh/uv/getting-started/installation/), which fetches the right
Python itself. Then:

```bash
uv tool install "git+https://github.com/coolchigi/strands-vs-adk#subdirectory=part2-learning-system"
```

If you've cloned the repo, `uv tool install .` from this folder does the same.

That gives you a `learn` command you can run from anywhere. (If your shell can't find it,
`uv tool update-shell` adds uv's tool folder to your PATH.)

That one install includes both builds. Which one runs depends on what you have set up:

- **ADK, with Gemini.** The first time you build a course, `learn` asks for a Gemini API key,
  which you can get at [aistudio.google.com/apikey](https://aistudio.google.com/apikey). It
  saves it to `~/.config/learning-system/env`, readable only by you, and doesn't ask again.
- **Strands, with Claude on Amazon Bedrock.** You need AWS credentials and access to Claude
  Sonnet 4.6 and Claude Haiku 4.5 in Bedrock. It picks Strands when you have no Gemini key
  saved, or when you pass `--engine strands`. If you sign in with `aws login`, install it this
  way instead:

  ```bash
  uv tool install --with "botocore[crt]" "git+https://github.com/coolchigi/strands-vs-adk#subdirectory=part2-learning-system"
  ```

If you have both set up, it uses Gemini unless you pass `--engine strands`.

## Ask for a course

```bash
learn "I want to learn TypeScript so I can build a small web app"
```

It asks what it needs to know, and you answer right there. This is a real run, trimmed, with the course folder shown where it goes by default and the spending line as it reads now:

```text
A few questions first, so I build the right course:
  What is your background with programming, particularly JavaScript?
> I know JavaScript well but have never used TypeScript
  What kind of web app are you looking to build, and do you have a specific framework in mind?
> a small web app with a backend API

Got it. Building your TypeScript course in ~/courses/typescript
This usually takes 30 to 90 minutes. You can stop it any time, and running the same command
again picks up where it left off.
Spending cap: $5.00. Spent so far: $0.00. At $2.50 it switches to a cheaper model
(gemini-3.5-flash-lite) to finish.

  Looking for the official TypeScript documentation
  ✓ Found it: TypeScript, version 7.0
  ✓ Worked out 15 things you'll need to be able to do
  Reading up on: Configure and execute the TypeScript compiler with strict safety settings
  ...
```

Leave it running. If it stops (you close the laptop, the network drops, it hits the spending
cap), run the same command again and it carries on from the last step that finished.

## Take the course

```bash
cd ~/courses/typescript
learn next
```

`learn next` tells you which lesson you're on. Each lesson is a folder with a `README.md` to
read (the explanation, with every fact linked to its source, then a worked example), and an
`exercise/` folder with files to change. Then:

```bash
learn check       # run the exercise's tests. Do this until it says Passed
learn hint        # stuck? one hint at a time
learn solution    # the answer. It records that you looked
learn quiz        # 3 questions. You see each answer after you've picked one
learn review      # questions you missed come back after 1, 3, 7 and 21 days
learn status      # every lesson, and what you've done
learn report "question 2 has two right answers"   # tell it something's wrong
```

These work from anywhere inside the course folder. `learn` on its own lists your courses and
how far you are in each.

A course folder also works without `learn` installed: `python3 learn.py next` inside it does
the same thing. On Windows, type `py` where it says `python3`.

## What gets checked, and what you need installed

Before a course is written out, every exercise is run three ways: the finished answer has to
pass its tests, the untouched starter has to fail them, and each gap you're meant to fill
has to fail them on its own, so there's nothing you can skip and still be told you passed.

| Subject | Tests run with | You need |
|---|---|---|
| Terraform | `terraform test`, against a mock AWS provider, so no cloud account | [Terraform](https://developer.hashicorp.com/terraform/install) |
| Python | Python's own `unittest` | Python 3.9 or newer |
| JavaScript | Node's built-in test runner | [Node.js](https://nodejs.org/en/download) 20 or newer |
| TypeScript | Node's built-in test runner, then the TypeScript compiler in strict mode, so a type error fails too | Node.js 22.6 or newer. The compiler is fetched once with npm |
| Anything else | nothing: you judge your work against the answer | |

One thing to know: lessons that still had problems after 3 tries ship anyway, with the
problems listed at the top of the lesson, so you know it's the course and not you.

## Settings

Everything goes in `~/.config/learning-system/env` as `NAME=value` lines, or your
environment:

- `LEARNING_BUDGET_USD`: the most one course may spend on model calls. $5 on Gemini and $10
  on Claude by default. It's a hard stop, and running the same command after raising it
  carries on.
- `LEARN_SWITCH_AT`: how far into that budget it switches to a cheaper model so the course
  finishes (Gemini 3.5 Flash-Lite, or Claude Haiku 4.5 on Bedrock). `0.5` by default. It
  tells you when it switches.
- `LEARN_CHEAP_MODEL`: a different cheaper model, or `none` to never switch.
- `LEARN_HOME`: where courses go. `~/courses` by default.
- `LEARN_ENGINE`: `adk` (Gemini) or `strands` (Claude on Bedrock), if you don't want it picked
  from your keys.

## For developers

The two framework builds can also be run directly, which is how the blog series compares them:

```bash
uv sync --extra test
uv run python -m impl.adk.run "I'd like to deeply understand Terraform and build projects along the way."
uv run python -m impl.strands.run "I'd like to deeply understand Terraform and build projects along the way."
```

Those write to `out/adk` and `out/strands`, where the two Terraform courses from the blog are.
Add `--extra aws-login` to the sync if your AWS credentials come from `aws login`.

Grade a course, re-checking every quote against its page and running every exercise:

```bash
uv run python -m learning.judge out/adk
```

Run the tests (they use the real `terraform`, `python3` and `node` where installed, and no
model):

```bash
uv run --extra test pytest
```

```text
learning/         shared: the model, fetching and verification, the stages, the checks,
                  running exercises, writing the course, learn.py, the `learn` command
impl/strands/     the Strands half: agents, tools and MCP, the graph, the meter
impl/adk/         the ADK half: the same, the ADK way
tests/            offline, no model calls
examples/         the runnable snippets from the blog posts
```
