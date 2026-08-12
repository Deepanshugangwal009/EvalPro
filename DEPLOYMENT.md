# EvalPro — Deployment Guide

## Stack

- Python 3.12 / Flask 3 with blueprints (`auth`, `admin`, `student`, `exam`, `result`)
- Jinja2 templates + Bootstrap 5 from CDN, plain JavaScript (no build step)
- **MySQL** accessed with `mysql-connector-python` using raw SQL
- The database is not just tables: it also uses **two SQL views**
  (`student_performance_view`, `exam_statistics_view`) and **two stored procedures**
  (`sp_generate_result`, `sp_subject_report`), which the admin reports page calls
- `gunicorn` as the production WSGI server

The stored procedures and views are the deciding factor for hosting: the database
provider must be a real MySQL server that allows `CREATE PROCEDURE` and
`CREATE VIEW`. **TiDB Cloud is not usable here** — it is MySQL-compatible but does
not support stored procedures.

## Recommended hosting

### Best option — PythonAnywhere Free (app **and** database on one service)

| Question | Answer |
| --- | --- |
| Backend runs there? | Yes — it is a Python/WSGI host |
| Frontend runs there? | Yes — Jinja templates and `static/` are served by the same app |
| Database included? | **Yes — the free plan includes a real MySQL database** |
| Separate DB provider needed? | **No** |
| Genuinely free? | Yes, and the site does **not** sleep |
| Beginner friendly? | Yes — web UI, no Docker, no build pipeline |

Free-plan limits: one web app at `yourname.pythonanywhere.com`, 512 MB disk,
low CPU-seconds quota, you must click "Run until 3 months from today" every
3 months, and outbound internet is restricted to a whitelist (irrelevant here —
the database is internal).

### Alternative — Render Web Service (Free) + Aiven for MySQL (Free)

Use this if you want deploy-on-git-push. The web service is free and
`render.yaml` is included, but **Render offers no MySQL**, so the database must
come from a separate provider. Aiven's free MySQL plan (1 GB, no backups)
supports procedures and views. Render free services sleep after 15 minutes idle.

Not suitable: Netlify and Vercel (no persistent Python server + no MySQL).

## PythonAnywhere — step by step

1. **Prepare the repository.** From the `oes` folder: `git init`, `git add .`,
   `git commit -m "EvalPro"`, push to a GitHub repo named `EvalPro`.
   Confirm `.env` is not committed.
2. **Create the account** at <https://www.pythonanywhere.com> (Beginner / free).
3. **Create the database.** *Databases* tab → set a MySQL password → create a
   database named `oes_db`. PythonAnywhere will actually name it
   **`yourname$oes_db`** — that full name is what you put in `MYSQL_DATABASE`.
   Note the host shown on that page: `yourname.mysql.pythonanywhere-services.com`.
4. **Clone the code.** *Consoles* tab → Bash:
   ```bash
   git clone https://github.com/<you>/EvalPro.git
   cd EvalPro
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. **Create `.env`** in the project folder (`nano .env`):
   ```
   SECRET_KEY=<a long random string>
   MYSQL_HOST=yourname.mysql.pythonanywhere-services.com
   MYSQL_PORT=3306
   MYSQL_USER=yourname
   MYSQL_PASSWORD=<your MySQL password>
   MYSQL_DATABASE=yourname$oes_db
   MYSQL_SSL=0
   SESSION_COOKIE_SECURE=1
   ```
6. **Create the schema, views, procedures and seed data:**
   ```bash
   python init_db.py
   ```
   This is the step that replaces running the `.sql` files by hand — it strips the
   `USE oes_db;` lines and handles the `DELIMITER $$` blocks that a plain SQL
   client would choke on, and applies everything to whatever database you configured.
7. **Create the web app.** *Web* tab → *Add a new web app* → **Manual configuration**
   → Python 3.12. Then set:
   - *Source code*: `/home/yourname/EvalPro`
   - *Virtualenv*: `/home/yourname/EvalPro/venv`
   - *WSGI configuration file*: replace its contents with
     ```python
     import sys
     path = '/home/yourname/EvalPro'
     if path not in sys.path:
         sys.path.insert(0, path)
     from wsgi import app as application
     ```
   - *Static files*: URL `/static/` → Directory `/home/yourname/EvalPro/static/`
8. **Reload** the web app and open `https://yourname.pythonanywhere.com`.
9. **Test:** log in at `/admin/login` as `admin` / `admin123`, **change that
   password immediately**, create a subject → an exam → questions, then register a
   student, take the exam, and check `/result/...` and `/admin/reports`
   (the reports page proves the views and stored procedure are working).

## Render + Aiven — step by step

1. Push the repo to GitHub as above.
2. Create a free MySQL service at <https://aiven.io>; copy the service URI.
3. Run the database setup **from your own machine** against the remote database:
   ```bash
   set DATABASE_URL=mysql://user:password@host:port/defaultdb
   set MYSQL_SSL=1
   python init_db.py
   ```
   (on Windows PowerShell use `$env:DATABASE_URL = "..."`)
4. On <https://render.com>, *New → Web Service*, connect the repo. `render.yaml`
   sets Runtime = Python, Build = `pip install -r requirements.txt`,
   Start = `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`.
5. Add environment variables: `SECRET_KEY`, `DATABASE_URL`, `MYSQL_SSL=1`,
   `SESSION_COOKIE_SECURE=1`, `FLASK_ENV=production`.
6. Deploy and test as in step 9 above.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key. **Required** on any hosting service — the app exits if it is missing there. |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_USER` / `MYSQL_PASSWORD` / `MYSQL_DATABASE` | database connection |
| `DATABASE_URL` | optional single connection string that overrides the five variables above |
| `MYSQL_SSL` | `1` when the MySQL server is remote and requires TLS |
| `MYSQL_SSL_CA` | optional path to the provider's CA certificate |
| `MYSQL_POOL_SIZE` | connection pool size (default 3) |
| `SESSION_COOKIE_SECURE` | `1` when served over HTTPS |
| `PASS_PERCENTAGE` | pass mark, default 40 |
| `FLASK_DEBUG` | keep `0` in production |

## Manual database setup you must perform

- Create the database (PythonAnywhere: via the Databases tab; Aiven: `defaultdb`
  already exists).
- Run `python init_db.py` **once**. Nothing in the app creates tables at runtime.
- Change the seeded `admin` / `admin123` login straight after the first deploy —
  that hash is committed in `database/seed.sql`.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `SECRET_KEY must be set when running on a hosting service` | add the `SECRET_KEY` variable. |
| `Unknown database 'oes_db'` | on PythonAnywhere the name is prefixed — use `yourname$oes_db`. |
| `2003 Can't connect to MySQL server` | wrong host, or the provider needs TLS — set `MYSQL_SSL=1`. |
| `1045 Access denied` | wrong MySQL user/password. |
| `PROCEDURE ... does not exist` on `/admin/reports` | `init_db.py` was not run, or was run against a different database. |
| `1227 Access denied; you need SUPER privileges` while creating procedures | the provider blocks routine creation — that provider cannot host this project; use PythonAnywhere or Aiven. |
| 500 on every page after deploy | check the error log (PythonAnywhere *Web* tab, or Render logs); it is almost always the database connection. |
| Site is slow on the first click after idle | Render free tier only; PythonAnywhere does not sleep. |

## Local development is unchanged

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

with a local MySQL running and `.env` copied from `.env.example`.
