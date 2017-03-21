from django import forms

class LoginForm(forms.Form):
    user_email = forms.EmailField()
    user_password = forms.PasswordInput()
    password_retype = forms.PasswordInput()