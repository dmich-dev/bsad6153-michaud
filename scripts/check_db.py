"""Week 2 database check. Run it from the project folder:

    python scripts/check_db.py          # connects as the owner (DATABASE_URL)
    python scripts/check_db.py --app    # connects as the read-only role (APP_DATABASE_URL)

It confirms that your connection string works and shows which database user you
are connected as. It never prints the connection string, which contains your password.
"""

import os
from pathlib import Path
import sys

import psycopg
from dotenv import load_dotenv


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    # Bind dotenv to this project; never search parent directories.
    try:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    except (OSError, UnicodeError):
        print("[FAIL] Could not read project .env configuration.")
        return 1

    variable = "APP_DATABASE_URL" if "--app" in argv else "DATABASE_URL"
    url = os.environ.get(variable)

    if not url or not url.strip():
        print(f"[FAIL] {variable} is not set. Add it to your .env file (see .env.example).")
        return 1

    try:
        # connect_timeout keeps a wrong address from hanging forever.
        with psycopg.connect(url, connect_timeout=10) as conn:
            version, user = conn.execute("select version(), current_user").fetchone()
    except (psycopg.Error, UnicodeError):
        # Driver diagnostics can contain the connection string or password.
        print(f"[FAIL] Could not connect using {variable}.")
        print("       Check: Supabase Session pooler string? Correct password? Project paused?")
        return 1

    print(f"[ok] Connected using {variable}")
    print(f"     Database user: {user}")
    print(f"     Server: {version.split(',')[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
