from common.db import db_cursor


def get_user_name(user_id):
    with db_cursor() as cur:
        cur.execute(
            'SELECT first_name, last_name FROM "USER" WHERE user_id = %s',
            (user_id,),
        )
        return cur.fetchone()


def get_profile(doctor_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT u.first_name, u.last_name, u.email, u.phone,
                      d.specialty, d.license_number
               FROM "USER" u JOIN doctor d ON u.user_id = d.doctor_id
               WHERE u.user_id = %s''',
            (doctor_id,),
        )
        return cur.fetchone()


def get_schedule(doctor_id, date=None):
    """Call get_doctor_schedule stored proc. date=None → CURRENT_DATE."""
    with db_cursor() as cur:
        if date:
            cur.execute('SELECT * FROM get_doctor_schedule(%s, %s)', (doctor_id, date))
        else:
            cur.execute('SELECT * FROM get_doctor_schedule(%s, CURRENT_DATE)', (doctor_id,))
        return cur.fetchall()


def list_appointments_in_range(doctor_id, start_date, end_date):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_date, a.appointment_time, a.status, a.reason,
                      u.first_name || ' ' || u.last_name AS patient_name,
                      a.patient_id, a.appointment_id
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" u ON p.patient_id = u.user_id
               WHERE a.doctor_id = %s
                 AND a.appointment_date BETWEEN %s AND %s
               ORDER BY a.appointment_date, a.appointment_time''',
            (doctor_id, start_date, end_date),
        )
        return cur.fetchall()


def get_appointment(doctor_id, appointment_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason, a.patient_id,
                      u.first_name, u.last_name,
                      p.date_of_birth, p.gender
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" u ON p.patient_id = u.user_id
               WHERE a.appointment_id = %s AND a.doctor_id = %s''',
            (appointment_id, doctor_id),
        )
        return cur.fetchone()


def get_visit_by_appointment(appointment_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT visit_date, diagnosis, vitals, visit_notes
               FROM visit WHERE appointment_id = %s''',
            (appointment_id,),
        )
        return cur.fetchone()


def get_prescription_for_visit(doctor_id, visit_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT prescription_id FROM prescription
               WHERE visit_id = %s AND doctor_id = %s LIMIT 1''',
            (visit_id, doctor_id),
        )
        return cur.fetchone()


def get_last_visit(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT visit_date, diagnosis FROM visit
               WHERE patient_id = %s ORDER BY visit_date DESC LIMIT 1''',
            (patient_id,),
        )
        return cur.fetchone()


def list_availability(doctor_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT day_of_week, start_time, end_time FROM availability
               WHERE doctor_id = %s
               ORDER BY CASE day_of_week
                   WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                   WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                   WHEN 'Sunday' THEN 7
               END, start_time''',
            (doctor_id,),
        )
        return cur.fetchall()


def doctor_treats_patient(doctor_id, patient_id):
    with db_cursor() as cur:
        cur.execute(
            'SELECT 1 FROM appointment WHERE patient_id = %s AND doctor_id = %s LIMIT 1',
            (patient_id, doctor_id),
        )
        return cur.fetchone() is not None


def get_patient_details(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT u.first_name, u.last_name, p.date_of_birth, p.gender, p.address,
                      p.emergency_contact_name, p.emergency_contact_phone
               FROM patient p JOIN "USER" u ON p.patient_id = u.user_id
               WHERE p.patient_id = %s''',
            (patient_id,),
        )
        return cur.fetchone()


def list_patient_visits(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes
               FROM visit v WHERE v.patient_id = %s ORDER BY v.visit_date DESC''',
            (patient_id,),
        )
        return cur.fetchall()


def list_pending_appointments(patient_id, doctor_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT appointment_id, appointment_date, appointment_time FROM appointment
               WHERE patient_id = %s AND doctor_id = %s AND status = 'Scheduled'
               ORDER BY appointment_date''',
            (patient_id, doctor_id),
        )
        return cur.fetchall()


def list_prescriptions(doctor_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT p.prescription_id, p.issue_date,
                      u.first_name || ' ' || u.last_name AS patient_name,
                      m.medication_name, c.frequency, c.duration
               FROM prescription p
               JOIN visit v ON p.visit_id = v.appointment_id
               JOIN patient pt ON v.patient_id = pt.patient_id
               JOIN "USER" u ON pt.patient_id = u.user_id
               JOIN contains c ON p.prescription_id = c.prescription_id
               JOIN medication m ON c.medication_id = m.medication_id
               WHERE p.doctor_id = %s ORDER BY p.issue_date DESC''',
            (doctor_id,),
        )
        return cur.fetchall()


def list_medications():
    with db_cursor() as cur:
        cur.execute('SELECT medication_id, medication_name FROM medication')
        return cur.fetchall()


def list_visits_for_prescriptions(doctor_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT v.appointment_id, v.visit_date,
                      u.first_name || ' ' || u.last_name AS patient_name
               FROM visit v
               JOIN patient p ON v.patient_id = p.patient_id
               JOIN "USER" u ON p.patient_id = u.user_id
               JOIN appointment a ON v.appointment_id = a.appointment_id
               WHERE a.doctor_id = %s''',
            (doctor_id,),
        )
        return cur.fetchall()
