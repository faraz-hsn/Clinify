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

| Folder          | Purpose                                      |
| --------------- | -------------------------------------------- |
| `accounts/`     | Login, logout, registration (Django auth)    |
| `patient/`      | Patient portal views and templates           |
| `doctor/`       | Doctor portal views and templates            |
| `clinic_admin/` | Admin panel views and templates              |
| `core/`         | Shared utilities (DB connection, decorators) |
| `database/`     | PostgreSQL schema and seed data              |

---

## Test Accounts

All seed accounts use the password `password`.

| Email                     | Role    |
| ------------------------- | ------- |
| `alex.johnson@email.com`  | Patient |
| `sarah.lee@email.com`     | Patient |
| `michael.brown@email.com` | Patient |
| `rose.smith@email.com`    | Doctor  |
| `james.wilson@email.com`  | Doctor  |
| `sara.admin@email.com`    | Admin   |
