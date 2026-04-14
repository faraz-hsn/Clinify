from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('patient/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),

    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('doctor/patient/<int:patient_id>/', views.doctor_patient_record, name='doctor_patient_record'),
    path('doctor/prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('doctor/availability/', views.doctor_availability, name='doctor_availability'),

    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/appointments/', views.admin_appointments, name='admin_appointments'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/medications/', views.admin_medications, name='admin_medications'),
]