from django import forms
from .models import Worker, Company, Contractor
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UploadEmployeeDataForm(forms.Form):
    file = forms.FileField(required=False, label='Upload Excel/CSV')
    google_sheet_url = forms.URLField(required=False, label='Google Sheet URL')

class LogoUploadForm(forms.ModelForm):
    class Meta:
        model = Company  # Or Contractor, reuse with dynamic
        fields = ['logo']

class BulkActionForm(forms.Form):
    action = forms.ChoiceField(choices=[('delete', 'Delete'), ('assign', 'Assign to Contractor')])
    contractor = forms.ModelChoiceField(queryset=Contractor.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['contractor'].queryset = Contractor.objects.filter(company=company)

class RegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'user_type']