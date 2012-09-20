from django import forms

class CSVForm(forms.Form):
  file = forms.FileField()
