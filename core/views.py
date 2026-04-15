from django.shortcuts import redirect
from .utils import get_user_from_session


def index(request):
    user_id, user_role = get_user_from_session(request)
    if not user_id:
        return redirect('login')
    if user_role == 'patient': return redirect('patient_dashboard')
    if user_role == 'doctor':  return redirect('doctor_dashboard')
    if user_role == 'admin':   return redirect('admin_dashboard')
    return redirect('login')
