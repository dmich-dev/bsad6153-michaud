#!/usr/bin/env bash
# One server-side terminal for an actual Milestone 2 recording, not saved output.
set -u
umask 077
project="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)" || exit 2
cd -- "$project" || exit 2
# Never let an inherited URL, libpq option or Python path select another target.
unset DATABASE_URL APP_DATABASE_URL PGHOST PGHOSTADDR PGPORT PGDATABASE PGUSER
unset PGPASSWORD PGSERVICE PGSERVICEFILE PGOPTIONS PYTHONPATH PYTHONHOME PYTHON_DOTENV_DISABLED
export PGSSLMODE=require
export TERM=xterm-256color
for file in .venv/bin/python data/raw/milestone2-verified-20261107/summary.json data/raw/milestone2-verified-20261107/models.json data/raw/milestone2-verified-20261107/endpoints.json; do
    if [[ ! -s "$file" ]]; then
        printf 'STOP: required project file is missing: %s\n' "$file" >&2
        exit 2
    fi
done
if ! command -v timeout >/dev/null 2>&1; then
    printf 'STOP: the server timeout command is unavailable. No replay started.\n' >&2
    exit 2
fi
printf 'Milestone 2: checking the real database connection...\n'
timeout --foreground --signal=INT --kill-after=5s 20s .venv/bin/python -I -B scripts/check_db.py
check_status=$?
if [[ $check_status -ne 0 ]]; then
    printf 'STOP: connection check failed (exit %s). No replay started.\n' "$check_status" >&2
    exit "$check_status"
fi
printf '\nREADY FOR RECORDING. Leave this same server terminal open.\n'
printf 'At script step 3, press Enter here to run the actual replay.\n'
printf 'Press Enter to start, or type q then Enter to cancel: '
if ! IFS= read -r answer; then
    printf '\nCanceled; no replay started.\n'
    exit 130
fi
if [[ -n "$answer" ]]; then
    printf 'Canceled; no replay started.\n'
    exit 130
fi
printf '\nStarting the actual loader. Progress below comes from the real run.\n'
timeout --foreground --signal=INT --kill-after=10s 120s .venv/bin/python -I -B ingest/load.py --run-dir data/raw/milestone2-verified-20261107
loader_status=$?
printf 'Loader exit code: %s\n' "$loader_status"
if [[ $loader_status -ne 0 ]]; then
    printf 'STOP: replay did not complete successfully. Do not read the success paragraph.\n' >&2
    printf 'Check the real database counts before retrying.\n' >&2
    exit "$loader_status"
fi
printf 'Replay finished successfully. Now compare your actual before/after counts in Supabase.\n'
printf 'Keep this result visible. Press Enter only when you have finished recording.\n'
IFS= read -r finished || true
exit 0
