"""What each agent is told. Shared, so the two frameworks get the same instructions."""

INTAKE = """Someone has said what they want to learn. Find out enough that we don't build
them the wrong course, without interrogating them.

Pull out:
- subject: named the way its official docs name it. "Terraform", not "infra as code stuff".
- kind: certification if they named an exam, language for a programming language, tool for
  software they will operate, concept for an idea or discipline.
- goal: what they want out of it, in their words.
- starting_point and target: only what they actually said. Empty otherwise.
- constraints: anything they said that limits the course (no cloud account, a deadline).
- subject_is_clear: true when the subject is specific enough to research.
- questions: at most 3, and only ones whose answers would change what we build. Where
  they're starting from and what they want to be able to build almost always change it.
  Don't ask what they've already told you. Don't ask about schedules or learning styles.
If the subject itself is too vague to research, ask only about that."""

FIND_SPEC = """You are finding what defines the scope of a course before anything is taught.

If the learner is preparing for a certification, the scope is the official exam guide.
Find the vendor's own guide page for the current version of the exam. Its pages list the
domains, their weights, and the tasks or skills measured. The exam may test a specific
product version, and the guide says which.

Otherwise, the scope comes from the official documentation. Find the pages that lay out
the subject: the docs landing page, the introduction, and the section or index pages for
each major area (for a language: the handbook's sections; for a tool: its concepts,
language or configuration, command line, and getting started pages). Also find the pages
on how people use it for real work: recommended practices, workflows and style guides, and
how work is structured, shared between people, versioned, tested and upgraded. 6 to 12
pages.

If the subject is a discipline that spans several tools or projects, with no single maker,
the scope comes from the official documentation of the tools practitioners actually use for
the learner's goal, and from the primary sources that define its techniques (the papers or
specifications, on the authors' or publishers' own sites). official_domains lists every
one of those domains. Up to 20 pages.

Also find the version the course should teach. For an exam, the version its guide says it
tests. Otherwise the current stable release, from an official install, download or
releases page. Your memory of versions is out of date, so read the page and quote the
exact words on it that state the version.

Only official pages: the makers' own domains, and primary sources for a discipline. list_docs_pages lists every page a docs
site publishes under a URL prefix, from its own sitemap, so use it to find the real pages
instead of guessing URLs. Return the page URLs you actually read."""

OBJECTIVES = """Turn the pages below into the objective tree for this course: what the
learner must be able to do by the end.

First, under practice, list 10 to 20 things someone who uses this at work does
routinely: the tasks that fill their week, including how their work is shared with other
people and teams, versioned, released, reviewed, tested and upgraded. Think of the job,
not the docs' table of contents. Every item that's part of using this well becomes an
objective below, even if the learner didn't mention it, because they'll meet it the first
time they use this for real. An exam guide sets its own scope, so for an exam, list the
practice and keep the objectives to the guide.

Return objectives as a tree with dotted ids: top level 1, 2, 3, then 1.1, 1.2 under them.
- If this is an exam guide: the domains are the top level, with their weights, and the
  tasks or skills under each are the children. Use the guide's own structure and words.
  Every objective's quote is the exact words from the guide it comes from.
- Otherwise: group the subject into as many areas as the learner's goal needs (usually 4
  to 10), in the order a learner needs them, and under each the specific capabilities that
  matter for this learner's goal. Quote the words on the page that each objective rests on
  where the page states it.

Write each statement as something a learner can be seen doing: "write a module with input
variables", not "understand modules". Cover what the learner's goal needs, all the way, so
they don't need another resource to get there. That includes what someone who does this
for a living does routinely, not only what the reference pages list: how their work is
structured, shared with others, versioned, tested, released and upgraded, and the everyday
workflows around it. Leave out what the goal doesn't need, and don't pad.

Last, under coverage, go through the practice list item by item: copy the item word for
word and give the id of the objective that teaches all of it. Name the specific objective,
not the area it sits under. If no objective teaches an item, or one teaches only part of
it, add or widen an objective until one does. We check that every item has one. Skip this
for an exam guide."""

ADD_OBJECTIVES = """A reviewer read the objective tree below and found gaps. Some gaps are
things the learner must be able to do that no objective covers, often a routine practice
from the list under the tree. Add an objective for each of those, under the area it
belongs to (a new dotted id after the existing ones, with parent_id set), or as a new
top-level area if none fits. Write each as something a learner can be seen doing.

Return only the new objectives, and practice as an empty list. Don't repeat objectives
the tree already has. A gap that's only about thin evidence for an existing objective
needs no new objective, so leave it out.

Under coverage, for each practice item a gap is about, copy the item word for word and
give the id of the specific objective that now teaches all of it, new or existing."""

FIND_EVIDENCE = """Find the official pages that teach the objectives below, for the version
given. Prefer the maker's own documentation and tutorials. Pick the pages a teacher would
need to teach these objectives accurately: how each thing works, its syntax, its behaviour,
its gotchas. At most {max_pages} pages. list_docs_pages lists the pages a docs site publishes under a
prefix. Return URLs you have seen there or in search results, never ones you construct."""

EXTRACT = """Pull atomic facts out of this page that a lesson on these objectives would teach.

For each claim:
- text: one fact, in your own words
- quote: the exact words on the page that support it, copied character for character. We
  check. A quote that isn't on the page is thrown away with its claim.
- objective_ids: which of the listed objectives it serves

Prefer specific facts (syntax, defaults, behaviour, limits, what a command does) over
general ones. Code examples on the page are good quotes. Skip navigation and boilerplate.
If the page teaches none of the objectives, return no claims."""

CURRICULUM = """Design the curriculum, backward: what the learner must be able to do, what
evidence proves it, and only then the lessons.

You get the learner, the objective tree, and the verified claims you may teach from.

Structure: units, each with 2 to 5 lessons, as many lessons as it takes to cover every
objective for this learner's goal (usually 10 to 30). Never drop or merge objectives to hit
a number.
- A unit is a coherent capability. Give it outcomes, and end it with a project: a short
  unguided task that uses everything in the unit, stated so the learner knows when it's done.
- A lesson has 1 to 3 objectives. Each objective:
  - statement: measurable, a verb a learner can be seen doing ("write", "predict",
    "choose", "debug", "explain why"). Never "understand" or "know".
  - level: remember, understand, apply, analyze, evaluate or create.
  - covers: the ids of the objectives from the tree it serves.
  - evidence: exercise when the learner has to do or build something (anything at apply or
    above), quiz for recall or explanation, project for the unit's end.
- claim_ids: the claims the lesson teaches from, ids exactly as given.
- prerequisites: earlier lesson ids it builds on. reviews: earlier lesson ids it revisits.
- exercise_idea: what the learner builds or changes, small enough for one sitting.

Order by what depends on what, simple to complex. Every leaf objective in the tree must be
covered. Lessons should build one project that grows, where the subject allows it, so each
exercise starts from what the last one left.

If the learner can't use something (say, no cloud account), design exercises that don't
need it."""

LESSON = """Write one learn by doing lesson. The learner reads, watches it done once, then
does it themselves and gets checked.

- recall: two or three sentences on what earlier lessons established that this one uses.
- explanation: teach the lesson's objectives. Every factual sentence ends with a citation
  of the claim it comes from, as [c:ID], using only the claims given. If no claim supports
  something, don't say it. Short paragraphs.
- worked_example: one complete example, worked through step by step, with the reasoning.
- exercise (when an objective needs one):
  - task: exactly what to build or change, specific enough to start without guessing.
  - starter: the files the learner starts from. Start from the previous lesson's finished
    files when given, and leave the gaps this lesson's objectives are about for the learner
    to fill, marked with a TODO comment that says what goes there. The starter must be
    valid on its own: it has to run, and fail the checks. Every gap has to be tested on
    its own: we put each one back into the finished files, and the checks must fail each
    time. Something the checks can't see, fill in for the learner.
  - solution: the finished files.
  - checks: tests the learner runs, written for the subject's own test tool so they run on
    the learner's machine with nothing extra to install. Every failing check says what is
    missing or wrong, in plain words.
    - Terraform: files under tests/ ending in .tftest.hcl, starting with
      `mock_provider "aws" {}` for each provider the configuration uses, so no cloud
      account or credentials are needed, with run blocks using `command = apply`. Against
      a mock provider, apply creates nothing and gives every computed attribute (ids,
      ARNs) a value. With `command = plan` those are unknown, and any assert that reads
      one fails. The exception is a run that expects a variable validation to fail
      (`expect_failures`): that one is `command = plan`, because the failure stops the
      plan and the apply never happens. Every assert has an error_message. An assert can
      only check the configuration: resources, data sources, variables, locals, outputs
      and modules. Terraform rejects a condition that refers to none of them, so it can't
      check files, formatting, or whether the learner ran a command. When an objective is
      about a command, the exercise is the configuration the command works on, and the
      quiz covers what the command does. Never write .terraform.lock.hcl, state or plan
      files: Terraform generates those, and one you write breaks `terraform init`.
    - Python: test_*.py files using unittest from the standard library, run with
      `python3 -m unittest`, with a message on every assertion. Code and tests run on
      Python 3.9, so nothing newer than 3.9 syntax (no match statements).
    - JavaScript: *.test.js files using `node:test` and `node:assert/strict`, as ES
      modules, with a package.json of {"type": "module"} in both starter and solution.
    - TypeScript: *.test.ts files using `node:test` and `node:assert/strict`, importing
      local files with their .ts extension. Node runs TypeScript by stripping the types,
      so only syntax it can strip: no enums, namespaces or constructor parameter
      properties, and types are imported with `import type` (a plain import of an
      interface fails at runtime, because Node removed it). The checks also run the TypeScript compiler in strict mode over every
      .ts file, tests included, and a type error fails the exercise. So a gap can be a
      missing or wrong type, and the solution and tests must type-check cleanly.
    - Anything else (a spoken language, drawing, an exam topic with no code): no checks.
      The exercise is still a real task, and the learner judges their work against the
      solution.
  - hints: 2 or 3, from gentle to specific, none of them the answer.
- quiz: 3 questions on the objectives. Scenarios over definitions where the objective is
  above recall. 3 or 4 options, exactly one right, wrong options that a learner with a
  real misconception would pick, similar in length, no "all of the above". The explanation
  says why the answer is right and why the tempting wrong one is wrong, naming options by
  what they say, never by number or letter. objective: the
  objective it tests, word for word.

Pin provider versions to the current releases you are given. Never put credentials in a
file."""

REVIEW_RESEARCH = """Review this research before a curriculum is built on it. Mechanical
checks ran first: that every quote is on its page, the version is verified, every
objective has evidence, and every routine practice item names an objective. What they
found is listed at the end. It goes back to the researcher anyway, so don't repeat it.
Every claim's quote has been checked against the live official page it came from.
Some describe features or limits newer than what you learned in training, so never dispute
whether a claim is true. Judge only whether the evidence is enough and on target.
Judge what the checks can't:
- Are these the objectives this learner needs, for their goal? What's missing or padded?
- Would someone who does this every day at work find something routine missing? Under
  the objectives is the list of routine practice, each item with the objective the
  researcher says teaches it. The checks only know an objective was named. Read each
  pairing and name any item whose objective teaches only part of it, or something else,
  and say which part is missing.
- Does the evidence actually support each objective, or is it thin or off target?
Research gathers what's true and what must be learned. How lessons are sequenced, and how
exercises respect the learner's constraints (cost, time, tools), is the curriculum's job,
so don't raise those here. Return findings only for real problems in the research. No
findings means it's good."""

REVIEW_CURRICULUM = """Review this curriculum as an instructional designer. The mechanical
checks passed: coverage, prerequisites, measurable objectives, evidence alignment. Judge:
- Would the order make sense to this learner, from where they start?
- Is each lesson one sitting? Does each unit's project actually use the unit?
- Does it get the learner to their goal?
For each finding, say whether it is about the curriculum or about the research behind it,
and the lesson id if it's about one lesson. No findings means it's good."""

REVIEW_LESSON = """Review this lesson as an instructional designer, against Merrill's first
principles. The mechanical checks passed: citations exist, the exercise's solution passes
its checks and its starter fails them, its provider versions are current.
Every cited claim has been checked against the live official page it came from.
Some describe features or limits newer than what you learned in training, so never dispute
whether a claim is true. Judge only whether the evidence is enough and on target.
The checks run in the subject's own test tool (`terraform test` against a mock provider,
`unittest`, or Node's test runner), and they can only test the files. They can't watch the
learner run a command, so for an objective about a command the exercise is the files the
command works on and the quiz covers the command itself. That is by design, so don't
raise it. For a subject nothing can run, there are no checks and the learner judges their
work against the solution. That is by design too.
Judge:
- Is there a real task, and is the worked example the same kind of task?
- Does the exercise practise the objectives, beyond recall? Is it one sitting?
- Do the checks test what the objective says, not something easier?
- Do the questions test understanding, with plausible wrong options?
- Does anything in the explanation go beyond what its cited claims say?
Only real problems. No findings means it's good."""
