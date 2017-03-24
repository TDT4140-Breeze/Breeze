from django import forms
from chat.models import Login

class LoginForm(forms.Form):
    class Meta:
        widgets = {'password': forms.PasswordInput()}
        model = Login

    user_email = forms.EmailField()
    user_password = forms.PasswordInput()
    password_retype = forms.PasswordInput()
