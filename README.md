# BSAD 6153 Project: Agent Model Selection

**Student:** David Michaud (DJ)
**My decision:** Choose an AI model for coding or agent tasks, a decision I make daily.
**Website:** Milestone 4 review branch. No verified public HTTPS address yet. The private catalogue preview is not the public deployment.

This repository is one complete AI system, built over eight weeks: a real API, synced on a schedule into a
PostgreSQL database, shown on a public website, with a chatbot and an agent that answer and act from your
own data. You build it with an AI coding agent, and you read and verify everything it writes.

## Decision and data

I find it hard to choose a model consistently because new models seem to come out every other day.

This project will compare current API prices, context limits, and advertised tool support from the
[OpenRouter model catalog](https://openrouter.ai/api/v1/models). Those fields can support a shortlist;
they are not measurements of coding quality or reliability. API price estimates will be kept separate
from personal subscriptions and access provided through Newman.

The [baseline log](docs/baseline_log.md) records the current decision process before the system is built.
No model benchmarks or time savings have been measured for this project yet.

---

## Setting up your computer (Week 1 Setup)

You need a **Windows 10/11 or macOS computer where you can install software**, Git, Python 3.12, and your AI
coding agent (Claude Code, Codex, Antigravity, or Copilot). Let your agent help with the installs, but read
every command before you approve it, and keep auto-approve off.

1. **Clone this repository** into a short folder path that isn't synced by OneDrive or Dropbox, for example
   `C:\dev\bsad6153` on Windows or `~/dev/bsad6153` on macOS.
2. **Create and activate a virtual environment** from the project folder:

   | | Windows (PowerShell) | macOS (Terminal) |
   |---|---|---|
   | Create | `py -3.12 -m venv .venv` | `python3.12 -m venv .venv` |
   | Activate | `.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |

   You'll see `(.venv)` at the start of your prompt when it's active. Activate it every time you open a new terminal.
3. **Install the packages:** `pip install -r requirements.txt`
4. **Create your secrets file:** copy `.env.example` to `.env`, and put a fake value on the `TEST_SECRET=` line.
5. **Check everything:** `python scripts/check_setup.py` should end with `Setup OK`.
6. **Try the website:** `streamlit run app/streamlit_app.py` opens it in your browser. Press Ctrl+C to stop it.

### Working with your AI agent

- **You approve every command.** Read it first, and if you don't understand it, ask the agent what it does.
- **Ask for a plan before code:** "Before writing anything, tell me your plan."
- **Never paste a real key into the chat,** and never ask the agent to print your `.env` file.
- **The agent never gets the owner database password or deploy tokens.** That's how agents delete databases.
- **Record what you directed, read, verified, and decided** in each pull request's AI review log.

---

## Project layout

| Folder | What goes there | When |
|---|---|---|
| `ingest/` | Fetch, load, and sync code | Weeks 1&ndash;3 |
| `db/` | `schema.sql`, `roles.sql`, `queries.sql` | Weeks 2&ndash;6 |
| `docs/` | Data dictionary, logs, reports (see `docs/README.md`) | Every week |
| `evals/` | Golden questions and evaluation runs | Weeks 3&ndash;7 |
| `app/` | Your website (Streamlit) | Weeks 4&ndash;6 |
| `examples/` | A reference tool-using chatbot loop | Week 5 |
| `scripts/` | Setup and database checks | Weeks 0&ndash;2 |
| `data/sample/` | A small sample of raw API data (large downloads go in `data/raw/`, which Git ignores) | Week 1 |

## Secrets: where each one lives

| Secret | On your computer | On Render (website) | In GitHub Actions (sync) |
|---|---|---|---|
| `DATABASE_URL` | private SQL administrator connection for provisioning only | **never** | `catalog-production` environment secret: **dedicated sync writer only; never the owner** |
| `APP_DATABASE_URL` (read-only) | `.env` | environment setting | no |
| `AGENT_DATABASE_URL` | not used by this website | no | no |
| LLM key, `APP_PASSWORD` | not used by this website | no | no |
| Data API key | not needed by the sync | no | no; the OpenRouter catalog is fetched anonymously |

`.env.example` lists the names only. If a secret ever leaks, revoke or rotate it first, then tell the instructor.

---

## Deploying on Render (Week 4)

**Run locally:** In a project virtual environment, `python -m pip install -r requirements-app.txt`. Make only `APP_DATABASE_URL` available to the app using the private `app_reader` session-pooler URI; do not run it with the administrator or sync writer's environment. From the project root: `python -m streamlit run app/streamlit_app.py --server.address 127.0.0.1`. The tested data source is the existing project database, not an embedded sample. The checked-in `db/supabase-root-2021.crt` is a public trust certificate, not a password.

**Cache:** The planned cache lifetime is five minutes. The sync runs daily and the freshness target is 24 hours. A one-day cache could hide an entire successful update; querying the pooler on every widget interaction would repeat identical work. A five-minute cache bounds the normal visibility delay for a particular query after a committed update. The banner uses the most recent successful **sync**, not the time a visitor opened the page. See the code tour and direct database checks for the implementation.

**Public release:** Confirm permitted display of the selected metadata before publishing; public API access and attribution do not, on their own, settle republication rights. Following review, release the approved app on `main`, then create a **Free web service** using `render.yaml`. Only `APP_DATABASE_URL` is requested as a secret. Do not copy a general-purpose `.env`, owner URL, writer URI, LLM API key, or private usage logs into Render. The platform provides `PORT`. Free web services can sleep after 15 minutes without traffic and take about a minute to wake ([Render documentation](https://render.com/docs/free)). A green health endpoint checks that Streamlit started, not that the catalogue can reach its database.

**Domain:** Claim the student benefit if eligible. Record the actual renewal price and currency before accepting it. Add the custom domain in Render, then use **that service's** exact DNS targets at the registrar. A CNAME aliases a hostname to Render; an A record points a hostname at an IPv4 address; an ALIAS/ANAME can give an apex host a provider-managed target without using a conventional CNAME. Only add verification records if requested, and leave mail records alone. Once DNS and the certificate are ready, open the HTTPS site without credentials and verify both live views. Add the verified URL at the top of this README. If student approval is pending at the deadline, the instructor accepts the verified `onrender.com` URL with an actual pending-application screenshot; redact private education documents, identifiers and codes.

---

## Troubleshooting

- **`pip install` fails with "No such file or directory" on Windows:** the folder path is too long. Move the
  project to a short path such as `C:\dev\bsad6153` and recreate `.venv`.
- **PowerShell says running scripts is disabled when you activate:** use Command Prompt instead and run
  `.venv\Scripts\activate.bat`, or ask the instructor. Don't change system security settings without asking.
- **`python` opens the Microsoft Store or isn't found:** use `py -3.12` on Windows or `python3.12` on macOS.
- **The database check can't connect:** use Supabase's Session pooler string, check the password, and check
  that your Supabase project isn't paused.

---

## Project proposal (Week 1)

<!-- About 300 words: data source and backup API, your decision and workflow (from your baseline log),
     your first agent idea, and risks. See the Week 1 page. -->

## How to run this project

<!-- Keep this current: how to run the sync, the website, and the evaluations. -->

## Credits

<!-- Your data API's required attribution, plus any open-source code or samples you used. -->

## Milestone 3: production catalog sync

**Schedule:** daily at **09:17 UTC** (`17 9 * * *`). A maintainer can also use **Actions → Catalog sync → Run workflow → main**. The production job accepts only this repository’s `main`; other refs fail without receiving the environment secret. No PR, push, fixture or dry-run trigger is configured.

### Enable once

1. As database administrator, review the SQL privately. For an **empty** PostgreSQL 15+ database, apply `db/schema.sql`, then `db/milestone3.sql` and `db/roles.sql`, stopping on errors. For an existing Milestone 2/3 database, compare its schema and grants to those files; **do not rerun the baseline, drop data, or replace a working `app_reader`**. Only apply a missing reviewed migration. Confirm that `app_reader` can select the catalog and `sync_runs` but cannot write them.
2. In the target database, privately run `db/sync_writer.sql` once as the administrator. This creates a **new** `catalog_sync_writer`; a collision or inherited write/DDL privileges abort the transaction. It grants no membership, ownership, grant options, sequence management, DELETE or schema CREATE. It grants column-specific inserts and updates on the six sync tables. Keep public writable schemas, privileged user-defined `SECURITY DEFINER` routines, and unsafe triggers out of reach of this login; review these and row-level policies before activation. The script does not change PUBLIC grants, RLS, or existing roles. Ordinary PUBLIC connection, temporary-object and function privileges are not revoked. If the checks fail, investigate rather than granting a broader role.
3. Set a unique generated password privately (e.g. the interactive `\password catalog_sync_writer` command in an authenticated `psql` administrator session). Keep it out of shell history, repository files, logs and chat. In GitHub **Settings → Environments**, create/verify `catalog-production` and restrict **deployment branches/tags to the branch `main` only**, with no tag patterns. Protect `main` and review changes to the workflow, ingestion code and dependency lock. For unattended schedules, do not enable a mandatory per-run human reviewer unless you intend to approve each run.
4. In **that environment only**, set `DATABASE_URL` to the writer’s Supabase PostgreSQL URI. Do not also define a repository/organization fallback secret of that name. Use the project’s **Session pooler**, port `5432`, database `postgres`, username `catalog_sync_writer.<project-ref>`; percent-encode reserved characters in the password. A direct `db.<project-ref>.supabase.co` connection uses username `catalog_sync_writer` and requires runner connectivity. Use `postgresql://` and no query string, fragment or local certificate path. Transaction poolers on `6543` are not suitable for session advisory locking. The sync enforces `verify-full`, checks the actual database identity and resolves `db/supabase-root-2021.crt` from the checkout. The public CA’s file SHA-256 is `700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7`; verify against the [Supabase Studio certificate configuration](https://github.com/supabase/supabase/blob/4a73166675642dc3c1d1fc767a65adbee746d894/apps/studio/hooks/custom-content/custom-content.json) when rotating. Never put the `postgres` URI, the reader URI, or an OpenRouter key in this workflow.
5. Enable Actions and land the reviewed workflow on default branch `main`. Dispatch once from `main`. Verify an actual fetch and the matching committed row below. A manual success is **not** scheduled-run evidence. The schedule can start late; count only completed jobs with event `schedule` and a corresponding successful nonempty `sync_runs` row. An unchanged snapshot is a real fetch (positive fetched count, zero inserted/updated), not a skipped job.

```sql
SELECT run_id, trigger, started_at, finished_at, status,
       records_fetched, records_inserted, records_updated, error_message
FROM public.sync_runs ORDER BY run_id DESC LIMIT 10;
```

**Coverage and failure behavior.** The source is [OpenRouter catalog metadata](https://openrouter.ai/api/v1/models), not inference. Each attempt paginates the full catalog and samples provider details for up to ten recent text/tool-capable models. This is a full retrieval followed by SHA-256 change detection, not a source modification cursor. Equal payloads retain their timestamps; missing records are not deleted. An incomplete/invalid snapshot does not advance the checkpoint. Counts of inserted/updated rows span four normalized tables and need not equal the number of fetched source records. The workflow fails on a partial run, missing secret or unavailable database. If the DB is unreachable before the attempt is logged, only the failed Actions run can serve as evidence. Temporarily disable **Catalog sync** in Actions to pause; rotate/revoke the writer credential privately if necessary.

**Local verification (no hosted database):** on Linux x86-64/Python 3.13, install `requirements-sync.txt` in a fresh venv with `--only-binary=:all: --require-hashes`; run `python -I -B -m unittest discover -s tests` and `python -I -B tests/accept_postgres.py --pg-bin /path/to/postgresql/17/bin`. The latter creates, tests and stops its own disposable cluster in `TMPDIR`; use a private, short, writable path as a non-root OS user. It does not accept an existing database URL.
