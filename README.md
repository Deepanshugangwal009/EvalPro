# EvalPro - Online Examination System

A web based online examination system built with Python, Flask and MySQL. An admin
manages subjects, exams and the question bank, while students register, attempt
scheduled timer based exams, and view their results and performance history.

---

## Description

The project replaces a paper based classroom test with an online one. The admin
creates subjects, creates an exam under a subject, schedules it for a date and a
time window, sets the duration, and adds multiple choice questions to it. A student
registers with an email, logs in, sees which exams are open, attempts an exam with a
live countdown timer, and submits. The answers are checked automatically, the marks
and percentage are calculated, and the result is stored and shown immediately. Every
past result stays available under Result History and Performance.

---

## Features

**Student**
- Registration and login with hashed passwords
- Dashboard with available exams, attempted exams and average percentage
- Exam list with live status: Available, Upcoming, Closed, Attempted
- Instructions page before starting an exam
- Timer based exam attempt with question palette and Previous/Next navigation
- Auto submit when the timer reaches zero
- Automatic result generation with marks, percentage and Pass/Fail
- Result history and performance tracking

**Admin**
- Separate admin login
- Dashboard with total students, subjects, exams and attempts
- Subject management (add, edit, delete, view)
- Exam management (create, schedule, set duration, activate/deactivate, delete)
- Question bank management per exam, with exam total marks kept in sync
- Reports: exam statistics, subject wise analysis, student performance

---

## Technologies Used

| Layer | Technology |
|-------|------------|
| Language | Python 3 |
| Backend | Flask |
| Templating | Jinja2 (Flask's built in server side HTML templating) |
| Frontend | HTML, CSS, Bootstrap 5, JavaScript |
| Database | MySQL |
| DB Access | Raw SQL through `mysql-connector-python` |

SQLAlchemy is intentionally not used so that all the SQL concepts (joins,
transactions, views, stored procedures, aggregate functions) are written directly in
SQL and are visible in the project.

---

## Database Design Overview

Eight tables are used.

| Table | Purpose |
|-------|---------|
| `students` | Registered students (name, email, hashed password, course, semester) |
| `admins` | Admin accounts |
| `subjects` | Subjects under which exams are created |
| `exams` | Exam details, schedule, duration and total marks |
| `questions` | Multiple choice questions belonging to an exam |
| `attempts` | One row per student per exam attempt |
| `attempt_answers` | The option chosen by the student for every question |
| `results` | Final marks, percentage and Pass/Fail for a student and exam |

**Relationships**

- `subjects (1) -> (M) exams`
- `exams (1) -> (M) questions`
- `students (1) -> (M) attempts` and `exams (1) -> (M) attempts`
- `attempts (1) -> (M) attempt_answers`
- `students (1) -> (M) results` and `exams (1) -> (M) results`

---

## SQL Concepts Used

| Concept | Where it is used |
|---------|------------------|
| Primary Keys | Every table |
| Foreign Keys | `exams`, `questions`, `attempts`, `attempt_answers`, `results` |
| Constraints | `UNIQUE` (email, subject code, username, student+exam), `NOT NULL`, `ENUM`, `DEFAULT`, `ON DELETE CASCADE` |
| Complex Relationships | student and exam linked through `attempts` and `results`; subject to exam to question chain |
| Joins | Exam list, student exam list, result page, reports |
| Aggregate Functions | `COUNT`, `SUM`, `AVG`, `MAX`, `MIN` in dashboards, marks calculation and reports |
| Transactions | Exam submission (attempt + answers + result committed together) |
| Views | `student_performance_view`, `exam_statistics_view` |
| Stored Procedures | `sp_generate_result`, `sp_subject_report` |

---

## Folder Structure

```
oes/
├── app.py
├── config.py
├── db.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── README.md
├── .gitignore
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   ├── views.sql
│   └── procedures.sql
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py
│   ├── admin.py
│   ├── student.py
│   ├── exam.py
│   └── result.py
│
├── helpers/
│   ├── __init__.py
│   ├── decorators.py
│   └── evaluation.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── 404.html
│   ├── 500.html
│   ├── auth/
│   │   ├── register.html
│   │   ├── student_login.html
│   │   └── admin_login.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── subjects.html
│   │   ├── subject_form.html
│   │   ├── questions.html
│   │   ├── question_form.html
│   │   ├── exams.html
│   │   ├── exam_form.html
│   │   ├── exam_questions.html
│   │   └── reports.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── exam_list.html
│   │   └── performance.html
│   ├── exam/
│   │   ├── instructions.html
│   │   └── attempt.html
│   └── result/
│       ├── result.html
│       └── history.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js
        └── timer.js
```

---

## Explanation of Every File

**Root**

| File | Purpose |
|------|---------|
| `app.py` | Creates the Flask app, loads the config, registers all blueprints, defines the landing route and the 404/500 error handlers |
| `config.py` | All configuration in one place, read from environment variables with local development defaults |
| `db.py` | The only place that opens MySQL connections. Provides `get_connection`, `fetch_one`, `fetch_all`, `execute` and `call_procedure` |
| `requirements.txt` | Python dependencies with the versions used |
| `Procfile` | Start command used by the hosting platform (`gunicorn app:app`) |
| `runtime.txt` | Python version the hosting platform should use |
| `.gitignore` | Ignores `__pycache__/`, `*.pyc`, `.env` and `venv/` |

**database/**

| File | Purpose |
|------|---------|
| `schema.sql` | Creates `oes_db` and all eight tables with keys and constraints |
| `seed.sql` | Inserts the default admin account and sample subjects |
| `views.sql` | Creates `student_performance_view` and `exam_statistics_view` |
| `procedures.sql` | Creates `sp_generate_result` and `sp_subject_report` |

**blueprints/**

| File | Purpose |
|------|---------|
| `auth.py` | Student registration, student login, admin login, logout and session handling |
| `admin.py` | Admin dashboard, subject CRUD, exam CRUD, question CRUD and reports |
| `student.py` | Student dashboard, exam list with availability status, and performance page |
| `exam.py` | Exam instructions, the attempt page, and the transactional submit handler |
| `result.py` | Single result page and result history |

**helpers/**

| File | Purpose |
|------|---------|
| `decorators.py` | `login_required` and `admin_required` session guards |
| `evaluation.py` | Marks, percentage and Pass/Fail calculation |

**templates/** contains the Jinja2 pages. `base.html` is the master layout with the
Bootstrap navbar and flash messages; every other page extends it.

**static/** holds `style.css`, `main.js` (auto dismissing alerts and confirm dialogs)
and `timer.js` (the exam countdown that auto submits at zero).

---

## Installation Steps

1. Install Python 3 and MySQL Server.
2. Open a terminal in the `oes` folder.
3. (Optional but recommended) create a virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

---

## Database Setup Steps

Run the four SQL files in this order from the `oes` folder:

```
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
mysql -u root -p < database/views.sql
mysql -u root -p < database/procedures.sql
```

`schema.sql` creates the database and tables, `seed.sql` adds the default admin and
sample subjects, `views.sql` creates the two views, and `procedures.sql` creates the
two stored procedures.

Default admin login:

- Username: `admin`
- Password: `admin123`

---

## Configuration Steps

`config.py` reads every setting from an environment variable and falls back to a local
development default, so a normal local setup needs no changes at all.

| Variable | Default | Meaning |
|----------|---------|---------|
| `MYSQL_HOST` | `localhost` | MySQL host |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | MySQL user |
| `MYSQL_PASSWORD` | *(empty)* | Password for that user |
| `MYSQL_DATABASE` | `oes_db` | Database name |
| `SECRET_KEY` | development value | Signs the session cookie |
| `FLASK_DEBUG` | `0` | Set to `1` for auto-reload while developing |
| `PORT` | `5000` | Port the server listens on |

If your local MySQL root account has a password, set it before starting the app:

```
set MYSQL_PASSWORD=your_mysql_password
```

`PASS_PERCENTAGE` decides the Pass/Fail mark and is set to 40 in `config.py`.
`PERMANENT_SESSION_LIFETIME` keeps a login valid for 60 minutes.

---

## How to Run

```
python app.py
```

Then open `http://127.0.0.1:5000/` in a browser.

For auto-reload while developing, turn debug on first:

```
set FLASK_DEBUG=1
```

---

## Project Workflow

1. The admin logs in at `/admin/login` and adds subjects.
2. The admin creates an exam under a subject, sets the date, time window and duration.
3. The admin adds questions to that exam. The exam total marks update automatically.
4. A student registers at `/register` and logs in at `/login`.
5. The student opens Exams and sees each exam as Available, Upcoming, Closed or Attempted.
6. For an available exam the student reads the instructions and starts the exam.
7. The timer counts down, the student answers and submits (or the timer submits automatically).
8. The attempt, all the answers and the result are saved together inside one transaction.
9. The result is shown immediately, and stays available under Results and Performance.
10. The admin sees the totals on the dashboard and the three reports on the Reports page.

---

## Dependencies

| Package | Version | Why it is needed |
|---------|---------|------------------|
| Flask | 3.1.3 | Web framework and Jinja2 templating |
| Werkzeug | 3.1.8 | Password hashing (`generate_password_hash`, `check_password_hash`) |
| mysql-connector-python | 26.7.0 | MySQL driver, installs on Windows without a C compiler |
| gunicorn | 26.0.0 | Production WSGI server used by the hosting platform |

Bootstrap 5 is loaded from a CDN, so an internet connection is needed for the styling
to appear.

---

## Deployment

### Netlify, GitHub Pages and Vercel static hosting will not work

This is a **server rendered Flask application with a MySQL database**. It needs a
running Python process and a live database connection on every request. Netlify and
GitHub Pages only serve static files, so there is no `index.html` for them to publish
and every URL returns "Page not found". The `templates/index.html` file in this repo is
a Jinja2 template, not a static page: it only becomes HTML when Flask renders it.

Deploying this project needs two things:

1. A host that runs Python web services
2. A hosted MySQL database

### Recommended: PythonAnywhere (free, includes MySQL)

PythonAnywhere is the simplest option because the free plan includes both the Python
web app and a MySQL database.

1. Create a free account and open a Bash console.
2. Clone the repository and install the requirements:

   ```
   git clone https://github.com/Deepanshugangwal009/EvalPro.git
   cd EvalPro
   pip install --user -r requirements.txt
   ```

3. Open the **Databases** tab, set a MySQL password, and create a database. The full
   name will look like `yourusername$oes_db`.
4. Load the schema into it. The first two lines of `schema.sql` create and select a
   local database, which a hosted account cannot do, so strip them:

   ```
   tail -n +3 database/schema.sql | mysql -u yourusername -h yourusername.mysql.pythonanywhere-services.com -p 'yourusername$oes_db'
   mysql -u yourusername -h yourusername.mysql.pythonanywhere-services.com -p 'yourusername$oes_db' < database/seed.sql
   ```

   `seed.sql`, `views.sql` and `procedures.sql` also begin with `USE oes_db;`, so strip
   that line the same way with `tail -n +2`.
5. Open the **Web** tab, add a new manual-configuration Flask app, and point the WSGI
   file at `app.py` so it imports `app`.
6. In the Web tab's environment variables, set `MYSQL_HOST`, `MYSQL_USER`,
   `MYSQL_PASSWORD`, `MYSQL_DATABASE` and a long random `SECRET_KEY`.
7. Reload the web app.

### Alternative: Render, Railway or Fly.io

These run the app from the included `Procfile` (`gunicorn app:app`) and `runtime.txt`.
They do not provide MySQL on the free plan, so pair them with a hosted MySQL such as
Railway MySQL, Aiven or Clever Cloud, then set the same environment variables in the
service dashboard.

### Before going live

- Leave `FLASK_DEBUG` unset or `0`. Debug mode exposes an interactive console that can
  run arbitrary code on the server, and the custom 404 and 500 pages only appear when
  debug is off.
- Set `SECRET_KEY` to a long random value through an environment variable, never in the
  committed source.
- Use a database user limited to this one database rather than `root`.
- The app is served by `gunicorn` in production; the Flask development server started by
  `python app.py` is for local use only.

---

## Assumptions Made

- A student can attempt an exam only once. This is enforced by a `UNIQUE(student_id,
  exam_id)` constraint and checked before the exam page opens.
- An exam can be attempted only inside its scheduled date and time window, and only
  if it is marked active.
- 40 percent is the pass mark.
- Every question is multiple choice with exactly four options and one correct answer.
- There is no negative marking, and an unanswered question is stored as `NULL`.
- The exam duration is counted from the moment the attempt page is opened.
- A subject cannot be deleted while exams reference it, an exam cannot be deleted once
  students have attempted it, and a question cannot be deleted once it is part of a
  submitted exam.
- Admin accounts are created through `seed.sql`, not through the application.
