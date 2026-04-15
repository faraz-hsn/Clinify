import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from core.models import get_connection
from core.utils import get_user_from_session, login_required_custom


@login_required_custom(role='admin')
def admin_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM patient')
        patient_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM doctor')
        doctor_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM appointment WHERE status = 'Scheduled'")
        pending_count = cur.fetchone()[0]
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
               ORDER BY a.appointment_date DESC LIMIT 10'''
        )
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient_count = doctor_count = pending_count = 0
        appointments = []
    return render(request, 'clinic_admin/dashboard.html', {
        'patient_count': patient_count, 'doctor_count': doctor_count,
        'pending_count': pending_count, 'appointments': appointments,
        'today': datetime.date.today().strftime('%A, %B %d, %Y')
    })


@login_required_custom(role='admin')
def admin_appointments(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        try:
            conn = get_connection()
            cur = conn.cursor()
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
        cur = conn.cursor()
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
        appointments = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        appointments = []
    return render(request, 'clinic_admin/appointments.html', {'appointments': appointments})


@login_required_custom(role='admin')
def admin_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        try:
            conn = get_connection()
            cur = conn.cursor()
            if action == 'edit':
                new_role = request.POST.get('role')
                cur.execute('SELECT role FROM "USER" WHERE user_id = %s', (user_id,))
                current = cur.fetchone()
                if current and current[0] != new_role:
                    messages.error(request, f'Role change not allowed. User is currently a {current[0]}. Delete and re-create the account to change roles.')
                    cur.close()
                    conn.close()
                    return redirect('admin_users')
                cur.execute(
                    'UPDATE "USER" SET first_name=%s, last_name=%s, phone=%s WHERE user_id=%s',
                    (request.POST.get('first_name'), request.POST.get('last_name'),
                     request.POST.get('phone'), user_id)
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
        cur = conn.cursor()
        cur.execute(
            'SELECT user_id, first_name, last_name, email, phone, role FROM "USER" ORDER BY role, last_name'
        )
        users = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        users = []
    return render(request, 'clinic_admin/users.html', {'users': users})


@login_required_custom(role='admin')
def admin_medications(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            conn = get_connection()
            cur = conn.cursor()
            if action == 'add':
                cur.execute(
                    'INSERT INTO medication (medication_name, description, dosage_form) VALUES (%s,%s,%s)',
                    (request.POST.get('name'), request.POST.get('description'),
                     request.POST.get('dosage_form'))
                )
            elif action == 'delete':
                cur.execute('DELETE FROM medication WHERE medication_id = %s',
                            (request.POST.get('medication_id'),))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Medications updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_medications')
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT medication_id, medication_name, description, dosage_form FROM medication')
        medications = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        medications = []
    return render(request, 'clinic_admin/medications.html', {'medications': medications})
