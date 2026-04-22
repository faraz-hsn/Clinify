import datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.forms import AdminCreateForm
from common.decorators import login_required_custom

from . import selectors, services


@login_required_custom(role='admin')
def admin_dashboard(request):
    try:
        patient_count, doctor_count, pending_count = selectors.dashboard_counts()
        appointments = selectors.list_recent_appointments()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient_count = doctor_count = pending_count = 0
        appointments = []
    return render(request, 'clinic_admin/dashboard.html', {
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'pending_count': pending_count,
        'appointments': appointments,
        'today': datetime.date.today().strftime('%A, %B %d, %Y'),
    })


@login_required_custom(role='admin')
def admin_appointments(request):
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        try:
            if action == 'cancel':
                services.cancel_appointment(appointment_id)
            elif action == 'update_status':
                services.update_appointment_status(
                    appointment_id, request.POST.get('status'),
                )
            messages.success(request, 'Appointment updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_appointments')

    try:
        appointments = selectors.list_all_appointments()
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
            if action == 'edit':
                services.update_user(
                    user_id,
                    request.POST.get('first_name'),
                    request.POST.get('last_name'),
                    request.POST.get('phone'),
                    None,
                )
                messages.success(request, 'Staff member updated.')
            elif action == 'toggle_active':
                is_active = request.POST.get('is_active') == '1'
                services.set_doctor_active(user_id, is_active)
                messages.success(
                    request,
                    'Doctor account activated.' if is_active else 'Doctor account deactivated.',
                )
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_users')

    try:
        users = selectors.list_users()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        users = []
    return render(request, 'clinic_admin/users.html', {'users': users})


@login_required_custom(role='admin')
def admin_create_admin(request):
    form = AdminCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.create_admin(form.cleaned_data)
            messages.success(
                request,
                f"Admin account created for {form.cleaned_data['email']}.",
            )
            return redirect('admin_create_admin')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'clinic_admin/create_admin.html', {'form': form})


@login_required_custom(role='admin')
def admin_medications(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add':
                services.add_medication(
                    request.POST.get('name'),
                    request.POST.get('description'),
                    request.POST.get('dosage_form'),
                )
            elif action == 'delete':
                services.delete_medication(request.POST.get('medication_id'))
            messages.success(request, 'Medications updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('admin_medications')

    try:
        medications = selectors.list_medications()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        medications = []
    return render(request, 'clinic_admin/medications.html', {'medications': medications})
