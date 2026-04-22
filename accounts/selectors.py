from common.db import db_cursor


def get_user_identity_by_email(email):
    """Return (user_id, role) for the given email, or None if not found."""
    with db_cursor() as cur:
        cur.execute(
            'SELECT user_id, role FROM "USER" WHERE LOWER(email) = LOWER(%s)',
            (email,),
        )
        return cur.fetchone()


def get_user_login_state_by_email(email):
    """Return (user_id, role, is_active) for the given email, or None if not found."""
    with db_cursor() as cur:
        cur.execute(
            'SELECT user_id, role, is_active FROM "USER" WHERE LOWER(email) = LOWER(%s)',
            (email,),
        )
        return cur.fetchone()


def is_user_active(user_id):
    with db_cursor() as cur:
        cur.execute('SELECT is_active FROM "USER" WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        return bool(row[0]) if row else False


def email_exists(email):
    with db_cursor() as cur:
        cur.execute(
            'SELECT 1 FROM "USER" WHERE LOWER(email) = LOWER(%s)',
            (email,),
        )
        return cur.fetchone() is not None


def get_user_credentials_by_email(email):
    """Return the columns ClinicBackend needs to authenticate a login attempt."""
    with db_cursor() as cur:
        cur.execute(
            'SELECT user_id, password_hash, role, first_name, last_name '
            'FROM "USER" WHERE LOWER(email) = LOWER(%s)',
            (email,),
        )
        return cur.fetchone()
