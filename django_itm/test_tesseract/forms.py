from django import forms
from .models import Docs

class UploadFileForm(forms.ModelForm):
    class Meta:
        model = Docs
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError("Файл слишком большой. Максимальный размер 10MB")
        return file

class LoginForm(forms.Form):
    """Форма авторизации"""
    username = forms.CharField(label='Имя пользователя')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

class AnalyzeForm(forms.Form):
    """Форма анализа документа"""
    doc_id = forms.IntegerField(label='ID документа')

from django import forms

from django import forms

from django import forms

class DocumentDeleteForm(forms.Form):
    doc_id = forms.IntegerField(
        label='ID документа для удаления',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )