# Clinify - Clinic Management System

CPSC 471 - Group 27

---

## Setup

1. Create your local environment file

```bash
cp .env.example .env
```

Update `.env` with your local values:

| Variable      | Description                                      |
| ------------- | ------------------------------------------------ |
| `SECRET_KEY`  | Django secret key generated in step 4            |
| `DEBUG`       | Use `True` for local development                 |
| `DB_NAME`     | PostgreSQL database name                         |
| `DB_USER`     | PostgreSQL user                                  |
| `DB_PASSWORD` | PostgreSQL password for `DB_USER`                |
| `DB_HOST`     | PostgreSQL host                                  |

2. Create virtual environment and activate it

```bash
python -m venv venv
source venv/bin/activate
```

On Windows, use `venv\Scripts\activate`.

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Generate a Django secret key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output into `SECRET_KEY` in `.env`.

5. Set up the database (PostgreSQL must be installed)

```bash
psql -U postgres -f database/schema.sql
psql -U postgres -f database/seed.sql
python manage.py migrate
```

6. Run

```bash
python manage.py runserver
```

---

## Project Structure

| Folder          | Purpose                                             |
| --------------- | --------------------------------------------------- |
| `config/`       | Django project settings, root URLs, WSGI/ASGI       |
| `common/`       | Shared utilities (DB cursor, decorators, session)   |
| `accounts/`     | Login, logout, registration (Django auth)           |
| `patient/`      | Patient portal views and templates                  |
| `doctor/`       | Doctor portal views and templates                   |
| `clinic_admin/` | Admin panel views and templates                     |
| `templates/`    | Shared templates                                    |
| `static/`       | CSS and JavaScript assets                           |
| `database/`     | PostgreSQL schema and seed data                     |

---

## Test Accounts

All seed accounts use the password `password`. Staff accounts (doctors and admins) must use the `@clinify.com` domain.

| Email                           | Role    | Notes                 |
| ------------------------------- | ------- | --------------------- |
| `alex.johnson@email.com`        | Patient |                       |
| `sarah.lee@email.com`           | Patient |                       |
| `michael.brown@email.com`       | Patient |                       |
| `emma.davis@email.com`          | Patient |                       |
| `liam.martinez@email.com`       | Patient |                       |
| `olivia.chen@email.com`         | Patient |                       |
| `rose.smith@clinify.com`        | Doctor  | Family Medicine       |
| `james.wilson@clinify.com`      | Doctor  | Cardiology            |
| `priya.patel@clinify.com`       | Doctor  | Pediatrics            |
| `marcus.thompson@clinify.com`   | Doctor  | Dermatology, inactive |
| `sara.admin@clinify.com`        | Admin   |                       |
| `david.reyes@clinify.com`       | Admin   |                       |
