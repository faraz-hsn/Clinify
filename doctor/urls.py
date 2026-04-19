from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('patient/<int:patient_id>/', views.doctor_patient_record, name='doctor_patient_record'),
    path('prescriptions/', views.doctor_prescriptions, name='doctor_prescriptions'),
    path('availability/', views.doctor_availability, name='doctor_availability'),
    path('profile/', views.doctor_profile, name='doctor_profile'),
]
