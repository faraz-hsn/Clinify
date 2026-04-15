from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('appointments/', views.patient_appointments, name='patient_appointments'),
    path('medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('profile/', views.patient_profile, name='patient_profile'),
]
