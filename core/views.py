import hashlib
import functools
import json
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import get_connection
from .forms import LoginForm, RegisterForm


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_from_session(request):
    return request.session.get('user_id'), request.session.get('user_role')

def login_required_custom(role=None):
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id, user_role = get_user_from_session(request)
            if not user_id:
                return redirect('login')
            if role and user_role != role:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ── AUTH ─────────────────────────────────────────────────

def index(request):
    user_id, user_role = get_user_from_session(request)
    if not user_id:
        return redirect('login')
    if user_role == 'patient': return redirect('patient_dashboard')
    if user_role == 'doctor':  return redirect('doctor_dashboard')
    if user_role == 'admin':   return redirect('admin_dashboard')
    return redirect('login')


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email'].strip()
        password = hash_password(form.cleaned_data['password'])
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                'SELECT user_id, password_hash, role FROM "USER" WHERE LOWER(email) = LOWER(%s)',
                (email,)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
            if not user:
                messages.error(request, 'No account found with that email.')
            elif user[1] != password:
                messages.error(request, 'Incorrect password.')
            else:
                request.session['user_id']   = user[0]
                request.session['user_role'] = user[2]
                return redirect('index')
        except Exception as e:
            messages.error(request, f'Database error: {e}')
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    return redirect('login')


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        password_hash = hash_password(d['password'])
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute('SELECT user_id FROM "USER" WHERE LOWER(email) = LOWER(%s)', (d['email'],))
            if cur.fetchone():
                messages.error(request, 'An account with this email already exists.')
                cur.close()
                conn.close()
                return render(request, 'core/register.html', {'form': form})
            cur.execute(
                '''INSERT INTO "USER" (first_name, last_name, email, phone, password_hash, role)
                   VALUES (%s,%s,%s,%s,%s,'patient') RETURNING user_id''',
                (d['first_name'], d['last_name'], d['email'], d['phone'], password_hash)
            )
            user_id = cur.fetchone()[0]
            cur.execute(
                '''INSERT INTO patient (patient_id, date_of_birth, gender, address,
                   emergency_contact_name, emergency_contact_phone)
                   VALUES (%s,%s,%s,%s,%s,%s)''',
                (user_id, d['date_of_birth'], d['gender'],
                 d['address'], d['emergency_contact_name'], d['emergency_contact_phone'])
            )
            cur.execute('INSERT INTO medical_record (patient_id, record_number) VALUES (%s, 1)', (user_id,))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'core/register.html', {'form': form})


# ── PATIENT ──────────────────────────────────────────────

@login_required_custom(role='patient')
def patient_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute('SELECT first_name, last_name FROM "USER" WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || \' \' || u.last_name AS doctor_name
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
    return render(request, 'core/patient_dashboard.html', {
        'user': user,
        'appointments': appointments,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='patient')
def patient_profile(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        if request.method == 'POST':
            cur.execute('UPDATE "USER" SET phone = %s WHERE user_id = %s', (request.POST.get('phone'), user_id))
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
    return render(request, 'core/patient_profile.html', {'profile': profile})


@login_required_custom(role='patient')
def patient_appointments(request):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'cancel':
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute('SELECT cancel_appointment(%s)', (request.POST.get('cancel_id'),))
                conn.commit()
                cur.close()
                conn.close()
                messages.success(request, 'Appointment cancelled.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        elif action == 'reschedule':
            try:
                conn = get_connection()
                cur  = conn.cursor()
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
            date      = request.POST.get('date')
            time      = request.POST.get('time')
            reason    = request.POST.get('reason')
            try:
                conn = get_connection()
                cur  = conn.cursor()
                day_name = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%A')
                cur.execute(
                    '''SELECT 1 FROM availability WHERE doctor_id = %s AND day_of_week = %s
                       AND start_time <= %s AND end_time >= %s''',
                    (doctor_id, day_name, time, time)
                )
                if not cur.fetchone():
                    messages.error(request, 'Doctor is not available at that time.')
                else:
                    cur.execute('SELECT book_appointment(%s,%s,%s,%s,%s)', (user_id, doctor_id, date, time, reason))
                    conn.commit()
                    messages.success(request, 'Appointment booked successfully.')
                cur.close()
                conn.close()
            except Exception as e:
                messages.error(request, f'Error: {e}')
        return redirect('patient_appointments')

    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT d.doctor_id, u.first_name || \' \' || u.last_name, d.specialty
               FROM doctor d JOIN "USER" u ON d.doctor_id = u.user_id'''
        )
        doctors = cur.fetchall()
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      u.first_name || \' \' || u.last_name AS doctor_name
               FROM appointment a
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" u ON d.doctor_id = u.user_id
               WHERE a.patient_id = %s ORDER BY a.appointment_date DESC''',
            (user_id,)
        )
        appointments = cur.fetchall()
        cur.execute('SELECT doctor_id, day_of_week, start_time, end_time FROM availability ORDER BY doctor_id')
        avail_rows = cur.fetchall()
        availability_map = {}
        for row in avail_rows:
            did = str(row[0])
            if did not in availability_map:
                availability_map[did] = []
            availability_map[did].append({'day': row[1], 'start': str(row[2])[:5], 'end': str(row[3])[:5]})
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        doctors, appointments, availability_map = [], [], {}

    return render(request, 'core/patient_appointments.html', {
        'appointments': appointments,
        'doctors': doctors,
        'availability_json': json.dumps(availability_map)
    })


@login_required_custom(role='patient')
def patient_medical_history(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes,
                      u.first_name || \' \' || u.last_name AS doctor_name
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
    return render(request, 'core/patient_medical_history.html', {'visits': visits})


@login_required_custom(role='patient')
def patient_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT p.prescription_id, p.issue_date,
                      u.first_name || \' \' || u.last_name AS doctor_name,
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
    return render(request, 'core/patient_prescriptions.html', {'prescriptions': prescriptions})


# ── DOCTOR ───────────────────────────────────────────────

@login_required_custom(role='doctor')
def doctor_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute('SELECT first_name, last_name FROM "USER" WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        cur.execute('SELECT * FROM get_doctor_schedule(%s, CURRENT_DATE)', (user_id,))
        schedule = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, schedule = None, []
    return render(request, 'core/doctor_dashboard.html', {
        'user': user, 'schedule': schedule,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='doctor')
def doctor_schedule(request):
    user_id, _ = get_user_from_session(request)
    date = request.GET.get('date', '')
    try:
        conn = get_connection()
        cur  = conn.cursor()
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
    return render(request, 'core/doctor_schedule.html', {'schedule': schedule, 'date': date})


@login_required_custom(role='doctor')
def doctor_availability(request):
    user_id, _ = get_user_from_session(request)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if action == 'add':
                cur.execute(
                    'INSERT INTO availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s,%s,%s,%s)',
                    (user_id, request.POST.get('day_of_week'), request.POST.get('start_time'), request.POST.get('end_time'))
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
        cur  = conn.cursor()
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
    return render(request, 'core/doctor_availability.html', {'availability': availability})

@login_required_custom(role='doctor')
def doctor_patient_record(request, patient_id):
    user_id, _ = get_user_from_session(request)
    if request.method == 'POST':
        action         = request.POST.get('action')
        appointment_id = request.POST.get('appointment_id')
        if action == 'record_visit':
            if not appointment_id:
                messages.error(request, 'Please select an appointment.')
                return redirect('doctor_patient_record', patient_id=patient_id)
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute(
                    """SELECT 1
                       FROM appointment
                       WHERE appointment_id = %s
                         AND patient_id = %s
                         AND doctor_id = %s
                         AND status = 'Scheduled' """,
                    (appointment_id, patient_id, user_id)
                )
                if not cur.fetchone():
                    messages.error(request, 'You can only record visits for your own scheduled appointments.')
                else:
                    cur.execute(
                        'SELECT create_visit(%s, %s, %s, %s, %s, %s)',
                        (int(appointment_id), int(patient_id), 1,
                         request.POST.get('diagnosis'), request.POST.get('vitals'), request.POST.get('notes'))
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
                    messages.success(request, 'Visit recorded successfully. You can now add a prescription.')
                    return redirect(f'/doctor/prescriptions/?visit_id={appointment_id}')
                cur.close()
                conn.close()
            except Exception as e:
                messages.error(request, f'Error: {e}')
        return redirect('doctor_patient_record', patient_id=patient_id)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            """SELECT u.first_name, u.last_name, p.date_of_birth, p.gender, p.address,
                      p.emergency_contact_name, p.emergency_contact_phone
               FROM patient p JOIN "USER" u ON p.patient_id = u.user_id WHERE p.patient_id = %s""",
            (patient_id,)
        )
        patient = cur.fetchone()
        cur.execute(
            'SELECT v.visit_date, v.diagnosis, v.vitals, v.visit_notes FROM visit v WHERE v.patient_id = %s ORDER BY v.visit_date DESC',
            (patient_id,)
        )
        visits = cur.fetchall()
        cur.execute(
            """SELECT appointment_id, appointment_date, appointment_time FROM appointment
               WHERE patient_id = %s AND doctor_id = %s AND status = 'Scheduled' ORDER BY appointment_date""",
            (patient_id, user_id)
        )
        pending_appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient, visits, pending_appointments = None, [], []
    return render(request, 'core/doctor_patient_record.html', {
        'patient': patient, 'visits': visits,
        'patient_id': patient_id, 'pending_appointments': pending_appointments
    })


@login_required_custom(role='doctor')
def doctor_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    selected_visit_id = request.GET.get('visit_id', '')

    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        medication_ids = request.POST.getlist('medication_id')
        frequencies = request.POST.getlist('frequency')
        durations = request.POST.getlist('duration')

        try:
            conn = get_connection()
            cur  = conn.cursor()

            cur.execute(
                """SELECT v.appointment_id
                   FROM visit v
                   JOIN appointment a ON v.appointment_id = a.appointment_id
                   LEFT JOIN prescription p ON p.visit_id = v.appointment_id
                   WHERE v.appointment_id = %s
                     AND a.doctor_id = %s
                     AND a.status = 'Completed'
                     AND p.prescription_id IS NULL""",
                (visit_id, user_id)
            )
            valid_visit = cur.fetchone()

            if not valid_visit:
                messages.error(request, 'That visit is not eligible for a new prescription.')
                cur.close()
                conn.close()
                return redirect('doctor_prescriptions')

            cleaned_rows = []
            for med_id, freq, dur in zip(medication_ids, frequencies, durations):
                med_id = (med_id or '').strip()
                freq = (freq or '').strip()
                dur = (dur or '').strip()
                if med_id and freq and dur:
                    cleaned_rows.append((med_id, freq, dur))

            if not cleaned_rows:
                messages.error(request, 'Please add at least one complete medication row.')
                cur.close()
                conn.close()
                return redirect(f'/doctor/prescriptions/?visit_id={visit_id}')

            cur.execute('SELECT create_prescription(%s,%s)', (visit_id, user_id))
            prescription_id = cur.fetchone()[0]

            for med_id, freq, dur in cleaned_rows:
                cur.execute(
                    'INSERT INTO contains (prescription_id, medication_id, frequency, duration) VALUES (%s,%s,%s,%s)',
                    (prescription_id, med_id, freq, dur)
                )

            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Prescription created successfully.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_prescriptions')
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            """SELECT p.prescription_id, p.issue_date,
                      u.first_name || ' ' || u.last_name AS patient_name,
                      m.medication_name, c.frequency, c.duration
               FROM prescription p
               JOIN visit v ON p.visit_id = v.appointment_id
               JOIN patient pt ON v.patient_id = pt.patient_id
               JOIN "USER" u ON pt.patient_id = u.user_id
               JOIN contains c ON p.prescription_id = c.prescription_id
               JOIN medication m ON c.medication_id = m.medication_id
               WHERE p.doctor_id = %s ORDER BY p.issue_date DESC, p.prescription_id DESC""",
            (user_id,)
        )
        prescriptions = cur.fetchall()

        cur.execute('SELECT medication_id, medication_name FROM medication ORDER BY medication_name')
        medications = cur.fetchall()

        cur.execute(
            """SELECT v.appointment_id, v.visit_date,
                      u.first_name || ' ' || u.last_name AS patient_name
               FROM visit v
               JOIN patient p ON v.patient_id = p.patient_id
               JOIN "USER" u ON p.patient_id = u.user_id
               JOIN appointment a ON v.appointment_id = a.appointment_id
               LEFT JOIN prescription pr ON pr.visit_id = v.appointment_id
               WHERE a.doctor_id = %s
                 AND a.status = 'Completed'
                 AND pr.prescription_id IS NULL
               ORDER BY v.visit_date DESC, v.appointment_id DESC""",
            (user_id,)
        )
        visits = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions, medications, visits = [], [], []
    return render(request, 'core/doctor_prescriptions.html', {
        'prescriptions': prescriptions,
        'medications': medications,
        'visits': visits,
        'selected_visit_id': str(selected_visit_id),
    })


# ── ADMIN ────────────────────────────────────────────────

@login_required_custom(role='admin')
def admin_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM patient')
        patient_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM doctor')
        doctor_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM appointment WHERE status = 'Scheduled'")
        pending_count = cur.fetchone()[0]
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status,
                      pu.first_name || \' \' || pu.last_name AS patient_name,
                      du.first_name || \' \' || du.last_name AS doctor_name
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" pu ON p.patient_id = pu.user_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" du ON d.doctor_id = du.user_id
               ORDER BY a.appointment_date DESC LIMIT 10'''
        )
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient_count = doctor_count = pending_count = 0
        appointments = []
    return render(request, 'core/admin_dashboard.html', {
        'patient_count': patient_count, 'doctor_count': doctor_count,
        'pending_count': pending_count, 'appointments': appointments,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='admin')
def admin_appointments(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action         = request.POST.get('action')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if action == 'cancel':
                cur.execute('SELECT cancel_appointment(%s)', (appointment_id,))
            elif action == 'update_status':
                cur.execute(
                    'UPDATE appointment SET status = %s WHERE appointment_id = %s',
                    (request.POST.get('status'), appointment_id)
                )
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Appointment updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_appointments')
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                      a.status, a.reason,
                      pu.first_name || \' \' || pu.last_name AS patient_name,
                      du.first_name || \' \' || du.last_name AS doctor_name
               FROM appointment a
               JOIN patient p ON a.patient_id = p.patient_id
               JOIN "USER" pu ON p.patient_id = pu.user_id
               JOIN doctor d ON a.doctor_id = d.doctor_id
               JOIN "USER" du ON d.doctor_id = du.user_id
               ORDER BY a.appointment_date DESC'''
        )
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        appointments = []
    return render(request, 'core/admin_appointments.html', {'appointments': appointments})


@login_required_custom(role='admin')
def admin_users(request):
    if request.method == 'POST':
        action  = request.POST.get('action')
        user_id = request.POST.get('user_id')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if action == 'edit':
                cur.execute(
                    'UPDATE "USER" SET first_name=%s, last_name=%s, phone=%s, role=%s WHERE user_id=%s',
                    (request.POST.get('first_name'), request.POST.get('last_name'),
                     request.POST.get('phone'), request.POST.get('role'), user_id)
                )
                messages.success(request, 'User updated.')
            elif action == 'delete':
                cur.execute('DELETE FROM "USER" WHERE user_id = %s', (user_id,))
                messages.success(request, 'User deleted.')
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_users')
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            'SELECT user_id, first_name, last_name, email, phone, role FROM "USER" ORDER BY role, last_name'
        )
        users = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        users = []
    return render(request, 'core/admin_users.html', {'users': users})


@login_required_custom(role='admin')
def admin_medications(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if action == 'add':
                cur.execute(
                    'INSERT INTO medication (medication_name, description, dosage_form) VALUES (%s,%s,%s)',
                    (request.POST.get('name'), request.POST.get('description'), request.POST.get('dosage_form'))
                )
            elif action == 'delete':
                cur.execute('DELETE FROM medication WHERE medication_id = %s', (request.POST.get('medication_id'),))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Medications updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_medications')
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute('SELECT medication_id, medication_name, description, dosage_form FROM medication')
        medications = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        medications = []
    return render(request, 'core/admin_medications.html', {'medications': medications})
