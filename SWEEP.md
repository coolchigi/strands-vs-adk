# Full sweep, 25 September 2026

Verify against the pinned versions (`strands-agents 1.55.1`, `google-adk 2.9.0`).
Report newer releases, do not bump.

The rule this time: check claimed **values**, not just that names exist. The
"Claude Sonnet 4" error passed every check I ran because `hasattr` was true.

## A. Environment
- [x] A1 installed versions match the pins in every file that states one
- [x] A2 newer releases: what exists, what changed
- [x] A3 both venvs healthy, examples venv rebuilds from lockfile

## B. Part 1 article, claim by claim
- [x] B1 every stated default, model id, region, version, limit checked against runtime values
- [x] B2 every backticked identifier resolves
- [x] B3 every quoted error or warning string byte-exact
- [x] B4 every number, count and parameter-count claim
- [x] B5 code blocks parse, multi-part files assemble
- [x] B6 imports resolve, undefined names
- [x] B7 every URL returns 200
- [x] B8 voice rules, placeholders, fences, tables

## C. Repo examples
- [x] C1 smoke test 20/20 from a clean sync
- [x] C2 every Strands example run live on Bedrock
- [x] C3 every ADK example run live on Gemini
- [x] C4 README claims verified, including the live-run status it asserts
- [x] C5 pyproject and requirements pins match what actually installs

## D. Part 2 docs and system
- [x] D1 FINDINGS.md, every claim checked against runtime values
- [x] D2 ARCHITECTURE.md
- [x] D3 DEPLOY.md
- [x] D4 CRITERIA.md and TESTING.md
- [x] D5 part2 README
- [x] D6 235-test suite passes
- [x] D7 quoted errors byte-exact, numbers, code blocks parse

## E. Cross-cutting
- [x] E1 version strings consistent across every doc
- [x] E2 cross-references (finding numbers, file paths, test names) resolve
- [x] E3 Dev.to draft matches the final article

---

## Result

All 22 items checked. Three errors found, all fixed.

**Part 1 said `LoopAgent` warns on import.** It does not. The import is silent and the
warning fires when you construct one. Verified both ways in a subprocess. This is the same
error I corrected in Part 2's FINDINGS weeks ago and never carried back to Part 1.

**The repo's FastAPI example diverged from the article.** `str(result.message)` instead of
`result.message`, so the endpoint returned a Python repr rather than JSON. Exercised with
TestClient against live Bedrock to confirm the fix.

**The README stated the ADK sub-agent handoff as unconditional.** It is prompt dependent.
"Outline a curriculum" delegates to `curriculum_builder`, "what should I teach" is answered
by the parent. Both verified live.

Verified and correct: every stated default and limit (`turns`, `output_tokens`,
`total_tokens`, `max_llm_calls` 500, the `temp:` prefix never persisting, ADK reading
default values into the tool schema), every quoted error triggered rather than grepped,
all five Agents CLI metric names and three deployment targets checked against their docs,
38/38 URLs, 235 part2 tests, all 20 examples run live on Bedrock and Gemini.

Newer releases exist and were deliberately not taken: strands-agents 1.57.0,
google-adk 2.9.2, strands-agents-evals 1.4.0, mcp 2.2.0.
