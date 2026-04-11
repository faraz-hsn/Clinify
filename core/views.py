import hashlib
import functools
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import get_connection
from .forms import LoginForm, RegisterForm


# ─── helpers ────────────────────────────────────────────

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

# ─── auth ───────────────────────────────────────────────

def index(request):
    user_id, user_role = get_user_from_session(request)
    if not user_id:
        return redirect('login')
    if user_role == 'patient':
        return redirect('patient_dashboard')
    if user_role == 'doctor':
        return redirect('doctor_dashboard')
    if user_role == 'admin':
        return redirect('admin_dashboard')
    return redirect('login')


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = hash_password(form.cleaned_data['password'])
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                'SELECT "User_ID", "Role" FROM "USER" WHERE "Email" = %s AND "Password_Hash" = %s',
                (email, password)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                request.session['user_id']   = user[0]
                request.session['user_role'] = user[1]
                return redirect('index')
            else:
                messages.error(request, 'Invalid email or password')
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

            # check email not already used
            cur.execute('SELECT "User_ID" FROM "USER" WHERE "Email" = %s', (d['email'],))
            if cur.fetchone():
                messages.error(request, 'Email already registered')
                cur.close()
                conn.close()
                return render(request, 'core/register.html', {'form': form})

            # insert into USER
            cur.execute(
                '''INSERT INTO "USER" ("First_Name","Last_Name","Email","Phone","Password_Hash","Role")
                   VALUES (%s,%s,%s,%s,%s,'patient') RETURNING "User_ID"''',
                (d['first_name'], d['last_name'], d['email'], d['phone'], password_hash)
            )
            user_id = cur.fetchone()[0]

            # insert into PATIENT
            cur.execute(
                '''INSERT INTO PATIENT
                   ("Patient_ID","Date_Of_Birth","Gender","Address","Emergency_Contact_Name","Emergency_Contact_Phone")
                   VALUES (%s,%s,%s,%s,%s,%s)''',
                (user_id, d['date_of_birth'], d['gender'],
                 d['address'], d['emergency_contact_name'], d['emergency_contact_phone'])
            )

            # create empty medical record
            cur.execute(
                'INSERT INTO MEDICAL_RECORD ("Patient_ID","Record_Number") VALUES (%s, 1)',
                (user_id,)
            )

            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Account created, please log in')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'core/register.html', {'form': form})


# ─── patient ────────────────────────────────────────────

@login_required_custom(role='patient')
def patient_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()

        cur.execute(
            'SELECT "First_Name","Last_Name" FROM "USER" WHERE "User_ID" = %s',
            (user_id,)
        )
        user = cur.fetchone()

        cur.execute(
            '''SELECT a."Appointment_ID", a."Appointment_Date", a."Appointment_Time",
                      a."Status", a."Reason",
                      u."First_Name" || \' \' || u."Last_Name" AS doctor_name
               FROM APPOINTMENT a
               JOIN DOCTOR d ON a."Doctor_ID" = d."Doctor_ID"
               JOIN "USER" u ON d."Doctor_ID" = u."User_ID"
               WHERE a."Patient_ID" = %s
               ORDER BY a."Appointment_Date" DESC LIMIT 5''',
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
        'appointments': appointments
    })


@login_required_custom(role='patient')
def patient_appointments(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()

        # get all doctors for booking form
        cur.execute(
            '''SELECT d."Doctor_ID", u."First_Name" || \' \' || u."Last_Name", d."Specialty"
               FROM DOCTOR d JOIN "USER" u ON d."Doctor_ID" = u."User_ID"'''
        )
        doctors = cur.fetchall()

        # get patient appointments
        cur.execute(
            '''SELECT a."Appointment_ID", a."Appointment_Date", a."Appointment_Time",
                      a."Status", a."Reason",
                      u."First_Name" || \' \' || u."Last_Name" AS doctor_name
               FROM APPOINTMENT a
               JOIN DOCTOR d ON a."Doctor_ID" = d."Doctor_ID"
               JOIN "USER" u ON d."Doctor_ID" = u."User_ID"
               WHERE a."Patient_ID" = %s
               ORDER BY a."Appointment_Date" DESC''',
            (user_id,)
        )
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        doctors, appointments = [], []

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        date      = request.POST.get('date')
        time      = request.POST.get('time')
        reason    = request.POST.get('reason')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute(
                'SELECT book_appointment(%s,%s,%s,%s,%s)',
                (user_id, doctor_id, date, time, reason)
            )
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Appointment booked successfully')
            return redirect('patient_appointments')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'core/patient_appointments.html', {
        'appointments': appointments,
        'doctors': doctors
    })


@login_required_custom(role='patient')
def patient_medical_history(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT v."Visit_Date", v."Diagnosis", v."Vitals", v."Visit_Notes",
                      u."First_Name" || \' \' || u."Last_Name" AS doctor_name
               FROM VISIT v
               JOIN APPOINTMENT a ON v."Appointment_ID" = a."Appointment_ID"
               JOIN DOCTOR d ON a."Doctor_ID" = d."Doctor_ID"
               JOIN "USER" u ON d."Doctor_ID" = u."User_ID"
               WHERE v."Patient_ID" = %s
               ORDER BY v."Visit_Date" DESC''',
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
            '''SELECT p."Prescription_ID", p."Issue_Date",
                      u."First_Name" || \' \' || u."Last_Name" AS doctor_name,
                      m."Medication_Name", c."Frequency", c."Duration"
               FROM PRESCRIPTION p
               JOIN VISIT v ON p."Visit_ID" = v."Appointment_ID"
               JOIN "USER" u ON p."Doctor_ID" = u."User_ID"
               JOIN CONTAINS c ON p."Prescription_ID" = c."Prescription_ID"
               JOIN MEDICATION m ON c."Medication_ID" = m."Medication_ID"
               WHERE v."Patient_ID" = %s
               ORDER BY p."Issue_Date" DESC''',
            (user_id,)
        )
        prescriptions = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions = []

    return render(request, 'core/patient_prescriptions.html', {'prescriptions': prescriptions})


# ─── doctor ─────────────────────────────────────────────

@login_required_custom(role='doctor')
def doctor_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()

        cur.execute(
            'SELECT "First_Name","Last_Name" FROM "USER" WHERE "User_ID" = %s',
            (user_id,)
        )
        user = cur.fetchone()

        cur.execute(
            'SELECT * FROM get_doctor_schedule(%s, CURRENT_DATE)',
            (user_id,)
        )
        schedule = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, schedule = None, []

    return render(request, 'core/doctor_dashboard.html', {
        'user': user,
        'schedule': schedule
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

    return render(request, 'core/doctor_schedule.html', {
        'schedule': schedule,
        'date': date
    })


@login_required_custom(role='doctor')
def doctor_patient_record(request, patient_id):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()

        cur.execute(
            '''SELECT u."First_Name", u."Last_Name", p."Date_Of_Birth",
                      p."Gender", p."Address", p."Emergency_Contact_Name",
                      p."Emergency_Contact_Phone"
               FROM PATIENT p JOIN "USER" u ON p."Patient_ID" = u."User_ID"
               WHERE p."Patient_ID" = %s''',
            (patient_id,)
        )
        patient = cur.fetchone()

        cur.execute(
            '''SELECT v."Visit_Date", v."Diagnosis", v."Vitals", v."Visit_Notes"
               FROM VISIT v WHERE v."Patient_ID" = %s
               ORDER BY v."Visit_Date" DESC''',
            (patient_id,)
        )
        visits = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient, visits = None, []

    if request.method == 'POST':
        action = request.POST.get('action')
        appointment_id = request.POST.get('appointment_id')

        if action == 'record_visit':
            diagnosis = request.POST.get('diagnosis')
            vitals    = request.POST.get('vitals')
            notes     = request.POST.get('notes')
            try:
                conn = get_connection()
                cur  = conn.cursor()
                cur.execute(
                    'SELECT create_visit(%s,%s,%s,%s,%s,%s)',
                    (appointment_id, patient_id, 1, diagnosis, vitals, notes)
                )
                conn.commit()
                cur.close()
                conn.close()
                messages.success(request, 'Visit recorded')
                return redirect('doctor_patient_record', patient_id=patient_id)
            except Exception as e:
                messages.error(request, f'Error: {e}')

    return render(request, 'core/doctor_patient_record.html', {
        'patient': patient,
        'visits': visits,
        'patient_id': patient_id
    })


@login_required_custom(role='doctor')
def doctor_prescriptions(request):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        try:
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute('SELECT create_prescription(%s,%s)', (visit_id, user_id))
            prescription_id = cur.fetchone()[0]

            medication_ids = request.POST.getlist('medication_id')
            frequencies    = request.POST.getlist('frequency')
            durations      = request.POST.getlist('duration')

            for med_id, freq, dur in zip(medication_ids, frequencies, durations):
                cur.execute(
                    'INSERT INTO CONTAINS VALUES (%s,%s,%s,%s)',
                    (prescription_id, med_id, freq, dur)
                )
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Prescription created')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT p."Prescription_ID", p."Issue_Date",
                      u."First_Name" || \' \' || u."Last_Name" AS patient_name,
                      m."Medication_Name", c."Frequency", c."Duration"
               FROM PRESCRIPTION p
               JOIN VISIT v ON p."Visit_ID" = v."Appointment_ID"
               JOIN PATIENT pt ON v."Patient_ID" = pt."Patient_ID"
               JOIN "USER" u ON pt."Patient_ID" = u."User_ID"
               JOIN CONTAINS c ON p."Prescription_ID" = c."Prescription_ID"
               JOIN MEDICATION m ON c."Medication_ID" = m."Medication_ID"
               WHERE p."Doctor_ID" = %s
               ORDER BY p."Issue_Date" DESC''',
            (user_id,)
        )
        prescriptions = cur.fetchall()

        cur.execute('SELECT "Medication_ID","Medication_Name" FROM MEDICATION')
        medications = cur.fetchall()

        cur.execute(
            '''SELECT v."Appointment_ID", v."Visit_Date",
                      u."First_Name" || \' \' || u."Last_Name" AS patient_name
               FROM VISIT v
               JOIN PATIENT p ON v."Patient_ID" = p."Patient_ID"
               JOIN "USER" u ON p."Patient_ID" = u."User_ID"
               JOIN APPOINTMENT a ON v."Appointment_ID" = a."Appointment_ID"
               WHERE a."Doctor_ID" = %s''',
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
        'visits': visits
    })


# ─── admin ──────────────────────────────────────────────

@login_required_custom(role='admin')
def admin_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur  = conn.cursor()

        cur.execute('SELECT COUNT(*) FROM PATIENT')
        patient_count = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM DOCTOR')
        doctor_count = cur.fetchone()[0]

        cur.execute('SELECT COUNT(*) FROM APPOINTMENT WHERE "Status" = \'Scheduled\'')
        pending_count = cur.fetchone()[0]

        cur.execute(
            '''SELECT a."Appointment_ID", a."Appointment_Date", a."Appointment_Time",
                      a."Status",
                      pu."First_Name" || \' \' || pu."Last_Name" AS patient_name,
                      du."First_Name" || \' \' || du."Last_Name" AS doctor_name
               FROM APPOINTMENT a
               JOIN PATIENT p ON a."Patient_ID" = p."Patient_ID"
               JOIN "USER" pu ON p."Patient_ID" = pu."User_ID"
               JOIN DOCTOR d ON a."Doctor_ID" = d."Doctor_ID"
               JOIN "USER" du ON d."Doctor_ID" = du."User_ID"
               ORDER BY a."Appointment_Date" DESC LIMIT 10'''
        )
        appointments = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient_count = doctor_count = pending_count = 0
        appointments = []

    return render(request, 'core/admin_dashboard.html', {
        'patient_count': patient_count,
        'doctor_count':  doctor_count,
        'pending_count': pending_count,
        'appointments':  appointments
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
                status = request.POST.get('status')
                cur.execute(
                    'UPDATE APPOINTMENT SET "Status" = %s WHERE "Appointment_ID" = %s',
                    (status, appointment_id)
                )
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Appointment updated')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_appointments')

    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT a."Appointment_ID", a."Appointment_Date", a."Appointment_Time",
                      a."Status", a."Reason",
                      pu."First_Name" || \' \' || pu."Last_Name" AS patient_name,
                      du."First_Name" || \' \' || du."Last_Name" AS doctor_name
               FROM APPOINTMENT a
               JOIN PATIENT p ON a."Patient_ID" = p."Patient_ID"
               JOIN "USER" pu ON p."Patient_ID" = pu."User_ID"
               JOIN DOCTOR d ON a."Doctor_ID" = d."Doctor_ID"
               JOIN "USER" du ON d."Doctor_ID" = du."User_ID"
               ORDER BY a."Appointment_Date" DESC'''
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
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute(
            '''SELECT "User_ID","First_Name","Last_Name","Email","Phone","Role"
               FROM "USER" ORDER BY "Role","Last_Name"'''
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
                name        = request.POST.get('name')
                description = request.POST.get('description')
                dosage_form = request.POST.get('dosage_form')
                cur.execute(
                    'INSERT INTO MEDICATION ("Medication_Name","Description","Dosage_Form") VALUES (%s,%s,%s)',
                    (name, description, dosage_form)
                )
            elif action == 'delete':
                med_id = request.POST.get('medication_id')
                cur.execute('DELETE FROM MEDICATION WHERE "Medication_ID" = %s', (med_id,))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Medications updated')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_medications')

    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute('SELECT "Medication_ID","Medication_Name","Description","Dosage_Form" FROM MEDICATION')
        medications = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        medications = []

    return render(request, 'core/admin_medications.html', {'medications': medications})