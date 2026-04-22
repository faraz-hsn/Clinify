import psycopg2

from common.db import db_cursor
from common.phone import normalize_phone


def update_profile(doctor_id, phone, specialty):
    phone = normalize_phone(phone)
    with db_cursor(commit=True) as cur:
        cur.execute(
            'UPDATE "USER" SET phone = %s WHERE user_id = %s',
            (phone, doctor_id),
        )
        cur.execute(
            'UPDATE doctor SET specialty = %s WHERE doctor_id = %s',
            (specialty or None, doctor_id),
        )


def _fmt_time(t):
    # Accepts 'HH:MM' string; returns '9:00 AM' style. Falls back to input on error.
    try:
        h, m = [int(x) for x in t.split(':')[:2]]
        ampm = 'PM' if h >= 12 else 'AM'
        h12 = h % 12 or 12
        return f'{h12}:{m:02d} {ampm}'
    except Exception:
        return t


def _time_str(t):
    # Normalize a time value (string 'HH:MM[:SS]' or time object) to 'HH:MM'.
    s = t.strftime('%H:%M') if hasattr(t, 'strftime') else str(t)
    return s[:5]


def add_availability_slots(doctor_id, days, start_time, end_time):
    if not days:
        raise ValueError('Please select at least one day.')
    if not start_time or not end_time:
        raise ValueError('Please pick both a start and end time.')
    if start_time == end_time:
        raise ValueError(
            f'Start and end time are the same ({_fmt_time(start_time)}). Please choose a range.'
        )
    if start_time > end_time:
        raise ValueError(
            f'End time ({_fmt_time(end_time)}) must be after start time ({_fmt_time(start_time)}).'
        )
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''SELECT day_of_week, start_time, end_time FROM availability
               WHERE doctor_id = %s AND day_of_week = ANY(%s)''',
            (doctor_id, list(days)),
        )
        existing = cur.fetchall()
        for day, ex_start, ex_end in existing:
            ex_s, ex_e = _time_str(ex_start), _time_str(ex_end)
            if start_time == ex_s and end_time == ex_e:
                raise ValueError(
                    f'You already have this exact slot on {day} ({_fmt_time(ex_s)} – {_fmt_time(ex_e)}).'
                )
            if start_time == ex_s:
                raise ValueError(
                    f'You already have a slot starting at {_fmt_time(ex_s)} on {day}.'
                )
            if end_time == ex_e:
                raise ValueError(
                    f'You already have a slot ending at {_fmt_time(ex_e)} on {day}.'
                )
            if start_time < ex_e and end_time > ex_s:
                raise ValueError(
                    f'This overlaps your existing {_fmt_time(ex_s)} – {_fmt_time(ex_e)} slot on {day}.'
                )
        for day in days:
            cur.execute(
                'INSERT INTO availability (doctor_id, day_of_week, start_time, end_time) '
                'VALUES (%s, %s, %s, %s)',
                (doctor_id, day, start_time, end_time),
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


def _assert_doctor_owns_appointment(cur, doctor_id, appointment_id, require_scheduled=True):
    sql = 'SELECT 1 FROM appointment WHERE appointment_id = %s AND doctor_id = %s'
    params = [appointment_id, doctor_id]
    if require_scheduled:
        sql += " AND status = 'Scheduled'"
    cur.execute(sql, params)
    if not cur.fetchone():
        raise ValueError('Appointment not found or not actionable.')


def cancel_appointment(doctor_id, appointment_id):
    with db_cursor(commit=True) as cur:
        _assert_doctor_owns_appointment(cur, doctor_id, appointment_id)
        cur.execute('SELECT cancel_appointment(%s)', (int(appointment_id),))


def mark_no_show(doctor_id, appointment_id):
    with db_cursor(commit=True) as cur:
        _assert_doctor_owns_appointment(cur, doctor_id, appointment_id)
        cur.execute(
            "UPDATE appointment SET status = 'No-Show' WHERE appointment_id = %s",
            (int(appointment_id),),
        )


def update_visit(doctor_id, appointment_id, diagnosis, vitals, notes):
    with db_cursor(commit=True) as cur:
        cur.execute(
            '''SELECT 1 FROM visit v
               JOIN appointment a ON v.appointment_id = a.appointment_id
               WHERE v.appointment_id = %s AND a.doctor_id = %s''',
            (appointment_id, doctor_id),
        )
        if not cur.fetchone():
            raise ValueError('Visit not found.')
        cur.execute(
            '''UPDATE visit SET diagnosis = %s, vitals = %s, visit_notes = %s
               WHERE appointment_id = %s''',
            (diagnosis, vitals, notes, appointment_id),
        )


def create_prescription(doctor_id, visit_id, medication_ids, frequencies, durations):
    visit_id = (visit_id or '').strip()
    if not visit_id:
        raise ValueError('Please select a visit.')
    try:
        visit_id_int = int(visit_id)
    except ValueError:
        raise ValueError('Invalid visit selection. Please try again.') from None

    medication_ids = medication_ids or []
    frequencies = frequencies or []
    durations = durations or []
    if not (len(medication_ids) == len(frequencies) == len(durations)):
        raise ValueError('Invalid form submission. Please try again.')

    rows = []
    for med_id, freq, dur in zip(medication_ids, frequencies, durations):
        med_id = (str(med_id).strip() if med_id is not None else '')
        freq = (freq or '').strip()
        dur = (dur or '').strip()

        if not med_id and not freq and not dur:
            continue
        if not med_id:
            raise ValueError('Please select a medication for each row.')
        if not freq or not dur:
            raise ValueError('Please enter a frequency and duration for each medication.')
        if len(freq) > 100 or len(dur) > 100:
            raise ValueError('Frequency and duration must be 100 characters or less.')

        try:
            med_id_int = int(med_id)
        except ValueError:
            raise ValueError('Invalid medication selection. Please try again.') from None

        rows.append((med_id_int, freq, dur))

    if not rows:
        raise ValueError('Please add at least one medication.')

    med_ids = [r[0] for r in rows]
    if len(set(med_ids)) != len(med_ids):
        raise ValueError('Please don’t select the same medication more than once.')

    try:
        with db_cursor(commit=True) as cur:
            cur.execute(
                'SELECT medication_id FROM medication WHERE medication_id = ANY(%s)',
                (med_ids,),
            )
            existing = {r[0] for r in cur.fetchall()}
            missing = [str(m) for m in med_ids if m not in existing]
            if missing:
                raise ValueError('One or more selected medications are invalid. Please re-select.')

            cur.execute('SELECT create_prescription(%s, %s)', (visit_id_int, doctor_id))
            prescription_id = cur.fetchone()[0]

            for med_id_int, freq, dur in rows:
                cur.execute(
                    'INSERT INTO contains VALUES (%s, %s, %s, %s)',
                    (prescription_id, med_id_int, freq, dur),
                )
        return prescription_id
    except ValueError:
        raise
    except psycopg2.Error as e:
        primary = getattr(getattr(e, 'diag', None), 'message_primary', None) or str(e)
        if 'Only the assigned doctor can prescribe for a completed visit.' in primary:
            raise ValueError('You can only prescribe for your own completed visits.') from None
        if 'A prescription already exists for this visit.' in primary:
            raise ValueError('A prescription already exists for this visit.') from None
        raise ValueError('Could not create the prescription. Please review the form and try again.') from None
