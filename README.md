# NovaCRM — a HubSpot-style CRM built with Django

A full-featured CRM web app inspired by HubSpot's core CRM: Contacts, Companies,
Deals with a drag-and-drop pipeline board, Tasks, activity timelines, a dashboard,
global search, and Django admin — all built with Django's ORM and class-based views.

## Reports & exports

A **Reports** page (in the sidebar) pulls together deal/revenue totals,
pipeline-by-stage, pipeline-by-rep (managers only), contacts, companies, and
tasks into one place — respecting the same rep-vs-manager visibility as the
rest of the CRM (reps only ever see their own numbers).

From that page you can:
- **Print** — opens the browser print dialog with a clean, sidebar-free layout
- **Export CSV** — plain text, opens in Excel/Sheets/Numbers
- **Export Excel (.xlsx)** — a real multi-sheet workbook (Deals, Contacts,
  Companies, Tasks each on their own tab), styled headers, auto-sized columns
- **Export PDF** — a formatted, multi-page report suitable for sending to a
  client or archiving

## Features

- **Dashboard** — contact/company/deal counts, open pipeline value, won revenue,
  pipeline-by-stage breakdown, tasks due today, overdue tasks, recent activity feed.
- **Contacts** — full CRUD, lifecycle stages (Lead, MQL, SQL, Opportunity, Customer, etc.),
  linked company, activity timeline, related deals & tasks.
- **Companies** — full CRUD, industry/revenue/employee data, linked contacts & deals,
  open pipeline value per company.
- **Deals** — Kanban pipeline board with **drag-and-drop** stage changes (AJAX, no
  page reload needed to move a card — it saves instantly), plus a full detail page,
  CRUD forms, won/lost status.
- **Tasks** — due dates, priority, status, "mark complete" action, overdue flagging,
  linked to contacts/deals/companies.
- **Activity timeline** — log notes, calls, emails, and meetings against any
  contact, company, or deal.
- **Global search** — one search box in the top bar searches contacts, companies,
  and deals at once.
- **Auth** — login required for the whole CRM; Django admin available for power-user
  data management.
- **Demo data seeding** — one management command populates realistic sample data.

## Tech stack

- Python 3 + Django 5/6 (class-based views, ORM, forms, admin)
- SQLite (default; swap `DATABASES` in `config/settings.py` for Postgres/MySQL in production)
- Vanilla HTML/CSS/JS templates (no frontend framework needed) — HubSpot-inspired
  navy sidebar + orange accent theme, plain JS for the kanban drag-and-drop

## User accounts & roles

There's no self-service signup — an admin creates every account, either in
Django admin (`/admin/`) or via `python manage.py createsuperuser`. Two roles:

- **Rep** (a regular user) — only ever sees, edits, and deletes contacts,
  companies, and deals they own, and tasks assigned to them. Trying to open
  someone else's record by guessing its URL returns a 404. When a rep
  creates a new record, it's automatically owned by them — they don't get
  an "Owner" field to reassign it.
- **Manager** — sees and can edit everything, and can assign the
  owner/assigned-to field on any record. To make someone a manager, open
  their user in Django admin (`/admin/auth/user/`) and check **"Staff
  status"**. Superusers are always managers too.

To add a new rep: Django admin → **Users → Add user**, set a username and
password, leave "Staff status" unchecked. To add a manager: same, but check
"Staff status".

## AI features (powered by Claude)

Four AI-assisted features, all using Anthropic's Claude API:

- **Summarize** — on any Contact or Deal page, click "Summarize" for a
  3-5 sentence brief of that record's activity and status.
- **Draft Follow-up** — generates a short follow-up email based on the
  record's context (deal amount, stage, recent activity).
- **Suggest Next Action** — on a Deal page, get one concrete next step
  the AI thinks you should take, with a reason why.
- **AI Assistant** (sidebar link) — a chat interface where you can ask
  free-form questions about your own CRM data ("which deals are closing
  this month?", "what's overdue?"). It only sees data the logged-in user
  has access to — same rep-vs-manager rule as the rest of the CRM.

**Setup:** add your key to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```
Get one at https://console.anthropic.com/settings/keys. Without a key, every
AI button shows a friendly "not configured" message instead of erroring —
the rest of the CRM works completely normally either way.

**Cost note:** each AI action is a small, focused API call (a short summary
of one record, or a chat turn) — not sending your whole database. Usage is
billed by Anthropic per your account's standard API pricing.

## Client portal (giving a company's own employee a login)

A company's employee, manager, or owner (e.g. someone at Acme Robotics) can
get their own login that shows **only their company's deals and activity**
— read-only, and completely walled off from the rest of the CRM (they
can't see other companies, contacts, tasks, reports, or admin).

**To grant portal access to someone:**
1. In Django admin, create their user account: **Users → Add user** (set
   username + password, leave "Staff status" **unchecked**)
2. Go to that **Company** in admin (**Companies → [pick one]**)
3. Scroll to the **"Portal users"** section at the bottom of the page →
   **Add another Portal user** → select the user you just created → Save

That's it — give them their username/password, and they log in at the
normal `/login/` page. They're automatically routed to `/portal/` instead
of the internal CRM, every time.

**Demo login included:** `demo_client` / `democlient123` — shows Acme
Robotics' portal view. Try it at `/portal/` after logging in, or just log
in normally and you'll be routed there automatically.

**What they can't do:** edit anything, see other companies, see contacts,
tasks, reports, or reach Django admin — every internal URL redirects a
portal login straight back to their own `/portal/` page, even if they type
the URL directly.

## Deploying to Render (free tier)

The project is already configured for this — `render.yaml`, `build.sh`, and
`Procfile` are included, and `config/settings.py` automatically switches
from SQLite/DEBUG-on (local) to Postgres/DEBUG-off (production) based on
environment variables, so no code changes are needed to deploy.

**1. Push the project to GitHub**

Render deploys from a Git repo, not a zip upload.

```bash
cd hubspot_crm
git init
git add .
git commit -m "Initial commit"
```
Create a new empty repo on GitHub, then:
```bash
git remote add origin https://github.com/<you>/<repo-name>.git
git branch -M main
git push -u origin main
```

**2. Create the Render service**

1. Go to https://render.com and sign up / log in (free)
2. Click **New +** → **Blueprint**
3. Connect your GitHub account and select the repo you just pushed
4. Render reads `render.yaml` automatically and provisions:
   - A **web service** (runs `build.sh` then `gunicorn config.wsgi:application`)
   - A free **Postgres database**, wired up via the `DATABASE_URL` env var
   - A random, secure `SECRET_KEY`
5. Click **Apply** — first deploy takes a few minutes

**3. Create your first user**

Once deployed, open the **Shell** tab for your web service in the Render
dashboard and run:
```bash
python manage.py createsuperuser
```
(Or run `python manage.py seed_data` instead, to get demo data + the
`admin`/`admin123` login — recommended only for a demo, not real client data.)

**4. Visit your live site**

Render gives you a URL like `https://novacrm.onrender.com`. Log in at
`https://novacrm.onrender.com/login/`.

**Notes on the free tier:**
- The free web service spins down after 15 minutes of inactivity and takes
  ~30–60 seconds to wake back up on the next request — fine for a demo/small
  team tool, not ideal if you need instant access at all hours (paid tier
  removes this).
- The free Postgres database expires after 90 days unless upgraded — for
  anything beyond testing, plan to move to a paid database plan before then.
- To use a custom domain instead of `*.onrender.com`, add it in the Render
  dashboard under your service's **Settings → Custom Domains**.

**If you'd rather deploy without a `render.yaml` blueprint** (e.g. on
Railway, which has a similar free-tier flow): create a new project from your
GitHub repo, add a Postgres database, and set these environment variables on
the web service manually — Railway/Render both auto-detect `Procfile`:
```
SECRET_KEY=<any long random string>
DEBUG=False
DATABASE_URL=<automatically provided when you attach a Postgres addon>
ALLOWED_HOSTS=<your-app>.up.railway.app
```
Then set the build command to `./build.sh` and start command to
`gunicorn config.wsgi:application`.

## Getting started

### Option A — with Docker (easiest way to get Postgres running)

If you have Docker Desktop installed, this spins up a local Postgres
database for you with zero manual setup:

```bash
# 1. Start Postgres in the background
docker compose up -d

# 2. Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate     # Windows Git Bash. Mac/Linux: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the env template (already pre-filled to match docker-compose.yml)
cp .env.example .env

# 5. Run migrations + seed demo data
python manage.py migrate
python manage.py seed_data

# 6. Run the dev server
python manage.py runserver
```

### Option B — with Postgres installed directly on your machine

1. Install Postgres (e.g. from postgresql.org) and note the password you set.
2. Create a database and user:
   ```sql
   CREATE USER novacrm_user WITH PASSWORD 'novacrm_pass';
   CREATE DATABASE novacrm_db OWNER novacrm_user;
   ```
3. Copy `.env.example` to `.env` and set `DATABASE_URL` to match what you
   created above (the example file already has a matching default).
4. Continue from step 2 in Option A (venv, install, migrate, seed, runserver).

### Option C — no Postgres at all, just use SQLite

Don't create a `.env` file (or delete `DATABASE_URL` from it). The project
falls back to a local `db.sqlite3` file automatically — this is how the
project ran before Postgres was added, and still works identically for
quick local testing.

### How the database is chosen

`config/settings.py` reads `DATABASE_URL` from a `.env` file in the project
root (loaded automatically via `python-dotenv`) or from a real environment
variable if one is set (e.g. on Render). If neither is present, it falls
back to SQLite. Nothing else in the project needs to change between the
three options above.

Visit **http://127.0.0.1:8000/** and log in with `admin` / `admin123`
(or create your own user with `python manage.py createsuperuser`).

Django admin is available at **http://127.0.0.1:8000/admin/**.

## Project structure

```
hubspot_crm/
├── manage.py
├── requirements.txt
├── .env.example             # template for local config (copy to .env)
├── docker-compose.yml        # spins up a local Postgres for development
├── build.sh / Procfile / render.yaml   # Render deployment config
├── config/                # project settings, root urls, wsgi/asgi
├── crm/                    # the CRM app
│   ├── models.py           # Company, Contact, PipelineStage, Deal, Task, Activity
│   ├── views.py            # dashboard, CRUD views, kanban board + AJAX move, search
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   ├── management/commands/seed_data.py
│   └── templates/crm/      # all HTML templates
└── static/
    ├── css/style.css       # HubSpot-inspired theme
    └── js/kanban.js        # drag-and-drop pipeline board
```

## Extending it further

Ideas if you want to keep building this out toward feature-parity with HubSpot:
- Email integration (send/log emails from the CRM, e.g. via Django + a transactional
  email API)
- Custom fields / custom properties per object (would need a generic `CustomField`
  + `CustomFieldValue` model pair or a JSONField on each model)
- Reporting/analytics with charts (e.g. Chart.js against aggregate querysets)
- Role-based permissions & multiple pipelines
- REST API (Django REST Framework) for a mobile app or integrations
- Marketing features: forms, landing pages, email sequences
