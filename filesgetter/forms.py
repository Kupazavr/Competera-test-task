from django import forms

from django import forms

class UploadFileForm(forms.Form):
    ftpurl = forms.CharField(label='url')
    ftplogin = forms.CharField(label='login')
    ftppassword = forms.CharField(label='password')
    file = forms.FileField(label='FirstCSVFile')
    file2 = forms.FileField(label='SecondCSVFile')
