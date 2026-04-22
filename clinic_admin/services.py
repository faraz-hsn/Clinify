from django.contrib.auth.hashers import make_password

from accounts import selectors as account_selectors
from common.db import db_cursor
from common.names import normalize_person_name
from common.phone import normalize_phone

from . import selectors


def create_admin(data):
    """Create an additional admin account. Email domain is enforced by the form."""
    if account_selectors.email_exists(data['email']):
        raise ValueError('An account with this email already exists.')

    first_name = normalize_person_name(data['first_name'])
    last_name = normalize_person_name(data['last_name'])
    password_hash = make_password(data['password'])
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''INSERT INTO "USER" (first_name, last_name, email, password_hash, role)
               VALUES (%s, %s, %s, %s, 'admin') RETURNING user_id''',
            (first_name, last_name, data['email'], password_hash),
        )
        user_id = cur.fetchone()[0]
        cur.execute('INSERT INTO admin (admin_id) VALUES (%s)', (user_id,))
    return user_id


def cancel_appointment(appointment_id):
    with db_cursor(commit=True) as cur:
        cur.execute('SELECT cancel_appointment(%s)', (appointment_id,))


def update_appointment_status(appointment_id, status):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'UPDATE appointment SET status = %s WHERE appointment_id = %s',
            (status, appointment_id),
        )


def update_user(user_id, first_name, last_name, phone, new_role):
    """Update a user's name and phone. Role changes are not permitted here."""
    current_role = selectors.get_user_role(user_id)
    if current_role not in ('doctor', 'admin'):
        raise ValueError('Only staff accounts can be managed here.')
    if current_role and new_role and current_role != new_role:
        raise ValueError('Role changes are not supported.')
    first_name = normalize_person_name(first_name)
    last_name = normalize_person_name(last_name)
    phone = normalize_phone(phone)
    with db_cursor(commit=True) as cur:
        cur.execute(
            'UPDATE "USER" SET first_name=%s, last_name=%s, phone=%s WHERE user_id=%s',
            (first_name, last_name, phone, user_id),
        )


def set_doctor_active(doctor_id, is_active):
    doctor_id = (doctor_id or '').strip()
    if not doctor_id:
        raise ValueError('Missing doctor account.')
    try:
        doctor_id_int = int(doctor_id)
    except ValueError:
        raise ValueError('Invalid doctor account.') from None

    with db_cursor(commit=True) as cur:
        cur.execute(
            'SELECT role FROM "USER" WHERE user_id = %s',
            (doctor_id_int,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError('Doctor account not found.')
        if row[0] != 'doctor':
            raise ValueError('Only doctor accounts can be activated/deactivated.')

        if not is_active:
            cur.execute(
                '''SELECT 1 FROM appointment
                   WHERE doctor_id = %s
                     AND status = 'Scheduled'
                     AND appointment_date >= CURRENT_DATE
                   LIMIT 1''',
                (doctor_id_int,),
            )
            if cur.fetchone():
                raise ValueError(
                    'This doctor has scheduled appointments and cannot be deactivated.'
                )

        cur.execute(
            'UPDATE "USER" SET is_active = %s WHERE user_id = %s',
            (bool(is_active), doctor_id_int),
        )


def delete_user(user_id):
    with db_cursor(commit=True) as cur:
        cur.execute('DELETE FROM "USER" WHERE user_id = %s', (user_id,))


def add_medication(name, description, dosage_form):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'INSERT INTO medication (medication_name, description, dosage_form) '
            'VALUES (%s, %s, %s)',
            (name, description, dosage_form),
        )


def delete_medication(medication_id):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'DELETE FROM medication WHERE medication_id = %s',
            (medication_id,),
        )
