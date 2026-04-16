from common.db import db_cursor


def dashboard_counts():
    with db_cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM patient')
        patient_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM doctor')
        doctor_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM appointment WHERE status = 'Scheduled'")
        pending_count = cur.fetchone()[0]
    return patient_count, doctor_count, pending_count


def list_recent_appointments(limit=10):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status,
                      pu.first_name || ' ' || pu.last_name AS patient_name,
                      du.first_name || ' ' || du.last_name AS doctor_name
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" pu ON p.patient_id = pu.user_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" du ON d.doctor_id = du.user_id
               ORDER BY a.appointment_date DESC LIMIT %s''',
            (limit,),
        )
        return cur.fetchall()


def list_all_appointments():
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      pu.first_name || ' ' || pu.last_name AS patient_name,
                      du.first_name || ' ' || du.last_name AS doctor_name
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" pu ON p.patient_id = pu.user_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" du ON d.doctor_id = du.user_id
               ORDER BY a.appointment_date DESC'''
        )
        return cur.fetchall()


def list_users():
    with db_cursor() as cur:
        cur.execute(
            'SELECT user_id, first_name, last_name, email, phone, role '
            'FROM "USER" ORDER BY role, last_name'
        )
        return cur.fetchall()


def get_user_role(user_id):
    with db_cursor() as cur:
        cur.execute('SELECT role FROM "USER" WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        return row[0] if row else None


def list_medications():
    with db_cursor() as cur:
        cur.execute(
            'SELECT medication_id, medication_name, description, dosage_form FROM medication'
        )
        return cur.fetchall()
