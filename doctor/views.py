import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import get_connection
from core.utils import get_user_from_session, login_required_custom


@login_required_custom(role='doctor')
def doctor_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT first_name, last_name FROM "USER" WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        cur.execute('SELECT * FROM get_doctor_schedule(%s, CURRENT_DATE)', (user_id,))
        schedule = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, schedule = None, []
    return render(request, 'doctor/dashboard.html', {
        'user': user, 'schedule': schedule,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='doctor')
def doctor_schedule(request):
    user_id, _ = get_user_from_session(request)
    date = request.GET.get('date', '')
    try:
        conn = get_connection()
        cur = conn.cursor()
        if date:
            cur.execute('SELECT * FROM get_doctor_schedule(%s, %s)', (user_id, date))
        else:
            cur.execute('SELECT * FROM get_doctor_schedule(%s, CURRENT_DATE)', (user_id,))
        schedule = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        schedule = []
    return render(request, 'doctor/schedule.html', {'schedule': schedule, 'date': date})


@login_required_custom(role='doctor')
def doctor_availability(request):
    user_id, _ = get_user_from_session(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            conn = get_connection()
            cur = conn.cursor()
            if action == 'add':
                cur.execute(
                    'INSERT INTO availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s,%s,%s,%s)',
                    (user_id, request.POST.get('day_of_week'),
                     request.POST.get('start_time'), request.POST.get('end_time'))
                )
                messages.success(request, 'Availability added.')
            elif action == 'delete':
                cur.execute(
                    'DELETE FROM availability WHERE doctor_id = %s AND day_of_week = %s AND start_time = %s',
                    (user_id, request.POST.get('day_of_week'), request.POST.get('start_time'))
                )
                messages.success(request, 'Availability removed.')
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_availability')
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            '''SELECT day_of_week, start_time, end_time FROM availability WHERE doctor_id = %s
               ORDER BY CASE day_of_week
                 WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 WHEN 'Sunday' THEN 7
               END''',
            (user_id,)
        )
        availability = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        availability = []
    return render(request, 'doctor/availability.html', {'availability': availability})


@login_required_custom(role='doctor')
def doctor_patient_record(request, patient_id):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        appointment_id = request.POST.get('appointment_id')
        if action == 'record_visit':
            if not appointment_id:
                messages.error(request, 'Please select an appointment.')
                return redirect('doctor_patient_record', patient_id=patient_id)
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    '''SELECT 1 FROM appointment
                       WHERE appointment_id = %s AND patient_id = %s
                         AND doctor_id = %s AND status = 'Scheduled' ''',
                    (appointment_id, patient_id, user_id)
                )
                if not cur.fetchone():
                    messages.error(request, 'You can only record visits for your own scheduled appointments.')
                    cur.close()
                    conn.close()
                else:
                    cur.execute(
                        'SELECT create_visit(%s, %s, %s, %s, %s, %s)',
                        (int(appointment_id), int(patient_id), 1,
                         request.POST.get('diagnosis'), request.POST.get('vitals'),
                         request.POST.get('notes'))
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    messages.success(request, 'Visit recorded. You can now create a prescription.')
                    return redirect(f'/doctor/prescriptions/?visit_id={appointment_id}')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        return redirect('doctor_patient_record', patient_id=patient_id)

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            'SELECT 1 FROM appointment WHERE patient_id = %s AND doctor_id = %s LIMIT 1',
            (patient_id, user_id)
        )
        if not cur.fetchone():
            cur.close()
            conn.close()
            messages.error(request, 'You do not have access to this patient record.')
            return redirect('doctor_dashboard')

        cur.execute(
            '''SELECT u.first_name, u.last_name, p.date_of_birth, p.gender, p.address,
                      p.emergency_contact_name, p.emergency_contact_phone
               FROM patient p JOIN "USER" u ON p.patient_id = u.user_id
               WHERE p.patient_id = %s''',
            (patient_id,)
        )
        patient = cur.fetchone()
        cur.execute(
            '''SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes
               FROM visit v WHERE v.patient_id = %s ORDER BY v.visit_date DESC''',
            (patient_id,)
        )
        visits = cur.fetchall()
        cur.execute(
            '''SELECT appointment_id, appointment_date, appointment_time FROM appointment
               WHERE patient_id = %s AND doctor_id = %s AND status = 'Scheduled'
               ORDER BY appointment_date''',
            (patient_id, user_id)
        )
        pending_appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient, visits, pending_appointments = None, [], []

    return render(request, 'doctor/patient_record.html', {
        'patient': patient, 'visits': visits,
        'patient_id': patient_id, 'pending_appointments': pending_appointments
    })


@login_required_custom(role='doctor')
def doctor_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    selected_visit_id = request.GET.get('visit_id', '')

    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute('SELECT create_prescription(%s,%s)', (visit_id, user_id))
            prescription_id = cur.fetchone()[0]
            for med_id, freq, dur in zip(
                request.POST.getlist('medication_id'),
                request.POST.getlist('frequency'),
                request.POST.getlist('duration')
            ):
                cur.execute('INSERT INTO contains VALUES (%s,%s,%s,%s)',
                            (prescription_id, med_id, freq, dur))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Prescription created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_prescriptions')

    try:
        conn = get_connection()
        cur = conn.cursor()
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
            (user_id,)
        )
        prescriptions = cur.fetchall()
        cur.execute('SELECT medication_id, medication_name FROM medication')
        medications = cur.fetchall()
        cur.execute(
            '''SELECT v.appointment_id, v.visit_date,
                      u.first_name || ' ' || u.last_name AS patient_name
               FROM visit v
               JOIN patient p ON v.patient_id = p.patient_id
               JOIN "USER" u ON p.patient_id = u.user_id
               JOIN appointment a ON v.appointment_id = a.appointment_id
               WHERE a.doctor_id = %s''',
            (user_id,)
        )
        visits = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions, medications, visits = [], [], []

    return render(request, 'doctor/prescriptions.html', {
        'prescriptions': prescriptions,
        'medications': medications,
        'visits': visits,
        'selected_visit_id': selected_visit_id
    })
