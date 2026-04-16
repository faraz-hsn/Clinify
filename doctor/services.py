from common.db import db_cursor


def add_availability(doctor_id, day_of_week, start_time, end_time):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'INSERT INTO availability (doctor_id, day_of_week, start_time, end_time) '
            'VALUES (%s, %s, %s, %s)',
            (doctor_id, day_of_week, start_time, end_time),
        )


def delete_availability(doctor_id, day_of_week, start_time):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'DELETE FROM availability '
            'WHERE doctor_id = %s AND day_of_week = %s AND start_time = %s',
            (doctor_id, day_of_week, start_time),
        )


def record_visit(doctor_id, patient_id, appointment_id, diagnosis, vitals, notes):
    if not appointment_id:
        raise ValueError('Please select an appointment.')
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''SELECT 1 FROM appointment
               WHERE appointment_id = %s AND patient_id = %s
                 AND doctor_id = %s AND status = 'Scheduled' ''',
            (appointment_id, patient_id, doctor_id),
        )
        if not cur.fetchone():
            raise ValueError('You can only record visits for your own scheduled appointments.')
        cur.execute(
            'SELECT create_visit(%s, %s, %s, %s, %s, %s)',
            (int(appointment_id), int(patient_id), 1, diagnosis, vitals, notes),
        )


def create_prescription(doctor_id, visit_id, medication_ids, frequencies, durations):
    with db_cursor(commit=True) as cur:
        cur.execute('SELECT create_prescription(%s, %s)', (visit_id, doctor_id))
        prescription_id = cur.fetchone()[0]
        for med_id, freq, dur in zip(medication_ids, frequencies, durations):
            cur.execute(
                'INSERT INTO contains VALUES (%s, %s, %s, %s)',
                (prescription_id, med_id, freq, dur),
            )
    return prescription_id
