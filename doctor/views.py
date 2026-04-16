import datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from common.decorators import login_required_custom
from common.session import get_user_from_session

from . import selectors, services


@login_required_custom(role='doctor')
def doctor_dashboard(request):
    user_id, _ = get_user_from_session(request)
    try:
        user = selectors.get_user_name(user_id)
        schedule = selectors.get_schedule(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        user, schedule = None, []
    return render(request, 'doctor/dashboard.html', {
        'user': user,
        'schedule': schedule,
        'today': datetime.date.today().strftime('%A, %B %d, %Y'),
    })


@login_required_custom(role='doctor')
def doctor_schedule(request):
    user_id, _ = get_user_from_session(request)
    date = request.GET.get('date', '')
    try:
        schedule = selectors.get_schedule(user_id, date or None)
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
            if action == 'add':
                services.add_availability(
                    user_id,
                    request.POST.get('day_of_week'),
                    request.POST.get('start_time'),
                    request.POST.get('end_time'),
                )
                messages.success(request, 'Availability added.')
            elif action == 'delete':
                services.delete_availability(
                    user_id,
                    request.POST.get('day_of_week'),
                    request.POST.get('start_time'),
                )
                messages.success(request, 'Availability removed.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_availability')

    try:
        availability = selectors.list_availability(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        availability = []
    return render(request, 'doctor/availability.html', {'availability': availability})


@login_required_custom(role='doctor')
def doctor_patient_record(request, patient_id):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST' and request.POST.get('action') == 'record_visit':
        appointment_id = request.POST.get('appointment_id')
        try:
            services.record_visit(
                user_id,
                patient_id,
                appointment_id,
                request.POST.get('diagnosis'),
                request.POST.get('vitals'),
                request.POST.get('notes'),
            )
            messages.success(request, 'Visit recorded. You can now create a prescription.')
            return redirect(f'/doctor/prescriptions/?visit_id={appointment_id}')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_patient_record', patient_id=patient_id)

    try:
        if not selectors.doctor_treats_patient(user_id, patient_id):
            messages.error(request, 'You do not have access to this patient record.')
            return redirect('doctor_dashboard')
        patient = selectors.get_patient_details(patient_id)
        visits = selectors.list_patient_visits(patient_id)
        pending_appointments = selectors.list_pending_appointments(patient_id, user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient, visits, pending_appointments = None, [], []

    return render(request, 'doctor/patient_record.html', {
        'patient': patient,
        'visits': visits,
        'patient_id': patient_id,
        'pending_appointments': pending_appointments,
    })


@login_required_custom(role='doctor')
def doctor_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    selected_visit_id = request.GET.get('visit_id', '')

    if request.method == 'POST':
        try:
            services.create_prescription(
                user_id,
                request.POST.get('visit_id'),
                request.POST.getlist('medication_id'),
                request.POST.getlist('frequency'),
                request.POST.getlist('duration'),
            )
            messages.success(request, 'Prescription created.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_prescriptions')

    try:
        prescriptions = selectors.list_prescriptions(user_id)
        medications = selectors.list_medications()
        visits = selectors.list_visits_for_prescriptions(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        prescriptions, medications, visits = [], [], []

    return render(request, 'doctor/prescriptions.html', {
        'prescriptions': prescriptions,
        'medications': medications,
        'visits': visits,
        'selected_visit_id': selected_visit_id,
    })
