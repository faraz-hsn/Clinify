import datetime

from common.db import db_cursor


def update_profile(patient_id, phone, address, emergency_contact_name, emergency_contact_phone):
    with db_cursor(commit=True) as cur:
        cur.execute(
            'UPDATE "USER" SET phone = %s WHERE user_id = %s',
            (phone, patient_id),
        )
        cur.execute(
            '''UPDATE patient SET address = %s, emergency_contact_name = %s,
               emergency_contact_phone = %s WHERE patient_id = %s''',
            (address, emergency_contact_name, emergency_contact_phone, patient_id),
        )


def cancel_appointment(patient_id, appointment_id):
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''SELECT 1 FROM appointment
               WHERE appointment_id = %s AND patient_id = %s AND status = 'Scheduled' ''',
            (appointment_id, patient_id),
        )
        if not cur.fetchone():
            raise ValueError('Cannot cancel this appointment.')
        cur.execute('SELECT cancel_appointment(%s)', (appointment_id,))


def reschedule_appointment(patient_id, appointment_id, new_date, new_time):
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''UPDATE appointment SET appointment_date = %s, appointment_time = %s
               WHERE appointment_id = %s AND patient_id = %s AND status = 'Scheduled' ''',
            (new_date, new_time, appointment_id, patient_id),
        )


def book_appointment(patient_id, doctor_id, date, time, reason):
    day_name = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%A')
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''SELECT 1 FROM availability
               WHERE doctor_id = %s AND day_of_week = %s
                 AND start_time <= %s AND end_time >= %s''',
            (doctor_id, day_name, time, time),
        )
        if not cur.fetchone():
            raise ValueError('Doctor is not available at that time.')

        cur.execute(
            '''SELECT 1 FROM appointment
               WHERE doctor_id = %s AND appointment_date = %s
                 AND appointment_time = %s AND status = 'Scheduled' ''',
            (doctor_id, date, time),
        )
        if cur.fetchone():
            raise ValueError('This time slot is already booked. Please choose another time.')

        cur.execute(
            'SELECT book_appointment(%s, %s, %s, %s, %s)',
            (patient_id, doctor_id, date, time, reason),
        )
