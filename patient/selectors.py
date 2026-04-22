from common.db import db_cursor


def get_user_name(user_id):
    with db_cursor() as cur:
        cur.execute(
            'SELECT first_name, last_name FROM "USER" WHERE user_id = %s',
            (user_id,),
        )
        return cur.fetchone()


def list_recent_appointments(patient_id, limit=5):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || ' ' || u.last_name AS doctor_name,
                      a.doctor_id
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s
               ORDER BY a.appointment_date DESC, a.appointment_time DESC
               LIMIT %s''',
            (patient_id, limit),
        )
        return cur.fetchall()


def get_next_scheduled_appointment(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.reason,
                      u.first_name || ' ' || u.last_name AS doctor_name,
                      d.specialty
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s
                 AND a.status = 'Scheduled'
                 AND (a.appointment_date > CURRENT_DATE
                      OR (a.appointment_date = CURRENT_DATE AND a.appointment_time >= CURRENT_TIME))
               ORDER BY a.appointment_date ASC, a.appointment_time ASC
               LIMIT 1''',
            (patient_id,),
        )
        return cur.fetchone()


def list_all_appointments(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || ' ' || u.last_name AS doctor_name,
                      a.doctor_id
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s
               ORDER BY a.appointment_date DESC, a.appointment_time DESC''',
            (patient_id,),
        )
        return cur.fetchall()


def list_doctors():
    with db_cursor() as cur:
        cur.execute(
            '''SELECT d.doctor_id, u.first_name || ' ' || u.last_name, d.specialty
               FROM doctor d JOIN "USER" u ON d.doctor_id = u.user_id'''
        )
        return cur.fetchall()


def availability_map():
    """Return {doctor_id: {slots: [...]}}."""
    with db_cursor() as cur:
        cur.execute(
            'SELECT doctor_id, day_of_week, start_time, end_time '
            'FROM availability ORDER BY doctor_id'
        )
        slot_rows = cur.fetchall()

    out = {}
    for doctor_id, day, start, end in slot_rows:
        entry = out.setdefault(str(doctor_id), {'slots': []})
        entry['slots'].append({
            'day': day, 'start': str(start)[:5], 'end': str(end)[:5],
        })
    return out


def get_profile(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT u.first_name, u.last_name, u.email, u.phone,
                      p.date_of_birth, p.gender, p.address,
                      p.emergency_contact_name, p.emergency_contact_phone
               FROM "USER" u JOIN patient p ON u.user_id = p.patient_id
               WHERE u.user_id = %s''',
            (patient_id,),
        )
        return cur.fetchone()


def list_visits(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes,
                      u.first_name || ' ' || u.last_name AS doctor_name
               FROM visit v
               JOIN appointment a ON v.appointment_id = a.appointment_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE v.patient_id = %s ORDER BY v.visit_date DESC''',
            (patient_id,),
        )
        return cur.fetchall()


def list_prescriptions(patient_id):
    with db_cursor() as cur:
        cur.execute(
            '''SELECT p.prescription_id, p.issue_date,
                      u.first_name || ' ' || u.last_name AS doctor_name,
                      m.medication_name, c.frequency, c.duration
               FROM prescription p
               JOIN visit v ON p.visit_id = v.appointment_id
               JOIN "USER" u ON p.doctor_id = u.user_id
               JOIN contains c ON p.prescription_id = c.prescription_id
               JOIN medication m ON c.medication_id = m.medication_id
               WHERE v.patient_id = %s ORDER BY p.issue_date DESC''',
            (patient_id,),
        )
        return cur.fetchall()
