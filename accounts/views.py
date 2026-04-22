from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from . import selectors, services
from .forms import DoctorRegisterForm, LoginForm, PatientRegisterForm


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip()
        password = form.cleaned_data['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            try:
                identity = selectors.get_user_login_state_by_email(email)
                if identity:
                    user_id, role, is_active = identity
                    if role == 'doctor' and not is_active:
                        messages.error(
                            request,
                            'Your doctor account is inactive. Please contact a clinic admin.',
                        )
                        return render(request, 'accounts/login.html', {'form': form})

                    login(request, user)
                    request.session['user_id'] = user_id
                    request.session['user_role'] = role
                else:
                    login(request, user)
            except Exception as e:
                messages.error(request, f'Database error: {e}')
            return redirect('index')

        try:
            if not selectors.email_exists(email):
                messages.error(request, 'No account found with that email.')
            else:
                messages.error(request, 'Incorrect password.')
        except Exception:
            messages.error(request, 'Login failed.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    """Role picker landing page."""
    return render(request, 'accounts/register.html')


def register_patient_view(request):
    form = PatientRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.register_patient(form.cleaned_data)
            messages.success(
                request,
                'Account created. Please log in and complete your profile.',
            )
            return redirect('login')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'accounts/register_patient.html', {'form': form})


def register_doctor_view(request):
    form = DoctorRegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.register_doctor(form.cleaned_data)
            messages.success(
                request,
                'Doctor account created. Please log in and complete your profile.',
            )
            return redirect('login')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'accounts/register_doctor.html', {'form': form})
