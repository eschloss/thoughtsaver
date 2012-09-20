from django.db import models
from django.contrib.auth.models import User

class Settings(models.Model):
  user = models.ForeignKey(User, unique=True)
  joined = models.DateTimeField(auto_now_add=True)
  lastOn = models.DateTimeField(auto_now=True)
  activationKey = models.CharField(max_length=80)
  dailyTestMaxItems = models.IntegerField(default=10)
  keyExpires = models.DateTimeField()
  denormalized_nextTest = models.DateField(blank=True, null=True)
  receiveEmail = models.BooleanField(default=True)