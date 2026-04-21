import datetime
import json

from django.contrib import messages
from django.shortcuts import redirect, render

from common.decorators import login_required_custom
from common.session import get_user_from_session

from . import selectors, services


def _profile_is_complete(profile):
    # profile tuple: (first_name, last_name, email, phone, dob, gender,
    # address, emergency_contact_name, emergency_contact_phone)
    return bool(profile and profile[4])  # date_of_birth set


@login_required_custom(role='patient')
def patient_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        user = selectors.get_user_name(user_id)
        profile = selectors.get_profile(user_id)
        if not _profile_is_complete(profile):
            messages.error(
                request,
                'Please complete your profile before booking appointments.',
            )
            return redirect('patient_profile')
        appointments = selectors.list_recent_appointments(user_id)
        next_appt = selectors.get_next_scheduled_appointment(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, appointments, next_appt = None, [], None
    return render(request, 'patient/dashboard.html', {
        'user': user,
        'appointments': appointments,
        'next_appt': next_appt,
        'today': datetime.date.today().strftime('%A, %B %d, %Y'),
    })


@login_required_custom(role='patient')
def patient_profile(request):
    user_id, _ = get_user_from_session(request)
    if request.method == 'POST':
        try:
            services.update_profile(
                user_id,
                request.POST.get('phone'),
                request.POST.get('date_of_birth'),
                request.POST.get('gender'),
                request.POST.get('address'),
                request.POST.get('emergency_contact_name'),
                request.POST.get('emergency_contact_phone'),
            )
            messages.success(request, 'Profile updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    try:
        profile = selectors.get_profile(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        profile = None
    return render(request, 'patient/profile.html', {
        'profile': profile,
        'profile_complete': _profile_is_complete(profile),
    })


@login_required_custom(role='patient')
def patient_appointments(request):
    user_id, _ = get_user_from_session(request)

    try:
        if not _profile_is_complete(selectors.get_profile(user_id)):
            messages.error(
                request,
                'Please complete your profile before booking appointments.',
            )
            return redirect('patient_profile')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'cancel':
                services.cancel_appointment(user_id, request.POST.get('cancel_id'))
                messages.success(request, 'Appointment cancelled.')
            elif action == 'reschedule':
                services.reschedule_appointment(
                    user_id,
                    request.POST.get('appointment_id'),
                    request.POST.get('new_date'),
                    request.POST.get('new_time'),
                )
                messages.success(request, 'Appointment rescheduled.')
            else:
                services.book_appointment(
                    user_id,
                    request.POST.get('doctor_id'),
                    request.POST.get('date'),
                    request.POST.get('time'),
                    request.POST.get('reason'),
                )
                messages.success(request, 'Appointment booked successfully.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('patient_appointments')

    try:
        doctors = selectors.list_doctors()
        appointments = selectors.list_all_appointments(user_id)
        availability_map = selectors.availability_map()
    except Exception as e:
        messages.error(request, f'Error: {e}')
        doctors, appointments, availability_map = [], [], {}

    return render(request, 'patient/appointments.html', {
        'appointments': appointments,
        'doctors': doctors,
        'availability_json': json.dumps(availability_map),
    })


@login_required_custom(role='patient')
def patient_medical_history(request):
    user_id, _ = get_user_from_session(request)
    try:
        visits = selectors.list_visits(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        visits = []
    return render(request, 'patient/medical_history.html', {'visits': visits})


@login_required_custom(role='patient')
def patient_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    try:
        prescriptions = selectors.list_prescriptions(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions = []
    return render(request, 'patient/prescriptions.html', {'prescriptions': prescriptions})
