import calendar
import datetime
import json

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from common.decorators import login_required_custom
from common.session import get_user_from_session

from . import selectors, services


def _profile_is_complete(profile):
    # profile tuple: (first_name, last_name, email, phone, specialty, license_number)
    return bool(profile and profile[4])  # specialty set


@login_required_custom(role='doctor')
def doctor_dashboard(request):
    user_id, _ = get_user_from_session(request)
    today = timezone.localdate()

    try:
        if not _profile_is_complete(selectors.get_profile(user_id)):
            messages.error(
                request,
                'Please complete your profile before using the doctor portal.',
            )
            return redirect('doctor_profile')
        user = selectors.get_user_name(user_id)

        month_str = request.GET.get('month') or today.strftime('%Y-%m')
        try:
            year, month = [int(x) for x in month_str.split('-')]
            first_day = datetime.date(year, month, 1)
        except (ValueError, TypeError):
            first_day = today.replace(day=1)
            year, month = first_day.year, first_day.month

        if month == 12:
            next_first = datetime.date(year + 1, 1, 1)
        else:
            next_first = datetime.date(year, month + 1, 1)
        last_day = next_first - datetime.timedelta(days=1)
        prev_first = (first_day - datetime.timedelta(days=1)).replace(day=1)

        selected_str = request.GET.get('date') or today.strftime('%Y-%m-%d')
        try:
            selected = datetime.datetime.strptime(selected_str, '%Y-%m-%d').date()
        except ValueError:
            selected = today

        month_appts = selectors.list_appointments_in_range(user_id, first_day, last_day)
        appt_days = {a[0] for a in month_appts}

        cal = calendar.Calendar(firstweekday=6)
        weeks = []
        for week in cal.monthdatescalendar(year, month):
            row = []
            for d in week:
                row.append({
                    'date': d,
                    'day': d.day,
                    'iso': d.strftime('%Y-%m-%d'),
                    'in_month': d.month == month,
                    'is_today': d == today,
                    'is_selected': d == selected,
                    'has_appt': d in appt_days,
                })
            weeks.append(row)

        selected_schedule = selectors.get_schedule(user_id, selected)

        upcoming = selectors.list_appointments_in_range(
            user_id, today, today + datetime.timedelta(days=14)
        )
    except Exception as e:
        messages.error(request, f'Error: {e}')
        return render(request, 'doctor/dashboard.html', {
            'user': None, 'weeks': [], 'upcoming': [], 'selected_schedule': [],
            'today': today, 'selected': today, 'month_label': today.strftime('%B %Y'),
            'prev_month': '', 'next_month': '', 'current_month': today.strftime('%Y-%m'),
        })

    return render(request, 'doctor/dashboard.html', {
        'user': user,
        'weeks': weeks,
        'upcoming': upcoming,
        'selected_schedule': selected_schedule,
        'today': today,
        'selected': selected,
        'month_label': first_day.strftime('%B %Y'),
        'prev_month': prev_first.strftime('%Y-%m'),
        'next_month': next_first.strftime('%Y-%m'),
        'current_month': first_day.strftime('%Y-%m'),
    })


@login_required_custom(role='doctor')
def doctor_profile(request):
    user_id, _ = get_user_from_session(request)
    if request.method == 'POST':
        try:
            services.update_profile(
                user_id,
                request.POST.get('phone'),
                request.POST.get('specialty'),
            )
            messages.success(request, 'Profile updated.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    try:
        profile = selectors.get_profile(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        profile = None
    return render(request, 'doctor/profile.html', {
        'profile': profile,
        'profile_complete': _profile_is_complete(profile),
    })


@login_required_custom(role='doctor')
def doctor_availability(request):
    user_id, _ = get_user_from_session(request)
    DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']

    form_values = {'days': [], 'start_time': '', 'end_time': ''}
    had_error = False

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'add':
                start = request.POST.get('start_time')
                end = request.POST.get('end_time')
                apply_days = request.POST.getlist('days') or [
                    request.POST.get('day_of_week')
                ]
                apply_days = [d for d in apply_days if d in DAYS]
                form_values = {
                    'days': apply_days, 'start_time': start or '', 'end_time': end or '',
                }
                services.add_availability_slots(user_id, apply_days, start, end)
                messages.success(
                    request,
                    f"Slot added to {len(apply_days)} day{'s' if len(apply_days) != 1 else ''}.",
                )
                return redirect('doctor_availability')
            elif action == 'delete':
                services.delete_availability(
                    user_id,
                    request.POST.get('day_of_week'),
                    request.POST.get('start_time'),
                )
                messages.success(request, 'Time slot removed.')
                return redirect('doctor_availability')
        except ValueError as e:
            messages.error(request, str(e))
            had_error = True
        except Exception:
            messages.error(request, 'Something went wrong. Please try again.')
            had_error = True
        if not had_error:
            return redirect('doctor_availability')

    try:
        rows = selectors.list_availability(user_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        rows = []

    schedule_by_day = {d: [] for d in DAYS}
    for day, start, end in rows:
        schedule_by_day[day].append({'start': start, 'end': end})
    weekly = [
        {'day': d, 'slots': schedule_by_day[d], 'short': d[:3]}
        for d in DAYS
    ]

    return render(request, 'doctor/availability.html', {
        'weekly': weekly,
        'days': DAYS,
        'form_values': form_values,
    })


@login_required_custom(role='doctor')
def doctor_patient_record(request, patient_id):
    user_id, _ = get_user_from_session(request)

    try:
        if not selectors.doctor_treats_patient(user_id, patient_id):
            messages.error(request, 'You do not have access to this patient record.')
            return redirect('doctor_dashboard')
        patient = selectors.get_patient_details(patient_id)
        visits = selectors.list_patient_visits(patient_id)
    except Exception as e:
        messages.error(request, f'Error: {e}')
        patient, visits = None, []

    return render(request, 'doctor/patient_record.html', {
        'patient': patient,
        'visits': visits,
        'patient_id': patient_id,
        'from_appointment': request.GET.get('from'),
    })


@login_required_custom(role='doctor')
def doctor_appointment(request, appointment_id):
    user_id, _ = get_user_from_session(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            if action == 'record_visit':
                patient_id = request.POST.get('patient_id')
                services.record_visit(
                    user_id,
                    patient_id,
                    appointment_id,
                    request.POST.get('diagnosis'),
                    request.POST.get('vitals'),
                    request.POST.get('notes'),
                )
                messages.success(request, 'Visit recorded.')
            elif action == 'update_visit':
                services.update_visit(
                    user_id,
                    appointment_id,
                    request.POST.get('diagnosis'),
                    request.POST.get('vitals'),
                    request.POST.get('notes'),
                )
                messages.success(request, 'Visit updated.')
            elif action == 'cancel':
                services.cancel_appointment(user_id, appointment_id)
                messages.success(request, 'Appointment cancelled.')
            elif action == 'no_show':
                services.mark_no_show(user_id, appointment_id)
                messages.success(request, 'Appointment marked as no-show.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('doctor_appointment', appointment_id=appointment_id)

    try:
        appointment = selectors.get_appointment(user_id, appointment_id)
        if not appointment:
            messages.error(request, 'Appointment not found.')
            return redirect('doctor_dashboard')
        patient_id = appointment[5]
        last_visit = selectors.get_last_visit(patient_id)
        visit = selectors.get_visit_by_appointment(appointment_id)
        prescription = selectors.get_prescription_for_visit(user_id, appointment_id) if visit else None
    except Exception as e:
        messages.error(request, f'Error: {e}')
        return redirect('doctor_dashboard')

    return render(request, 'doctor/appointment.html', {
        'appointment': appointment,
        'last_visit': last_visit,
        'visit': visit,
        'prescription': prescription,
    })


@login_required_custom(role='doctor')
def doctor_prescriptions(request):
    user_id, _ = get_user_from_session(request)
    selected_visit_id = request.GET.get('visit_id', '')

    if request.method == 'POST':
        visit_id = request.POST.get('visit_id')
        return_to_appointment = request.POST.get('return_to_appointment')
        try:
            services.create_prescription(
                user_id,
                visit_id,
                request.POST.getlist('medication_id'),
                request.POST.getlist('frequency'),
                request.POST.getlist('duration'),
            )
            messages.success(request, 'Prescription created.')
            if return_to_appointment and visit_id:
                return redirect('doctor_appointment', appointment_id=visit_id)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception:
            messages.error(request, 'Something went wrong while creating the prescription. Please try again.')
        url = reverse('doctor_prescriptions')
        if visit_id:
            url += f'?visit_id={visit_id}'
        return redirect(url)

    try:
        prescriptions = selectors.list_prescriptions(user_id)
        medications = selectors.list_medications()
        visits = selectors.list_visits_for_prescriptions(user_id)
    except Exception as e:
        messages.error(request, 'Could not load prescriptions. Please try again.')
        prescriptions, medications, visits = [], [], []

    return render(request, 'doctor/prescriptions.html', {
        'prescriptions': prescriptions,
        'medications': medications,
        'visits': visits,
        'selected_visit_id': selected_visit_id,
    })
