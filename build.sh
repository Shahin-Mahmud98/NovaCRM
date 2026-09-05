#!/usr/bin/env bash
# Render runs this during every deploy.
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Creates/updates a superuser from DJANGO_SUPERUSER_* env vars if set — see
# crm/management/commands/ensure_admin.py. This is how you get your first
# login on hosts (like Render's free tier) that don't offer shell access.
python manage.py ensure_admin

# Optional: set SEED_DEMO_DATA=true as an env var to also populate demo
# companies/contacts/deals/tasks on every deploy (safe to leave on — it
# won't duplicate existing records).
if [ "$SEED_DEMO_DATA" = "true" ]; then
  python manage.py seed_data
fi
