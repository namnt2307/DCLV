from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from lib.tools import generate_password

class EHRCreationForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('full_name', 'gender', 'birth_date',
                  'home_address', 'work_address', 'user_identifier')