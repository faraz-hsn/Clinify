# Clinify - Clinic Management System

CPSC 471 - Group 27

---

## Setup

1. Get the `.env` file in the root folder
2. Create virtual environment and activate it

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up the database (PostgreSQL must be installed)

```bash
psql -U postgres -f database/schema.sql
psql -U postgres -f database/seed.sql
python manage.py migrate
```

5. Run

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
| `database/`     | PostgreSQL schema and seed data                     |

Each feature app is split into `urls.py` → `views.py` (thin, HTTP only) → `services.py` (writes) / `selectors.py` (reads), which call the raw-SQL helpers in `common/db.py`.

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
| `marcus.thompson@clinify.com`   | Doctor  | Dermatology           |
| `sara.admin@clinify.com`        | Admin   |                       |
| `david.reyes@clinify.com`       | Admin   |                       |
