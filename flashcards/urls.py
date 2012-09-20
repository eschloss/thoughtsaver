from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('flashcards.views',
  (r'^addCard$', 'addCard'), #ajax call per card                       
  (r'^addCards$', 'addCards'),
  (r'^addTags$', 'addTags'),
  (r'^removeTags$', 'removeTags'),
  (r'^myCards$', 'myCards'),
  (r'^createShareSet$', 'createShareSet'),
  (r'^viewSet/([0123456789]*)$', 'viewShareSet'),
  (r'^changeCard$', 'changeCard'),
  (r'^addHtmlForSource', 'addHtmlForSource'),
  (r'^myCardsAjax$', 'myCardsAjax'),
  (r'^asyncSearch$', 'asyncSearch'),
  (r'^myTags$', 'myTags'),
  (r'^sendSessionCards$', 'sendSessionCards'),
  (r'copyCard/([-0123456789]*)$', 'copyCard'),
  (r'^removeCard/([-0123456789]*)$', 'removeCard'),
  (r'^addCardBookmarklet$', 'addCardBookmarklet'),
  (r'^help$', 'help'), 
)
urlpatterns += patterns('flashcards.testViews',
  (r'^dailyTest$', 'dailyTest'), 
  (r'^test$', 'test'), 
  (r'^completeTest$', 'completeTest'), 
  (r'^completeReview$', 'completeReview'), 
)