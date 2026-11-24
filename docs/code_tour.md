# Code tour: from a filter to a displayed price

AI-prepared tour for DJ to check. The line numbers below refer to the two source files linked here, not the starter. The last column is for DJ's own ✔ or ✘ and correction; a blank does not mean approved.

## [app/streamlit_app.py](../app/streamlit_app.py): what the visitor sees

| Lines | Claim to check against the source | DJ's check |
|---|---|---|
| 8, 11–23 | The TTL is 300 seconds. There are three independent data caches: last successful check, shortlist by minimum context **and** sampled-route filter, and routes by selected model ID. On a hit the wrapper returns cached data without opening a connection. | |
| 33–48 | A change in either filter feeds `ranked_entries` at line 40. The page states the workload, handles an empty shortlist and renders the returned rows without recalculating their prices. `rate` (26–30) formats decimal values without rounding; missing is not zero. | |
| 51–68 | Line 58 selects a catalogue ID from the shortlist; line 59 requests its sampled routes. An empty shortlist and an entry without matching sampled routes have different messages. A missing route limit or rate is shown as “Not listed.” | |
| 71–86, 92–94 | The banner runs before either result table. Its input is the stored successful finish time. On **each page run**, it converts that time to UTC and computes age against the clock, even if the timestamp came from cache. No success, a future time, or an age strictly over 24 hours gets a warning. This is not a continuously ticking clock in an idle tab. | |
| 92–105 | The UI catches `CatalogueUnavailable` at 95–96, shows a fixed retry message and still renders About. This file reads no credential and opens no connection; lines 13, 18 and 23 call the data module, not PostgreSQL directly. About attributes the metadata to OpenRouter and explains sampling and cold starts. | |

## [app/catalogue.py](../app/catalogue.py): what can reach PostgreSQL

| Lines | Claim to check against the source | DJ's check |
|---|---|---|
| 14–33 | The only environment **value** read is `APP_DATABASE_URL`, at line 18. Line 16 checks for `PG`-prefixed environment **names** and refuses to proceed if present. Lines 20–28 validate the project-qualified reader login, Supabase Session pooler host, database and port. The app does not discover `.env` or fall back to an owner login. | |
| 29–33, 38–42 | `psycopg.connect` opens the connection at **38**. It uses `verify-full`, the repository CA and a six-second connection timeout, then checks that TLS is in use. Lines 41–42 set the transaction to repeatable-read, read-only and limit statement time to eight seconds. | |
| 43–50 | The identity query executes at 43–45; **both** `session_user` and `current_user` must be `app_reader` and the transaction must report `on`. Only then does line **48** execute the requested data query with its separate parameters. Driver/parsing/OS errors become a detail-free exception at 49–50; explicit guard failures also abort. | |
| 90–91 → 48 | Freshness binds `success` and selects `max(finished_at)` from `public.sync_runs`. It does not select the latest attempted run, latest catalogue row, or page-load time. | |
| 53–70 → 48 | The shortlist SQL filters for text output, advertised tools, context and known base rates. The optional `EXISTS` checks for a sampled tool route without duplicating models. SQL calculates the example price, orders by it and catalogue ID and returns up to 20. Line 70 binds both widget values. | |
| 73–87 → 48 | The route SQL joins endpoints to providers and catalogue entries, filters `c.catalog_id = %s` and checks tool support on the route itself. The catalogue ID goes into a one-item parameter tuple at 87. Prices and limits in this view come from the **endpoint**, not from the catalogue row. | |

### An actual implementation correction

The first reader validator used `(url.port or 5432) == 5432`. A synthetic URL explicitly specifying port `0` reached the mocked connection as port `5432`: Python treated zero like a missing value. The failing regression recorded one attempted connection. The corrected expression at `catalogue.py:24` accepts only `None` (not specified) or `5432`; the same test then recorded no attempted connection. This was an assistant-found code defect during testing, not a student finding or a fabricated incorrect tour claim. No real credential or network connection was used in that regression.

DJ: check each row against the linked source. If a tour claim is actually wrong, preserve its original wording, mark it ✘, and write the corrected explanation and line(s). The implementation correction above is not a substitute for that personal check.
