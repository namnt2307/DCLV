from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from lib.tools import generate_password



class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'user_identifier','group_name', 'password1','password2' )
        # fields = ('username','full_name','gender','birth_date','home_address','work_address', 'email', 'user_identifier','group_name', 'password1','password2' )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    def register_save(self,commit=True):
        username = self.cleaned_data.get('user_identifier')
        user = super().save(commit=False)
        user.create_user(username=username)
        user.set_password('nam12345')
        if commit:
            user.save()
        return user
