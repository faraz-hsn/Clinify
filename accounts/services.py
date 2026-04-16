from django.contrib.auth.hashers import make_password

from common.db import db_cursor

from . import selectors


def register_patient(data):
    """Create a USER, patient, and empty medical_record row in one transaction.

    Raises ValueError if the email is already taken.
    """
    if selectors.email_exists(data['email']):
        raise ValueError('An account with this email already exists.')

    password_hash = make_password(data['password'])
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''INSERT INTO "USER" (first_name, last_name, email, phone, password_hash, role)
               VALUES (%s, %s, %s, %s, %s, 'patient') RETURNING user_id''',
            (data['first_name'], data['last_name'], data['email'],
             data['phone'], password_hash),
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            '''INSERT INTO patient (patient_id, date_of_birth, gender, address,
                   emergency_contact_name, emergency_contact_phone)
               VALUES (%s, %s, %s, %s, %s, %s)''',
            (user_id, data['date_of_birth'], data['gender'], data['address'],
             data['emergency_contact_name'], data['emergency_contact_phone']),
        )
        cur.execute(
            'INSERT INTO medical_record (patient_id, record_number) VALUES (%s, 1)',
            (user_id,),
        )
    return user_id
