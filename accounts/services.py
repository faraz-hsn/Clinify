from django.contrib.auth.hashers import make_password

from common.db import db_cursor

from . import selectors


def register_patient(data):
    """Create a USER, patient, and empty medical_record row in one transaction.

    Only core identity fields are required up front; profile details
    (DOB, gender, address, emergency contact) are collected post-signup
    on the patient profile page.

    Raises ValueError if the email is already taken.
    """
    if selectors.email_exists(data['email']):
        raise ValueError('An account with this email already exists.')

    password_hash = make_password(data['password'])
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''INSERT INTO "USER" (first_name, last_name, email, password_hash, role)
               VALUES (%s, %s, %s, %s, 'patient') RETURNING user_id''',
            (data['first_name'], data['last_name'], data['email'], password_hash),
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            'INSERT INTO patient (patient_id) VALUES (%s)',
            (user_id,),
        )
        cur.execute(
            'INSERT INTO medical_record (patient_id, record_number) VALUES (%s, 1)',
            (user_id,),
        )
    return user_id


def register_doctor(data):
    """Create a USER and doctor row. Email domain gating is enforced by the form.

    License number is required (NOT NULL UNIQUE in the schema); specialty
    is filled in later on the doctor profile page.

    Raises ValueError if the email or license number is already taken.
    """
    if selectors.email_exists(data['email']):
        raise ValueError('An account with this email already exists.')

    password_hash = make_password(data['password'])
    with db_cursor(commit=True) as cur:
        cur.execute(
            'SELECT 1 FROM doctor WHERE license_number = %s',
            (data['license_number'],),
        )
        if cur.fetchone():
            raise ValueError('A doctor with this license number already exists.')

        cur.execute(
            '''INSERT INTO "USER" (first_name, last_name, email, password_hash, role)
               VALUES (%s, %s, %s, %s, 'doctor') RETURNING user_id''',
            (data['first_name'], data['last_name'], data['email'], password_hash),
        )
        user_id = cur.fetchone()[0]
        cur.execute(
            'INSERT INTO doctor (doctor_id, license_number) VALUES (%s, %s)',
            (user_id, data['license_number']),
        )
    return user_id
