# AGENTS.md

MindForge is a fresh project scaffold. There is **no application code yet** — this directory currently contains only the OpenCode skills/config setup and the docs placeholders. Git is initialized (`main`, no commits yet).

## Repo layout

- `.agents/skills/` — 22 OpenCode skills (superpowers + design skills). Registered via `opencode.json` → `skills.paths`.
- `.opencode/plugins/superpowers.js` — auto-discovered plugin that injects the using-superpowers bootstrap and registers the skills dir at config time. Do not remove; restart opencode after editing.
- `.opencode/plans/` — implementation plans, named `YYYY-MM-DD-<topic>.md`.
- `docs/PRD`, `docs/TRD` — placeholder files for product / technical requirements.

## Gotchas

- **`.gitignore` ignores the entire OpenCode scaffold:** `docs/`, `opencode.json`, `skills-lock.json`, `.agents`, `.opencode/`. Only application code and AGENTS.md get committed. Commit steps inside the superpowers skills (brainstorming spec commits, TDD, plan execution) target the project files, not the scaffold.
- **Client commands run via `--prefix client`.** There is no root `package.json`; frontend commands live in `client/` (see "Client commands" below). Do not invent scripts like `./scripts/run.sh` — they referenced the old project and were removed.
- **`skills-lock.json` is stale** (lists 17 skills; 22 are installed) and its hash algorithm isn't reproducible. It's informational only — never hand-edit it or use it to verify installations. New installs via `npx skills add` update it automatically.
- **`docs/PRD` / `docs/TRD` are the doc convention**, not the brainstorming skill's default `docs/superpowers/specs/`. Follow the PRD/TRD split for product vs technical requirements.

## Skills

- Skills auto-load from `.agents/skills/` — no install step needed. Load via the `skill` tool.
- Global `graphify` skill lives at `~/.claude/skills/graphify` (outside this repo).
- Skill files under `.agents/skills/` are managed artifacts; treat them as reference material, not project code.

## Client commands

- `npm run dev --prefix client` — Vite dev server on :5173
- `npm run test --prefix client` / `npm run test:watch --prefix client` — vitest (jsdom)
- `npm run build --prefix client` — `tsc -b` + `vite build`
- `npm run lint --prefix client` — oxlint

## Design

- "Before any UI/design work: read `design/` (spec/design.md + tokens).
