from django import forms
from chat.models import Login, User

class LoginForm(forms.Form):
    class Meta:
     #   widgets = {'user_password': forms.PasswordInput(), 'password_retype': forms.PasswordInput()}
        model = User
    user_email = forms.EmailField()
    user_password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)
    password_retype = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)


    def email(self):
        data = self.cleaned_data.get('user_email')
        return data

    def password(self):
        data = self.cleaned_data.get('user_password')
        return data

    def clean(self):
        pass1 = self.cleaned_data.get('user_password')
        pass2 = self.cleaned_data.get('password_retype')
        if pass1 != pass2:
            raise forms.ValidationError("Passwords don't match")
        return self.cleaned_data

class lobbyForm(forms.Form):
    topic = forms.CharField()

    def lobby_topic(self):
        data = self.cleaned_data.get('topic')
        return data