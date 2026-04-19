from django import forms
from django.conf import settings


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class BaseRegisterForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Passwords do not match')
        return cleaned_data


class PatientRegisterForm(BaseRegisterForm):
    pass


# Kept for backwards compatibility with any existing imports.
RegisterForm = PatientRegisterForm


class DoctorRegisterForm(BaseRegisterForm):
    license_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Medical License Number'})
    )

    def clean_email(self):
        email = super().clean_email()
        domain = email.rsplit('@', 1)[-1] if '@' in email else ''
        allowed = [d.lower() for d in settings.STAFF_EMAIL_DOMAINS]
        if domain not in allowed:
            raise forms.ValidationError(
                'Doctor registration requires an email from: '
                + ', '.join('@' + d for d in allowed)
            )
        return email
