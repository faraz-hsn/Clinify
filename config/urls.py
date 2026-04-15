from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('patient/', include('patient.urls')),
    path('doctor/', include('doctor.urls')),
    path('admin/', include('clinic_admin.urls')),
]
