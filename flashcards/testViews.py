from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template  import RequestContext
from django.contrib.auth.decorators import login_required
import math, datetime, re
from flashcards.models import *
from flashcards.views import generateFullCardListFromQueryset
from django.core.urlresolvers import reverse

ITERATION_TO_NEXT_INTERVAL = [1, 6]

# responseQuality should be between 0 and 5
def calculateNewEasinessFactor(eFactor, responseQuality):
  eFactor = eFactor + (0.1-(5-responseQuality)*(0.08+(5-responseQuality)*0.02))
  return (eFactor if eFactor >= 1.3 else 1.3)

QUALITY_CUTOFF = 3

def updateCard(card, responseQuality):
  if responseQuality >= QUALITY_CUTOFF and card.nextTest <= datetime.date.today():
      card.iteration += 1
      eFactor = calculateNewEasinessFactor(card.eFactor, responseQuality)
      if card.iteration < 2:
        card.interRepetitionInterval = ITERATION_TO_NEXT_INTERVAL[card.iteration]
      else:
        card.interRepetitionInterval = math.ceil(card.interRepetitionInterval * eFactor) #Why does the SM-2 algorithm round up!!...?
      card.eFactor = eFactor
  elif responseQuality < QUALITY_CUTOFF:
    card.iteration = 0
    card.interRepetitionInterval = ITERATION_TO_NEXT_INTERVAL[card.iteration]
  card.nextTest = datetime.date.today() + datetime.timedelta(days=card.interRepetitionInterval)
  card.save()
  
@login_required
def dailyTest(request):
  settings = request.user.get_profile()
  cards = getDailyCards(settings)
  return render_to_response('test/test.html', {
      'cards': cards,
    }, context_instance=RequestContext(request)
  )

@login_required
def test(request):
  if request.method == 'POST':
    items = request.POST.items()
    pks = filter(lambda (x, y): x.isdigit() and y == 'on', items)
    pks = map(lambda x: x[0], pks)
    cards = Card.objects.filter(pk__in=pks)
    cards = generateFullCardListFromQueryset(cards)
    return render_to_response('test/test.html', {
        'cards': cards,
      }, context_instance=RequestContext(request)
    )
  return HttpResponseRedirect('/myCards')

def validTestData(card, value, settings):
  return True
  if card.settings != settings: return False
  if value < 0 or value > 5: return False
  return True 

def parseTestData(post, settings):
  testCardDict = {}
  for key in post:
    pk = re.sub(r'q_', '', key)
    card = Card.objects.filter(pk=int(pk)).only('front', 'back')[0]
    if not validTestData(card, post[key], settings): continue
    testCardDict[card] = pk=int(post[key])
  return testCardDict    

def reviewIncorrectCards(cards, request):
  return render_to_response('test/review.html', {
      'cards': generateFullCardListFromQueryset(cards),
    }, context_instance=RequestContext(request)
  )
  
def denormalizeSettings(settings):
  cards = Card.objects.filter(settings=settings).order_by('nextTest')
  settings.nextTest = cards[0].nextTest
  settings.save()

@login_required
def completeReview(request):
  return completeTest(request) # right now they are the same. this will change

def completeTest(request):
  if request.method == 'POST':
    testPOST = request.POST
    if not request.user.is_authenticated():
      request.session['testPOST'] = testPOST
      return HttpResponseRedirect('/accounts/login/?next=%s' % ('/completeTest'))  
  else:
    if not request.session.__contains__('testPOST') or not request.user.is_authenticated():
      raise Http404
    testPOST = request.session['testPOST']
    
  testCardDict = parseTestData(testPOST, request.user.get_profile())
  reviewCards = []
  for x in testCardDict:
    if testCardDict[x] < 3:
      reviewCards.append(x)
    updateCard(x, testCardDict[x])
  denormalizeSettings(request.user.get_profile()) # TODO denormalizeSettings should be a part of the Settings object
  if len(reviewCards) == 0:
    return HttpResponse('Test Complete')
  return reviewIncorrectCards(reviewCards, request)
  
def getDailyCards(settings):
  maxCards = settings.dailyTestMaxItems
  cards = Card.objects.filter(settings=settings, donottest=False, nextTest__lte=datetime.date.today()).order_by('nextTest').only('front', 'back')[:maxCards]
  return generateFullCardListFromQueryset(cards)
