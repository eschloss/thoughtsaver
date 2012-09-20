from django.db import models
from accounts.models import Settings
from django.db.models.signals import pre_delete, post_save
import logging
from djangotoolbox.fields import ListField
from google.appengine.api import taskqueue
import re
from django.http import HttpResponse
  
PRIORITY_CHOICES = (
  ('0', 'very low'),
  ('1', 'low'),
  ('2', 'average'),
  ('3', 'high'),
  ('4', 'very high'),
)

class Card(models.Model):
  front = models.CharField(max_length=100, null=True, blank=True)
  back = models.TextField()
  settings = models.ForeignKey(Settings, null=True) #Can only be null if it is part of a shareSet
  private = models.BooleanField(default=False)
  donottest = models.BooleanField(default=False)
  priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='3')
  original = models.BooleanField(default=True)
  collaborative = models.BooleanField(default=False)
  active = models.BooleanField(default=True)
  
  # TEST data
  interRepetitionInterval = models.IntegerField(default=1) #in days
  eFactor = models.FloatField(default=2.5) #Easiness Factor - see http://www.supermemo.com/english/ol/sm2.htm
  nextTest = models.DateField()
  iteration = models.IntegerField(default=0)
  def save(self, *args, **kwargs):
    if self.back != '':
      super(Card, self).save(*args, **kwargs)
  def __unicode__(self):
    return self.front
  def __as_dict__(self):
    dict = {
      'front': self.front,
      'back': self.back,
      'pk': self.pk,
      'private': self.private,
      'donottest': self.donottest,
      'priority': self.priority,
      'original': self.original,
      'active': self.active,
    }
    if self.settings != None:    
      dict['settings'] = self.settings.pk
    else:
      dict['settings'] = None
    return dict
def card_pre_delete(sender, **kwargs):
  self = kwargs['instance']
  # REMOVE objects with Foreign Key dependency on Card
  CardTagView.objects.filter(card=self).delete()
  CardSourceView.objects.filter(card=self).delete()
pre_delete.connect(card_pre_delete, sender=Card)
def card_post_save(sender, **kwargs):
  self = kwargs['instance']
  settings = self.settings
  if settings != None:
    if settings.denormalized_nextTest == None or settings.denormalized_nextTest > self.nextTest:
      settings.denormalized_nextTest = self.nextTest
      settings.save()
    denormalizeQueryset(CardTagView.objects.filter(card=self))
    denormalizeQueryset(CardSourceView.objects.filter(card=self))
post_save.connect(card_post_save, sender=Card)

def denormalizeQueryset(qset):
  for q in qset:
    q.save()

SEARCHABLE_TYPES = (
  ('t', 'Tag'),
  ('s', 'Source'),
)

class Searchable(models.Model):
  name = models.CharField(max_length=100, unique=True)
  type = models.CharField(max_length=1, choices=SEARCHABLE_TYPES)
  def save(self, *args, **kwargs):
    self.name = self.name.strip()
    super(Searchable, self).save(*args, **kwargs)
  def __unicode__(self):
    return self.name
def searchable_pre_delete(sender, **kwargs):
  self = kwargs['instance']
  # REMOVE objects with Foreign Key dependency on Card
  CardTagView.objects.filter(searchable=self).delete()
  CardSourceView.objects.filter(searchable=self).delete()
pre_delete.connect(searchable_pre_delete, sender=Searchable)
def searchable_post_save(sender, **kwargs):
  self = kwargs['instance']
  # UPDATE CardSearchableView
  denormalizeQueryset(CardTagView.objects.filter(searchable=self))
  denormalizeQueryset(CardSourceView.objects.filter(searchable=self))
post_save.connect(searchable_post_save, sender=Searchable)

class SuggestedTags(models.Model):
  settings = models.ForeignKey(Settings, unique=True)
  highestOccuringTag = models.ForeignKey(Searchable)
  highestOccuringAmount = models.IntegerField(default=1)
  
class CardSearchableView(models.Model):
  card = models.ForeignKey('Card')
  searchable = models.ForeignKey('Searchable')
  denormalized_searchable_name = models.CharField(max_length=50, blank=True, null=True)
  denormalized_card_settings = models.ForeignKey(Settings, blank=True, null=True)
  denormalized_card_original = models.BooleanField(default=True)
  denormalized_card_private = models.BooleanField(default=True)
  denormalized_card_active = models.BooleanField(default=True)
  class Meta:
    abstract = True
    unique_together = (("card", "searchable"),)
  def save(self, *args, **kwargs):
    self.denormalized_card_settings = self.card.settings
    self.denormalized_card_original = self.card.original
    self.denormalized_card_private = self.card.private
    self.denormalized_searchable_name = self.searchable.name
    super(CardSearchableView, self).save(*args, **kwargs)
    
class CardTagView(CardSearchableView):
  pass
def cardTagView_post_save(sender, **kwargs):
  self = kwargs['instance']
  #test against Highest Occuring Tag
  #TODO known bug - this doesnt account for the situation where the user removes cards - and therefore the highestOccuringAmount should decrease
  if self.denormalized_card_settings != None:
    try:
      sTag = SuggestedTags.objects.filter(settings=self.denormalized_card_settings)[0]
      tagCount = CardTagView.objects.filter(denormalized_card_settings=self.denormalized_card_settings, searchable=self.searchable).count()
      logging.info(str(sTag.highestOccuringAmount) + ": "+sTag.highestOccuringTag.name)
      logging.info(str(tagCount) + ": "+self.searchable.name)
      if tagCount > sTag.highestOccuringAmount:
        sTag.highestOccuringAmount = tagCount
        sTag.highestOccuringTag = self.searchable
        sTag.save()
    except:
      SuggestedTags.objects.create(settings=self.denormalized_card_settings, highestOccuringTag=self.searchable)
post_save.connect(cardTagView_post_save, sender=CardTagView)

    
SOURCE_LOCATIONS = (
  ('b', 'book'),
  ('w', 'webpage'),
  ('m', 'magazine'),
  ('n', 'newspaper'),
  ('p', 'person'),
)

class CardSourceView(CardSearchableView):
  text = models.TextField(blank=True, null=True)
def cardSourceView_post_save(sender, **kwargs):
  self = kwargs['instance']
  if self.text == None:
    taskqueue.add(url="/addHtmlForSource", params={'pk': str(self.pk), })
    logging.info('CARD SOURCE POST SAVE')
    logging.info('/addHtmlForSource pk=' + str(self.pk))
post_save.connect(cardSourceView_post_save, sender=CardSourceView)

class SearchLog(models.Model):
  settings = models.ForeignKey(Settings)
  date = models.DateTimeField(auto_now_add=True)
  searchable = models.ForeignKey(Searchable)
  
class ShareSet(models.Model):
  cards = ListField(models.ForeignKey(Card))
  editable = models.BooleanField(default=False)
  settings = models.ForeignKey(Settings)
  

#TODO there should be a model for words from the back of each card. This would
# be generated in the background over time. Maybe I can just make it searchable like in gobaloo
