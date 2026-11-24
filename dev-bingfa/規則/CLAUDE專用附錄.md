# Claude Code Appendix

Append this after the common rules in `~/.claude/CLAUDE.md`. Everything here is valid only in Claude Code.

## A1. Subagent names (for §5)

The `dev-bingfa` plugin ships three subagents. Plugin agents carry the plugin prefix, most likely `dev-bingfa:explorer`, `dev-bingfa:implementer`, `dev-bingfa:web-search-agent`; the exact names are shown in `/agents`.

- Investigation subagent (§5) → `explorer`.
- Implementation subagent (§5) → `implementer`.
- Internet research (debugging an error, finding solutions across sources) → `web-search-agent`.

## A2. Commits (for §5)

Git commits: the `commit` skill is user-run — suggest the user type `/dev-bingfa:commit` — or delegate to the `implementer` subagent. The main conversation authors no commits itself, ever.

## A3. Optional save-time check

If the optional `dev-bingfa-check` plugin is installed, it checks each Python file right after it is written and feeds back any broad `except` whose body is only `pass` (a silent failure, see §7). When it reports one, fix it or state where the user can see that failure. If the plugin is not installed, this check is off — do not claim it ran.

## A4. Invoking skills

- Skills marked *(user-run)* in §6 come from the `mattpocock-skills` plugin and only start when the user types them: `/mattpocock-skills:<name>`, e.g. `/mattpocock-skills:grill-me`, `/mattpocock-skills:to-spec`. When suggesting one, give the user that full command.
- Model-invocable Matt skills in §6 (`tdd`, `code-review`, `pr`) also use the full name: `mattpocock-skills:tdd`, `mattpocock-skills:code-review`, `mattpocock-skills:pr`. In particular, `code-review` in §6 means `mattpocock-skills:code-review`, not Claude Code's built-in `code-review` command of the same name.
- Skills shipped in this package carry the `dev-bingfa:` prefix, e.g. `/dev-bingfa:brownfield-recon`, `/dev-bingfa:blast-radius`, `/dev-bingfa:seam-audit`.
