from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from core.models import get_connection
from .forms import LoginForm, RegisterForm


def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip()
        password = form.cleaned_data['password']

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # Store clinic-specific session data
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    'SELECT user_id, role FROM "USER" WHERE LOWER(email) = LOWER(%s)',
                    (email,)
                )
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    request.session['user_id'] = row[0]
                    request.session['user_role'] = row[1]
            except Exception as e:
                messages.error(request, f'Database error: {e}')
            return redirect('index')
        else:
            # Determine specific error message
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    'SELECT user_id FROM "USER" WHERE LOWER(email) = LOWER(%s)',
                    (email,)
                )
                if not cur.fetchone():
                    messages.error(request, 'No account found with that email.')
                else:
                    messages.error(request, 'Incorrect password.')
                cur.close()
                conn.close()
            except Exception:
                messages.error(request, 'Login failed.')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        password_hash = make_password(d['password'])
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM "USER" WHERE LOWER(email) = LOWER(%s)', (d['email'],))
            if cur.fetchone():
                messages.error(request, 'An account with this email already exists.')
                cur.close()
                conn.close()
                return render(request, 'accounts/register.html', {'form': form})
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
    return render(request, 'accounts/register.html', {'form': form})
