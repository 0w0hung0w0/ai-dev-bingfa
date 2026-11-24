# Codex Appendix

Append this after the common rules in `~/.codex/AGENTS.md`. Everything here is valid only in Codex.

## C1. Subagent names (for §5)

This package's three subagents are copied by the user into `~/.codex/agents/` (plugins cannot install Codex subagents). Their names carry the `bingfa-` prefix; a plain `explorer` is Codex's own built-in agent, not this package's.

- Investigation subagent (§5) → `bingfa-explorer`.
- Implementation subagent (§5) → `bingfa-implementer`.
- Internet research (debugging an error, finding solutions across sources) → `bingfa-web-search-agent`.

If one of them is not available in this session, say so to the user and do not claim the work was delegated.

## C2. Commits (for §5)

Git commits: the `commit` skill is user-run — suggest the user type `$` and pick `dev-bingfa:commit` (or pick it from `/skills`) — or delegate to `bingfa-implementer`. The main conversation authors no commits itself, ever. (Invoking `dev-bingfa:commit` this way follows the Codex documentation; it has not yet been tested with this package.)

## C3. Optional save-time check

The optional `dev-bingfa-check` plugin may be installed, but on Codex it is **not verified to run**: Codex runs plugin hooks only after the user trusts them in `/hooks`, and no run inside a real Codex session has been observed yet. Never claim the check ran. Before delivering any change to a Python file, check it yourself: every broad `except` (bare, `Exception`, `BaseException`) whose body is only `pass` is a silent failure (§7) — fix it, or state where the user can see that failure. If the check does report one, treat it the same way.

## C4. Invoking skills

- Skills appear with their plugin prefix: `dev-bingfa:brownfield-recon`, `dev-bingfa:blast-radius`, `dev-bingfa:seam-audit`, `dev-bingfa:commit`, and `mattpocock-skills:<name>` for Matt Pocock's skills, e.g. `mattpocock-skills:tdd`, `mattpocock-skills:code-review`, `mattpocock-skills:pr`.
- The user starts a skill by typing `$` and picking it, or via `/skills` (Codex documentation; not yet tested with this package). When suggesting a *(user-run)* skill from §6, give the user the full prefixed name, e.g. `mattpocock-skills:grill-me`, `mattpocock-skills:to-spec`.
- *(user-run)* is enforced by rule text here, not by Codex. Codex ignores the Claude Code setting `disable-model-invocation`; it only hides skills that ship their own Codex setting, and Codex loads more of Matt Pocock's skill folders than his plugin list (at least one manual-only skill was seen in the automatic list). So: never start a skill marked *(user-run)* in §6, or any skill whose own instructions say it is manual-only, even if Codex offers it to you — suggest the user run it.
