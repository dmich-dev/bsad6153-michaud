# BSAD 6153 Project: Agent Model Selection

**Student:** David Michaud (DJ)
**My decision:** Choose an AI model for coding or agent tasks, a decision I make daily.
**Website:** Planned for Week 4.

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
| `DATABASE_URL` (owner) | `.env` | **never** | Actions secret |
| `APP_DATABASE_URL` (read-only) | `.env` | environment setting | if your checks need it |
| `AGENT_DATABASE_URL` | `.env` | environment setting | no |
| LLM key, `APP_PASSWORD` | `.env` | environment setting | no |
| Data API key | `.env` | no | Actions secret |

`.env.example` lists the names only. If a secret ever leaks, revoke or rotate it first, then tell the instructor.

---

## Deploying on Render (Week 4)

1. Claim your free domain through the GitHub Student Developer Pack.
2. In Render, choose **New &gt; Blueprint**, pick this repository, and enter each secret when asked.
   (`render.yaml` describes the service.) Or create a **Web Service** by hand with:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run app/streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
   - Environment variables: `PYTHON_VERSION=3.12.4`, `APP_DATABASE_URL`, and later your LLM key and `APP_PASSWORD`
3. Under **Settings &gt; Custom Domains**, add your domain, then add the DNS records Render shows you at your
   registrar. Ask your agent to explain each record before you add it. HTTPS turns on automatically.
4. Free services sleep when idle and take about a minute to wake. Say so on your site.

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

**Assistant-prepared proposal for DJ's review, updated November 1.** Source approval and DJ's own
workflow evidence remain pending. This proposal describes intended work, not a completed system.

Agent Model Selection supports a daily decision: which AI model to use for coding or agent tasks.
Frequent releases make consistent selection difficult. The current baseline contains one reconstructed
report of heavy 6.1 sol use for homelab tasks; timing, comparison sources, and confidence were not
recorded. Additional genuine entries and reflections are needed before drawing conclusions about the
workflow or claiming improvement.

The primary source is OpenRouter's model catalog, already named in the submitted repository setup.
It supplies advertised prices, context limits, modalities, and supported request parameters. Related
serving-endpoint records describe provider-specific offerings. The importer is planned to collect the
broader catalog with real pagination, preserve raw responses, and report distinct catalog IDs alongside
canonical identities. A later coding shortlist would filter suitable text-output and tool capabilities;
the entire catalog is not a list of equally suitable coding models.

Models.dev is the proposed backup. Its model metadata and provider offerings could support a separate
adapter, but identifiers, price units, update behavior, and attribution must be checked before use.
Source labels must remain visible so different providers' prices are not silently treated as identical.

By Week 6, the proposed agent would create a local shortlist and a change report using task constraints
such as budget, context requirements, and advertised tools. DJ would review its recommendation.
Purchases, subscription changes, and transmission of task content would require approval. These are
proposed boundaries for DJ to verify against his actual workflow.

Risks include missing fields, aliases, conflicting endpoint limits, stale pricing, rate limits,
authentication changes, and public-display terms. The design should retain timestamps and provenance,
back off on errors, and preserve unknown values. Metadata supports comparison; it does not establish
measured coding quality, reliability, personal subscription costs, or time savings.

See the [data dictionary](docs/data_dictionary.md), [documentation review](docs/api_check_2026-10-31.md), and
[remaining milestone checklist](docs/milestone1_checklist.md). The fetch pipeline is not implemented yet.

## How to run this project

The Week 1 setup commands above remain the documented setup workflow. The milestone importer is not
implemented yet, so there is no verified fetch/run command to present. Exact commands and observed
results will be added after the required API check, code review, and real clean-start/rerun verification.

Current evidence and remaining work are tracked in [submission readiness](docs/submission_readiness.md).

## Credits

- Public catalog and serving data: [OpenRouter](https://openrouter.ai/), with [API documentation](https://openrouter.ai/docs/)
  and [terms](https://openrouter.ai/terms). Public-display permission remains to be confirmed before Week 4.
- Proposed backup: [Models.dev](https://models.dev/), an open-source model database with an
  [MIT-licensed repository](https://github.com/anomalyco/models.dev). It has not been integrated.
- Codex assisted with API research, the small public-data sample, and draft documentation/proposal on
  October 29, 2026. DJ's review remains pending; the baseline observations were not generated or edited.
