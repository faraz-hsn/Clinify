from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('appointments/', views.admin_appointments, name='admin_appointments'),
    path('users/', views.admin_users, name='admin_users'),
    path('medications/', views.admin_medications, name='admin_medications'),
]
