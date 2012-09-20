from django.db import models
from accounts.models import Settings
from djangotoolbox.fields import ListField

class Row(models.Model):
  settings = models.ForeignKey(Settings)
  columns = ListField(models.TextField())
  order = models.IntegerField(blank=True, null=True) #i should eventually get rid of the blank=True, and null=True
  
  def __unicode__(self):
    return self.settings.user.username + " ["+ ", ".join(self.columns) + "]"
  
