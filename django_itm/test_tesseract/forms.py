from django import forms
from .models import Docs

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = Docs
        fields = ['file']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class DocumentDeleteForm(forms.Form):
    doc_id = forms.IntegerField()