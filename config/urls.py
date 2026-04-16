from django.urls import include, path

urlpatterns = [
    path('', include('common.urls')),
    path('', include('accounts.urls')),
    path('patient/', include('patient.urls')),
    path('doctor/', include('doctor.urls')),
    path('admin/', include('clinic_admin.urls')),
]
