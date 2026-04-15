import json
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import get_connection
from core.utils import get_user_from_session, login_required_custom


@login_required_custom(role='patient')
def patient_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT first_name, last_name FROM "USER" WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || ' ' || u.last_name AS doctor_name
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s
               ORDER BY a.appointment_date DESC LIMIT 5''',
            (user_id,)
        )
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, appointments = None, []
    return render(request, 'patient/dashboard.html', {
        'user': user,
        'appointments': appointments,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='patient')
def patient_profile(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
        if request.method == 'POST':
            cur.execute('UPDATE "USER" SET phone = %s WHERE user_id = %s',
                        (request.POST.get('phone'), user_id))
            cur.execute(
                '''UPDATE patient SET address = %s, emergency_contact_name = %s,
                   emergency_contact_phone = %s WHERE patient_id = %s''',
                (request.POST.get('address'), request.POST.get('emergency_contact_name'),
                 request.POST.get('emergency_contact_phone'), user_id)
            )
            conn.commit()
            messages.success(request, 'Profile updated.')
        cur.execute(
            '''SELECT u.first_name, u.last_name, u.email, u.phone,
                      p.date_of_birth, p.gender, p.address,
                      p.emergency_contact_name, p.emergency_contact_phone
               FROM "USER" u JOIN patient p ON u.user_id = p.patient_id
               WHERE u.user_id = %s''',
            (user_id,)
        )
        profile = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        profile = None
    return render(request, 'patient/profile.html', {'profile': profile})


@login_required_custom(role='patient')
def patient_appointments(request):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            cancel_id = request.POST.get('cancel_id')
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    '''SELECT 1 FROM appointment
                       WHERE appointment_id = %s AND patient_id = %s AND status = 'Scheduled' ''',
                    (cancel_id, user_id)
                )
                if not cur.fetchone():
                    messages.error(request, 'Cannot cancel this appointment.')
                else:
                    cur.execute('SELECT cancel_appointment(%s)', (cancel_id,))
                    conn.commit()
                    messages.success(request, 'Appointment cancelled.')
                cur.close()
                conn.close()
            except Exception as e:
                messages.error(request, f'Error: {e}')

        elif action == 'reschedule':
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    '''UPDATE appointment SET appointment_date = %s, appointment_time = %s
                       WHERE appointment_id = %s AND patient_id = %s AND status = 'Scheduled' ''',
                    (request.POST.get('new_date'), request.POST.get('new_time'),
                     request.POST.get('appointment_id'), user_id)
                )
                conn.commit()
                cur.close()
                conn.close()
                messages.success(request, 'Appointment rescheduled.')
            except Exception as e:
                messages.error(request, f'Error: {e}')

        else:
            doctor_id = request.POST.get('doctor_id')
            date = request.POST.get('date')
            time = request.POST.get('time')
            reason = request.POST.get('reason')
            try:
                conn = get_connection()
                cur = conn.cursor()
                day_name = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%A')

                cur.execute(
                    '''SELECT 1 FROM availability WHERE doctor_id = %s AND day_of_week = %s
                       AND start_time <= %s AND end_time >= %s''',
                    (doctor_id, day_name, time, time)
                )
                if not cur.fetchone():
                    messages.error(request, 'Doctor is not available at that time.')
                else:
                    cur.execute(
                        '''SELECT 1 FROM appointment
                           WHERE doctor_id = %s
                             AND appointment_date = %s
                             AND appointment_time = %s
                             AND status = 'Scheduled' ''',
                        (doctor_id, date, time)
                    )
                    if cur.fetchone():
                        messages.error(request, 'This time slot is already booked. Please choose another time.')
                    else:
                        cur.execute('SELECT book_appointment(%s,%s,%s,%s,%s)',
                                    (user_id, doctor_id, date, time, reason))
                        conn.commit()
                        messages.success(request, 'Appointment booked successfully.')
                cur.close()
                conn.close()
            except Exception as e:
                messages.error(request, f'Error: {e}')

        return redirect('patient_appointments')

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            '''SELECT d.doctor_id, u.first_name || ' ' || u.last_name, d.specialty
               FROM doctor d JOIN "USER" u ON d.doctor_id = u.user_id'''
        )
        doctors = cur.fetchall()
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || ' ' || u.last_name AS doctor_name
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s ORDER BY a.appointment_date DESC''',
            (user_id,)
        )
        appointments = cur.fetchall()
        cur.execute(
            'SELECT doctor_id, day_of_week, start_time, end_time FROM availability ORDER BY doctor_id'
        )
        avail_rows = cur.fetchall()
        availability_map = {}
        for row in avail_rows:
            did = str(row[0])
            if did not in availability_map:
                availability_map[did] = []
            availability_map[did].append({
                'day': row[1], 'start': str(row[2])[:5], 'end': str(row[3])[:5]
            })
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        doctors, appointments, availability_map = [], [], {}

    return render(request, 'patient/appointments.html', {
        'appointments': appointments,
        'doctors': doctors,
        'availability_json': json.dumps(availability_map)
    })


@login_required_custom(role='patient')
def patient_medical_history(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            '''SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes,
                      u.first_name || ' ' || u.last_name AS doctor_name
               FROM visit v
               JOIN appointment a ON v.appointment_id = a.appointment_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE v.patient_id = %s ORDER BY v.visit_date DESC''',
            (user_id,)
        )
        visits = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        visits = []
    return render(request, 'patient/medical_history.html', {'visits': visits})


@login_required_custom(role='patient')
def patient_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
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
            (user_id,)
        )
        prescriptions = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions = []
    return render(request, 'patient/prescriptions.html', {'prescriptions': prescriptions})
