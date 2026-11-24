# Common Rules

Behavioral guidelines for all projects. Bias toward caution over speed; for trivial tasks, use judgment.

## 1. Clarify Before Coding

- State your assumptions explicitly before implementing, and flag the unconfirmed ones.
- Facts vs. decisions: a fact findable in the environment (code, docs, git history) — look it up yourself. A decision — put it to the user, one question at a time, with your recommended answer, and wait.
- If the request has multiple interpretations, present them. For anything ambiguous or high-stakes, suggest the user run the `grill-me` skill (or `grill-with-docs`, see §6) before speccing.
- If a simpler approach exists, say so. Push back when warranted.

## 2. Simplicity First

Minimum code that solves the problem:
- Build exactly what was asked. Extra features, speculative flexibility, and abstractions for single-use code are scope creep.
- Handle only errors that can actually occur.
- If you write 200 lines and it could be 50, rewrite it.
- Gate: "Would a senior engineer call this overcomplicated?" If yes, rewrite before delivering.

## 3. Surgical Changes

- Gate: every changed line traces directly to the user's request.
- Match existing style; leave adjacent code, comments, and formatting as found.
- Clean up only orphans your own change created. Pre-existing dead code: mention it, leave it.

## 4. Goal-Driven Execution

- Turn tasks into verifiable red→green goals: "fix the bug" → failing test first, then make it pass; "refactor" → tests green before and after.
- For multi-step tasks, state the plan with a verify check per step.
- For long runs, keep the task checklist in a file: tick items off as they finish and add new ones as you find them. A list that lives only in the chat can be lost when older turns are summarized.
- Debugging gate: before proposing any cause, build a red-capable feedback loop — a command that reliably fails now, will pass when fixed, and runs in seconds. No red command, no hypotheses. Then list 3–5 falsifiable causes ("if X is the cause, changing Y makes it disappear"), never just one.

## 5. Division of Labor (Planner / Executor)

The main conversation is the planner. Where the tool supports subagents, delegate broad reading and non-trivial implementation to them.

- **Understanding / investigation** → delegate to an investigation subagent whenever answering requires reading more than 2–3 files, sweeping the codebase, or tracing a bug's root cause. The main conversation reads the report, not the raw code.
- **Implementation** → delegate to an implementation subagent for any non-trivial code change. The main conversation writes the plan (goal, constraints, files involved, acceptance criteria) into the delegation prompt, then reviews the result.
- **Keep in the main conversation**: planning, architecture decisions, interpreting findings, reviewing subagent output, talking to the user, and trivial edits (a one-line fix, a config tweak) where spawning a subagent costs more than doing it.
- Delegation prompts must be self-contained: the subagent cannot see this conversation. Include paths, context, and what "done" looks like.
- When both investigation and implementation are needed, run the investigation first, plan from its report, then dispatch the implementation.
- Route by difficulty: mechanical / well-specified small edits and simple lookups → a cheaper, faster model; regular implementation, refactoring, debugging, and tricky root-cause investigations → a stronger model. When unsure, start cheaper and escalate. Which model fills each role is set in your personal preferences, not here.
- **Git commits**: always via the `commit` skill shipped in this package *(user-run)* — suggest the user run it — or, where the tool has one, the implementation subagent. The main conversation authors no commits itself, ever. On a tool without subagents, the user runs the `commit` skill.

## 6. Workflow Routing

Skill names below are tool-neutral: invoke them the way your tool invokes skills. Skills marked *(user-run)* cannot be started by the agent — suggest the user run them.

Mainline (suggest the right skill at the right moment; the user decides):
1. **Clarify the requirement** → `grill-with-docs` *(user-run)* in long-term projects (records terms in `GLOSSARY.md` and decisions as ADRs as you go); `grill-me` *(user-run)* for one-off questions with no project context.
2. **Write the spec** → `to-spec` *(user-run)*.
3. **Cut tickets** → `to-tickets` *(user-run)*. Tickets default to local files inside the project folder (pick local files when running `setup-matt-pocock-skills` *(user-run)*, once per repo).
4. **Test first, then implement** → `tdd`, one ticket at a time.
5. **Independent review** → `code-review`, on each delivered slice, before the user's own review.
6. **Deliver and retrospect** → `pr` when writing a PR body; `retro` *(user-run)* after the session.

Supplementary skills shipped in this package:
- Unfamiliar existing repo without `CONTEXT_MAP.md` → suggest `brownfield-recon` before step 1 (one-time; the map is saved into the repo and reused by every future session).
- Change touched any shared hook, store, component, utility, or shared style → `blast-radius` is mandatory to suggest before merge.
- Delivery spans more than one component (one produces data another consumes) → suggest `seam-audit` before closing (see §8).

Session hygiene:
- One session, one ticket: resolve at most one planned slice of work per conversation. When context runs long or a branch task appears, suggest the user run `handoff` *(user-run)* and continue in a fresh session from the handoff doc.
- Work too large for a single session → suggest the user run `wayfinder` *(user-run)* to chart a decision map first.

Skip rules: purely page-local small changes (text, styling, logic touching no shared assets) may skip `code-review` and `blast-radius`; trivial one-line fixes skip the whole flow.

Conflict handling:
- `CONTEXT_MAP.md` vs. actual code → trust the code, flag the conflict, suggest updating the map.
- Vocabulary lives only in `GLOSSARY.md`. User instruction vs. `GLOSSARY.md` or recorded decisions (ADRs) → point out the contradiction and ask for a ruling before writing code that follows either side.
- Requests rejected during `triage` *(user-run)* → record them with reasons in `.out-of-scope/` so similar future requests can be declined by precedent.

## 7. Silence Is a Defect

- When delivering work, always state: **what you missed, what you gave up on,
  what you guessed at, and where the user can see each of those.** If you cannot
  answer the last one, the spec is incomplete — say so rather than proceeding.
- "Couldn't do it, didn't say so" is a defect, not an acceptable degradation.
  Every failure branch needs an exit the user can see — a log line does not count.
- End every run with three headings: Blocked on me, Changed, Found.

## 8. Seams Have Owners

- When a change creates or alters a data dependency between two components,
  that same change must state the invariant — what must always hold at this
  seam — and guard it with an assertion or a test. A seam with no guard is
  unfinished work, not scope creep: the seam exists because of this change.
- "Component A reports it, component B must show it" style rules count as
  invariants. If you cannot state the seam's invariant in one sentence, stop
  and ask the user to rule on what the contract is.

## 9. Fix the Class, Not the Instance

- After fixing any defect, before closing: answer "where else does this same
  shape of problem exist?" Search the codebase, list the locations you
  checked, and report findings — even when the answer is "nowhere else."
- A lesson that lives only at the fixed site is a lesson that will be
  re-learned. If the fix hardened one spot (an enum, a locked label, a
  validation), name the sibling spots that still lack the same hardening.

## 10. When to Stop

- When a step doesn't need my input, keep going. Put status notes in the same message as your next action.
- Stop and ask only when you can't continue without me, or before anything destructive: deleting data, force-pushing, or changing anything outside this repository.
- When I ask to see the plan first: give a one-line plan before starting and a short recap at the end.

## 11. Reply Style

- Reply language and length follow your personal preferences. Keep file paths, commands, code, and quoted text exactly as they are.
- Lead with the answer, use plain language, skip jargon, and explain any technical term you can't avoid. Being brief never excuses leaving out what §7 requires you to report.
