# Codex Appendix

Append this after the common rules in `~/.codex/AGENTS.md`. Everything here is valid only in Codex.

This package can be installed on Codex in two ways, and skill names differ between them:

- **File-copy route** (the default; for the ChatGPT desktop app, which has no `codex` command): the skills are copied into `~/.agents/skills/` and have **no prefix** — `commit`, `brownfield-recon`, `grill-me`. The optional save-time check is not installed.
- **Plugin route** (only for people who have the `codex` command): the skills come from plugins and carry a **prefix** — `dev-bingfa:commit`, `mattpocock-skills:grill-me`.

Always use a skill name exactly as it appears in your own list of available skills. Below, names are given as `commit` / `dev-bingfa:commit` meaning "whichever form your list shows".

## C1. Subagent names (for §5)

This package's three subagents are copied into `~/.codex/agents/` (in both routes; plugins cannot install Codex subagents). Their names carry the `bingfa-` prefix; a plain `explorer` is Codex's own built-in agent, not this package's.

- Investigation subagent (§5) → `bingfa-explorer`.
- Implementation subagent (§5) → `bingfa-implementer`.
- Internet research (debugging an error, finding solutions across sources) → `bingfa-web-search-agent`.

If one of them is not available in this session, say so to the user and do not claim the work was delegated.

## C2. Commits (for §5)

Git commits: the `commit` skill is user-run — suggest the user type `$` and pick `commit` / `dev-bingfa:commit` (whichever the list shows) — or delegate to `bingfa-implementer`. The main conversation authors no commits itself, ever. (Invoking the skill this way follows the Codex documentation; it has not yet been tested with this package.)

## C3. Save-time check

- File-copy route: the `dev-bingfa-check` save-time check is **not installed** — it is off. Never claim it ran.
- Plugin route: it may be installed, but on Codex it is **not verified to run** (Codex runs plugin hooks only after the user trusts them in `/hooks`, and no run inside a real Codex session has been observed yet). Never claim it ran.

Either way, before delivering any change to a Python file, check it yourself: every broad `except` (bare, `Exception`, `BaseException`) whose body is only `pass` is a silent failure (§7) — fix it, or state where the user can see that failure. If the check does report one, treat it the same way.

## C4. Invoking skills

- This package's skills: `brownfield-recon`, `blast-radius`, `seam-audit`, `commit` (plugin route: `dev-bingfa:brownfield-recon`, …). Matt Pocock's skills: `tdd`, `code-review`, `pr`, `grill-me`, … (plugin route: `mattpocock-skills:tdd`, …).
- The user starts a skill by typing `$` and picking it (Codex documentation; not yet tested with this package). When suggesting a *(user-run)* skill from §6, give the user the exact name from your skill list, e.g. `grill-me` or `mattpocock-skills:grill-me`.
- *(user-run)* is enforced by rule text here, not by Codex. Codex ignores the Claude Code setting `disable-model-invocation`; it only hides skills that ship their own Codex setting, and in the plugin route Codex loads more of Matt Pocock's skill folders than his plugin list (at least one manual-only skill was seen in the automatic list). So: never start a skill marked *(user-run)* in §6, or any skill whose own instructions say it is manual-only, even if Codex offers it to you — suggest the user run it.
