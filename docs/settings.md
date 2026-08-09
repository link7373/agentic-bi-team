# Permissions and Safety Rails

> Created by Colin Beck — https://www.linkedin.com/in/beckcolin/

`.claude/settings.json` is the team's permission posture. JSON can't carry comments, so
the reasoning lives here. Everything in it is a default you should adjust — a team with
a read-only replica can loosen it, a team pointed at production should tighten it.

`CLAUDE.md` §8 already tells agents to confirm before destructive or outward-facing
actions. That's a prompt, and prompts are guidance, not controls. This file and the hook
are the controls.

## The three lists

**`allow`** — runs without prompting. Reading files, searching, and the team's own
standard-library scripts. These are read-only or self-contained, and prompting for them
just trains people to click through prompts, which is how the important prompt gets
approved by reflex.

**`ask`** — prompts every time. Every database client is here, deliberately. A query is
usually harmless and occasionally very expensive, and the difference isn't visible in
the command. Also here: `git commit` and `git push` (the repo is the audit trail;
committing is a decision), `pip install` (the kit is standard-library-only for a reason
— see `CONTRIBUTING.md`), and `WebFetch`.

**`deny`** — never, no prompt. Two groups:

- *Credential files.* `.env`, `*.pem`, `*.key`, `credentials.json`,
  `service-account*.json`. These are already gitignored, but gitignore stops them
  reaching GitHub, not an agent's context window. A secret an agent never read cannot be
  echoed into a transcript, a log, or a deliverable. When a command needs a credential,
  it references the environment variable — the shell reads the value, the agent doesn't.
- *Irreversible shell operations.* `rm -rf`, `git push --force`, `git reset --hard`.
  If one of these is genuinely needed, a human runs it.

## The destructive-SQL hook

`scripts/hooks/block_destructive_sql.py` runs before every Bash call. It blocks when a
command **both** invokes a database client **and** contains a statement that destroys
data, destroys structure, or changes access: `DROP`, `TRUNCATE`, `DELETE`/`UPDATE`
without a `WHERE` clause, `GRANT`/`REVOKE`, `ALTER TABLE ... DROP`.

Two design choices worth knowing:

- **It only fires on commands containing a database client**, so your ordinary shell
  work is untouched. `rm -rf build/` is not its business (the deny list handles that).
- **It does not parse SQL.** A regex that pretends to understand SQL is worse than one
  that admits it doesn't. It matches statement keywords in the command text, which means
  it can be fooled by a sufficiently indirect command — it is a guard against accidents,
  not against a determined attempt to work around it.

When it blocks, the model sees an explanation and instructions: describe what would be
destroyed, get explicit confirmation, and prefer the idempotent rebuild patterns
(`CREATE OR REPLACE`, `MERGE`, delete-insert by partition) from
`standards/sql-and-data-standards.md`.

The escape hatch is prefixing the command with `AGENTIC_BI_ALLOW_DESTRUCTIVE=1`. Having
to type that out is the entire point — it converts an accident into a decision.

To disable the hook, remove the `hooks` block from `.claude/settings.json`. Consider
tightening the database credential to read-only instead; a read-only role makes the hook
redundant, which is a better outcome than turning it off.

## Read-only credentials beat every rule here

The strongest control isn't in this file. Point the team at a **read replica or a
read-only role** and the entire destructive-action problem becomes an error message from
the warehouse. `/connect-data` asks for this during setup. Everything above is defence
for the case where you can't.

## Local overrides

Personal adjustments go in `.claude/settings.local.json`, which is not tracked. Use it
for machine-specific paths or to allow a client you use constantly. Don't loosen the
credential deny list there — that one protects the transcript, not the warehouse.
