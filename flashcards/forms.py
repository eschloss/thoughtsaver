from django import forms
from flashcards.models import *
import logging

TAG_DELIMITER = ','

class CardForm(forms.ModelForm):
  tagField = forms.CharField(max_length=200, required=False)
  source1 = forms.CharField(max_length=200, required=False)
  source2 = forms.CharField(max_length=200, required=False)
  priority = forms.CharField(widget=forms.RadioSelect(choices=PRIORITY_CHOICES), initial='3')
  donottest = forms.BooleanField(initial=True)
  class Meta:
    model = Card
    fields = ('front', 'back', 'private', 'priority', 'donottest')
    widgets = {
            'front': forms.Textarea(),
        }
  def setFront(self, front):
    self.fields['front'].initial = front
  def setBack(self, back):
    self.fields['back'].initial = back
  def setSource(self, source):
    self.fields['source1'].initial = source
  
def tagListClean(tagField):
  tags = tagField.lower().split(TAG_DELIMITER)
  return filter(lambda x: x != None and x!='', map(lambda x: x.strip(), tags))