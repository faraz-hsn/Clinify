from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from . import selectors, services
from .forms import LoginForm, RegisterForm


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip()
        password = form.cleaned_data['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            try:
                identity = selectors.get_user_identity_by_email(email)
                if identity:
                    request.session['user_id'] = identity[0]
                    request.session['user_role'] = identity[1]
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
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.register_patient(form.cleaned_data)
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'accounts/register.html', {'form': form})
